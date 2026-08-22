import threading
import numpy as np
import sounddevice as sd
from key_detector import AutoKeyDetector


class AdaptiveNoiseSuppressor:
    """Khử ồn thích ứng kiểu AI-lite bằng ước lượng phổ và mặt nạ mềm.

    Bộ lọc học phổ nền khi được yêu cầu, tự cập nhật chậm trong các block yên
    lặng và giảm các dải có SNR thấp trước khi đưa sang autotune.
    """
    def __init__(self, sample_rate=48000, block_size=256):
        self.sample_rate, self.block_size = sample_rate, block_size
        self.enabled, self.strength, self.learning = False, 0.65, False
        self.noise_power = np.ones(block_size // 2 + 1, dtype=np.float32) * 1e-5
        self._noise_ready = False

    def reset(self):
        self.noise_power.fill(1e-5); self._noise_ready = False

    def learn(self, x):
        spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
        if len(spec) != len(self.noise_power):
            self.noise_power = np.ones(len(spec), dtype=np.float32) * 1e-5
        self.noise_power = 0.8 * self.noise_power + 0.2 * spec.astype(np.float32)
        self._noise_ready = True

    def process(self, x):
        if not self.enabled or not self._noise_ready:
            if self.learning: self.learn(x)
            return x
        window = np.hanning(len(x)).astype(np.float32)
        spectrum = np.fft.rfft(x * window)
        power = np.abs(spectrum) ** 2
        noise = np.maximum(self.noise_power, 1e-8)
        snr = power / noise
        # Wiener-like soft mask; strength 0..1, voice transients stay intact.
        mask = np.clip((snr - 1.0) / (snr + 1.0), 0.05, 1.0)
        mask = (1.0 - self.strength) + self.strength * mask
        cleaned = np.fft.irfft(spectrum * mask, n=len(x)).astype(np.float32)
        if self.learning and float(np.sqrt(np.mean(x*x))) < 0.025: self.learn(x)
        return cleaned


class RealtimeAutoTune:
    A4 = 440.0
    SCALES = {"Chromatic": list(range(12)), "Trưởng": [0,2,4,5,7,9,11], "Thứ": [0,2,3,5,7,8,10], "Ngũ cung": [0,2,4,7,9]}

    def __init__(self, sample_rate=48000, block_size=256):
        self.sample_rate, self.block_size = sample_rate, block_size
        self.key, self.scale_name = 0, "Chromatic"; self.retune_ms, self.mix, self.bypass = 35.0, 1.0, False
        self.autotune_enabled, self.harmony_enabled = True, False
        self.auto_key = AutoKeyDetector(sample_rate, 4096); self.key_stream = None; self.auto_key_enabled = False
        self.harmony_mode, self.harmony_level = "Tắt", 0.0
        self.noise_suppressor = AdaptiveNoiseSuppressor(sample_rate, block_size)
        self.reverb_enabled, self.delay_enabled = False, False
        self.reverb_mix, self.reverb_size, self.delay_mix, self.delay_ms, self.delay_feedback = 0.0, 0.55, 0.0, 280.0, 0.25
        self._last_ratio, self._lock, self.stream = 1.0, threading.Lock(), None
        self.level, self.detected_hz = 0.0, 0.0; self._delay_buffer = np.zeros(48000*2, dtype=np.float32); self._delay_pos = 0
        self._rev_buffers = [np.zeros(int(self.sample_rate*d), dtype=np.float32) for d in (0.0297,0.0371,0.0411,0.0437)]
        self._rev_pos = [0,0,0,0]

    def set_params(self, key, scale_name, retune_ms, mix, bypass, harmony_mode="Tắt", harmony_level=0.0, reverb_mix=0.0, reverb_size=0.55, delay_mix=0.0, delay_ms=280.0, delay_feedback=0.25, noise_enabled=False, noise_strength=0.65, noise_learning=False, autotune_enabled=True, harmony_enabled=False, reverb_enabled=False, delay_enabled=False):
        with self._lock:
            self.key, self.scale_name = int(key)%12, scale_name; self.retune_ms, self.mix, self.bypass = float(retune_ms), float(mix), bool(bypass)
            self.harmony_mode, self.harmony_level = harmony_mode, float(harmony_level); self.reverb_mix, self.reverb_size = float(reverb_mix), float(reverb_size)
            self.delay_mix, self.delay_ms, self.delay_feedback = float(delay_mix), float(delay_ms), float(delay_feedback)
            self.noise_suppressor.enabled = bool(noise_enabled); self.noise_suppressor.strength = float(noise_strength); self.noise_suppressor.learning = bool(noise_learning)
            self.autotune_enabled, self.harmony_enabled = bool(autotune_enabled), bool(harmony_enabled)
            self.reverb_enabled, self.delay_enabled = bool(reverb_enabled), bool(delay_enabled)

    def _detect_pitch(self, x):
        x=x.astype(np.float32,copy=False); x-=np.mean(x); rms=float(np.sqrt(np.mean(x*x)+1e-12)); self.level=min(1.0,rms*4)
        if rms<0.008:return 0.0
        n=len(x); w=x*np.hanning(n).astype(np.float32); corr=np.correlate(w,w,mode="full")[n-1:]; lo,hi=max(2,int(self.sample_rate/1000)),min(n-2,int(self.sample_rate/70))
        if hi<=lo:return 0.0
        lag=int(np.argmax(corr[lo:hi]))+lo; return float(self.sample_rate/lag) if corr[lag]>=corr[0]*.15 else 0.0

    def _nearest_scale_hz(self,hz):
        midi=69+12*np.log2(max(hz,1e-6)/self.A4); base=int(np.floor(midi/12))*12+self.key; cs=[base+o*12+i for o in range(-2,3) for i in self.SCALES.get(self.scale_name,range(12))]; target=min(cs,key=lambda m:abs(m-midi)); return self.A4*2**((target-69)/12)
    def _shift(self,x,semitones):
        r=float(np.clip(2**(semitones/12),.5,2)); src=np.linspace(0,len(x)-1,len(x),dtype=np.float32); mapped=np.clip((src-(len(x)-1)/2)*r+(len(x)-1)/2,0,len(x)-1); return np.interp(src,mapped,x).astype(np.float32)

    def _voice(self, mono):
        with self._lock: bypass,mix,retune,hm,hl,at_on,ha_on=self.bypass,self.mix,self.retune_ms,self.harmony_mode,self.harmony_level,self.autotune_enabled,self.harmony_enabled
        hz=self._detect_pitch(mono); self.detected_hz=hz
        if hz <= 0: return mono
        if at_on and not bypass:
            desired=self._nearest_scale_hz(hz)/hz; a=min(1,self.block_size/max(1,self.sample_rate*retune/1000)); self._last_ratio+=(desired-self._last_ratio)*a
            src=np.linspace(0,len(mono)-1,len(mono),dtype=np.float32); r=float(np.clip(self._last_ratio,.5,2)); mapped=np.clip((src-(len(mono)-1)/2)*r+(len(mono)-1)/2,0,len(mono)-1); tuned=np.interp(src,mapped,mono).astype(np.float32); out=mono*(1-mix)+tuned*mix
        else:
            tuned, out = mono, mono.copy()
        semi={"Bè 3":4,"Bè 5":7,"Bè quãng tám trên":12,"Bè quãng tám dưới":-12}.get(hm,0)
        return np.clip(out+(self._shift(tuned,semi)*hl if ha_on and semi and hl>0 else 0),-1,1)

    def _effects(self,x):
        with self._lock: rm,rs,dm,dms,df,reverb_on,delay_on=self.reverb_mix,self.reverb_size,self.delay_mix,self.delay_ms,self.delay_feedback,self.reverb_enabled,self.delay_enabled
        if delay_on and dm>0:
            d=min(len(self._delay_buffer)-1,max(1,int(self.sample_rate*dms/1000))); y=np.empty_like(x)
            for i,v in enumerate(x):
                p=(self._delay_pos+i)%len(self._delay_buffer); read=(p-d)%len(self._delay_buffer); y[i]=self._delay_buffer[read]; self._delay_buffer[p]=v+y[i]*np.clip(df,0,.85)
            self._delay_pos=(self._delay_pos+len(x))%len(self._delay_buffer); x=x*(1-dm)+y*dm
        if reverb_on and rm>0:
            wet=np.zeros_like(x)
            for j,b in enumerate(self._rev_buffers):
                g=.72-.08*j
                for i,v in enumerate(x):
                    p=self._rev_pos[j]; old=b[p]; b[p]=v+old*g; wet[i]+=old; self._rev_pos[j]=(p+1)%len(b)
            wet/=len(self._rev_buffers); x=x*(1-rm)+wet*(rm*(.65+.35*rs))
        return np.clip(x,-1,1)

    def _callback(self,indata,outdata,frames,time_info,status):
        clean = self.noise_suppressor.process(indata[:,0].copy())
        p=self._effects(self._voice(clean)); outdata[:]=0
        for ch in range(outdata.shape[1]):outdata[:,ch]=p
    def _key_callback(self, indata, frames, time_info, status):
        x = indata[:, 0] if indata.ndim > 1 else indata
        k, scale, confidence = self.auto_key.analyze(x)
        if self.auto_key_enabled and confidence >= 0.18:
            with self._lock:
                self.key, self.scale_name = k, scale

    def start_auto_key(self, source_device, sample_rate=None, channels=2):
        self.stop_auto_key()
        rate = int(sample_rate or self.sample_rate); self.auto_key.reset(); self.auto_key_enabled = True
        self.key_stream = sd.InputStream(samplerate=rate, blocksize=2048, device=source_device, channels=channels, dtype="float32", latency="low", callback=self._key_callback)
        self.key_stream.start()

    def stop_auto_key(self):
        self.auto_key_enabled = False
        if self.key_stream is not None: self.key_stream.stop(); self.key_stream.close(); self.key_stream = None

    def auto_key_status(self):
        return self.auto_key.label()

    def hostapis(self):
        return sd.query_hostapis()

    def devices(self, asio_only=False):
        ds = sd.query_devices(); hosts = sd.query_hostapis()
        if not asio_only: return ds
        return [d for d in ds if "ASIO" in hosts[d["hostapi"]]["name"].upper() and d["max_input_channels"] > 0 and d["max_output_channels"] > 0]

    def asio_available(self):
        return any("ASIO" in h["name"].upper() for h in sd.query_hostapis())

    def start(self,input_device=None,output_device=None,sample_rate=None,buffer_size=None,prefer_asio=True):
        if self.stream is not None:return
        if sample_rate:self.sample_rate=int(sample_rate)
        if buffer_size is not None:self.block_size=int(buffer_size)
        if prefer_asio and input_device is not None:
            try:
                hosts=sd.query_hostapis(); d=sd.query_devices(input_device)
                if "ASIO" not in hosts[d["hostapi"]]["name"].upper(): raise RuntimeError("Thiết bị đã chọn không thuộc ASIO")
            except Exception:
                prefer_asio=False
        self.stream=sd.Stream(samplerate=self.sample_rate,blocksize=self.block_size,device=(input_device,output_device),channels=(1,2),dtype="float32",latency="low",callback=self._callback); self.stream.start()
    def save_wav(self,path,seconds=10):
        import wave; recording=sd.rec(int(seconds*self.sample_rate),samplerate=self.sample_rate,channels=1,dtype="float32"); sd.wait(); pcm=np.clip(recording[:,0]*32767,-32768,32767).astype(np.int16)
        with wave.open(path,"wb") as wf:wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(self.sample_rate);wf.writeframes(pcm.tobytes())
    def stop(self):
        if self.stream is not None:self.stream.stop();self.stream.close();self.stream=None
    def close(self):
        self.stop_auto_key(); self.stop()
    def __del__(self):
        try:self.close()
        except Exception:pass


def note_names():return ["Đô (C)","Đô# (C#)","Rê (D)","Rê# (D#)","Mi (E)","Fa (F)","Fa# (F#)","Sol (G)","Sol# (G#)","La (A)","La# (A#)","Si (B)"]
def hz_to_note(hz):
    if hz<=0:return "--"
    midi=round(69+12*np.log2(hz/440));return f"{note_names()[midi%12]} {midi//12-1}"
