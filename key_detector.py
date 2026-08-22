import numpy as np

NOTE_NAMES = ["Đô (C)", "Đô# (C#)", "Rê (D)", "Rê# (D#)", "Mi (E)", "Fa (F)", "Fa# (F#)", "Sol (G)", "Sol# (G#)", "La (A)", "La# (A#)", "Si (B)"]
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88], dtype=np.float32)
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17], dtype=np.float32)


class AutoKeyDetector:
    def __init__(self, sample_rate=48000, fft_size=4096, history=12):
        self.sample_rate, self.fft_size, self.history = sample_rate, fft_size, history
        self.chroma_history = []; self.key_index = 0; self.scale = "Trưởng"; self.confidence = 0.0; self.active = False

    def reset(self):
        self.chroma_history.clear(); self.key_index=0; self.scale="Trưởng"; self.confidence=0.0

    def analyze(self, audio):
        x=np.asarray(audio,dtype=np.float32).reshape(-1); x=x-np.mean(x)
        if len(x)<512 or float(np.sqrt(np.mean(x*x)))<0.005: return self.key_index,self.scale,self.confidence
        if len(x)>self.fft_size:x=x[-self.fft_size:]
        win=np.hanning(len(x)); mag=np.abs(np.fft.rfft(x*win)); freqs=np.fft.rfftfreq(len(x),1/self.sample_rate)
        chroma=np.zeros(12,dtype=np.float32); valid=(freqs>=55)&(freqs<=2000)
        midi=np.round(69+12*np.log2(np.maximum(freqs[valid],1e-6)/440)).astype(int)%12
        for i,n in enumerate(midi): chroma[n]+=mag[valid][i]
        total=float(chroma.sum())
        if total<=1e-6:return self.key_index,self.scale,self.confidence
        chroma/=total; self.chroma_history.append(chroma)
        if len(self.chroma_history)>self.history:self.chroma_history.pop(0)
        avg=np.mean(self.chroma_history,axis=0); scores=[]
        for scale,profile in (("Trưởng",MAJOR),("Thứ",MINOR)):
            p=(profile-profile.mean())/(profile.std()+1e-6)
            for k in range(12):scores.append((float(np.dot(avg,np.roll(p,k))),k,scale))
        scores.sort(reverse=True); best=scores[0]; second=scores[1][0] if len(scores)>1 else 0
        self.confidence=float(np.clip((best[0]-second+0.05)*2.5,0,1))
        if self.confidence>=0.18:self.key_index,self.scale=best[1],best[2]
        return self.key_index,self.scale,self.confidence

    def label(self):return f"{NOTE_NAMES[self.key_index]} {self.scale} ({self.confidence*100:.0f}%)"
