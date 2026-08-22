import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from audio_engine import RealtimeAutoTune, note_names, hz_to_note

class QuiLeAutovocal(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("QuiLe-Autovocal"); self.geometry("900x820"); self.configure(bg="#111827"); self.e=RealtimeAutoTune(); self.running=False; self.recording=False; self.presets={"Nam trầm":dict(retune=55,mix=78,noise=.55,harmony="Bè 3",hlevel=.18,reverb=.14,room=.42,delay=.08,delay_ms=240,feedback=.18),"Nữ cao":dict(retune=22,mix=92,noise=.45,harmony="Bè 3",hlevel=.12,reverb=.18,room=.58,delay=.10,delay_ms=180,feedback=.16),"Radio voice":dict(retune=35,mix=100,noise=.72,harmony="Tắt",hlevel=0,reverb=.08,room=.25,delay=0,delay_ms=220,feedback=0)}; self._ui(); self._bind_shortcuts(); self._tick(); self.protocol("WM_DELETE_WINDOW",self._close)
    def _ui(self):
        s=ttk.Style(self); s.theme_use("clam"); s.configure("TFrame",background="#111827"); s.configure("TLabel",background="#111827",foreground="#e5e7eb",font=("Segoe UI",10)); s.configure("Title.TLabel",font=("Segoe UI",24,"bold"),foreground="#7dd3fc"); s.configure("TLabelframe",background="#111827",foreground="#cbd5e1"); s.configure("TLabelframe.Label",background="#111827",foreground="#7dd3fc"); s.configure("TButton",padding=8)
        r=ttk.Frame(self,padding=20); r.pack(fill="both",expand=True); ttk.Label(r,text="QuiLe-Autovocal",style="Title.TLabel").pack(anchor="w"); ttk.Label(r,text="Bộ chỉnh giọng, chồng bè và hiệu ứng realtime cho thu âm • livestream • karaoke").pack(anchor="w",pady=(0,12))
        io=ttk.LabelFrame(r,text="Audio interface",padding=10); io.pack(fill="x",pady=4); ttk.Label(io,text="Chọn cùng một sound card/audio interface cho đường vào và đường ra").grid(row=0,column=0,columnspan=3,sticky="w"); self.dev=tk.StringVar(); self.box=ttk.Combobox(io,textvariable=self.dev,state="readonly",width=65); self.box.grid(row=1,column=0,pady=7); ttk.Button(io,text="Tự nhận thiết bị",command=self._load).grid(row=1,column=1,padx=8); self.rate=tk.StringVar(value="48000 Hz"); ttk.Combobox(io,textvariable=self.rate,values=["44100 Hz","48000 Hz","96000 Hz"],state="readonly",width=12).grid(row=1,column=2); self.buffer=tk.StringVar(value="32 samples"); ttk.Combobox(io,textvariable=self.buffer,values=["32 samples","48 samples","64 samples","128 samples","256 samples"],state="readonly",width=14).grid(row=1,column=3,padx=8); self._load()
        ak=ttk.LabelFrame(r,text="Auto Key — tự nhận diện tông nhạc nền",padding=10); ak.pack(fill="x",pady=4); self.ak_on=tk.BooleanVar(value=False); self.ak_source=tk.StringVar(); self.ak_status=tk.StringVar(value="Chưa phân tích")
        ttk.Checkbutton(ak,text="Bật Auto Key",variable=self.ak_on,command=self._toggle_auto_key).pack(side="left"); ttk.Label(ak,text="Nguồn phân tích").pack(side="left",padx=(16,5)); self.ak_box=ttk.Combobox(ak,textvariable=self.ak_source,state="readonly",width=55); self.ak_box.pack(side="left",padx=6); ttk.Button(ak,text="Phân tích / dừng",command=self._toggle_auto_key).pack(side="left",padx=6); ttk.Label(ak,textvariable=self.ak_status,foreground="#7dd3fc").pack(side="left",padx=8)
        tune=ttk.LabelFrame(r,text="Tự dò tune",padding=10); tune.pack(fill="x",pady=4); self.key=tk.StringVar(value=note_names()[0]); self.scale=tk.StringVar(value="Chromatic"); self.retune=tk.DoubleVar(value=35); self.mix=tk.DoubleVar(value=100); self.at_on=tk.BooleanVar(value=True); self.bypass=tk.BooleanVar();
        for j,t in enumerate(["Tông giọng","Thang âm","Tốc độ bắt nốt (ms)","Mức chỉnh (%)"]):ttk.Label(tune,text=t).grid(row=0,column=[0,1,2,4][j],sticky="w",padx=(0,14) if j==0 else 14)
        ttk.Combobox(tune,textvariable=self.key,values=note_names(),state="readonly",width=16).grid(row=1,column=0); ttk.Combobox(tune,textvariable=self.scale,values=["Chromatic","Trưởng","Thứ","Ngũ cung"],state="readonly",width=13).grid(row=1,column=1,padx=14); ttk.Scale(tune,from_=5,to=150,variable=self.retune,orient="horizontal",length=140).grid(row=1,column=2,padx=14); ttk.Label(tune,textvariable=self.retune,width=5).grid(row=1,column=3); ttk.Scale(tune,from_=0,to=100,variable=self.mix,orient="horizontal",length=130).grid(row=1,column=4,padx=14); ttk.Label(tune,textvariable=self.mix,width=5).grid(row=1,column=5); ttk.Checkbutton(tune,text="Bật autotune",variable=self.at_on).grid(row=1,column=6,padx=8); ttk.Checkbutton(tune,text="Bypass",variable=self.bypass).grid(row=1,column=7,padx=8)
        pre=ttk.LabelFrame(r,text="Preset giọng hát",padding=10); pre.pack(fill="x",pady=4); self.preset=tk.StringVar(value="Tùy chỉnh"); ttk.Label(pre,text="Chọn cấu hình có sẵn").pack(side="left"); ttk.Combobox(pre,textvariable=self.preset,values=["Tùy chỉnh","Nam trầm","Nữ cao","Radio voice"],state="readonly",width=18).pack(side="left",padx=10); ttk.Button(pre,text="Áp dụng preset",command=self._apply_preset).pack(side="left"); ttk.Label(pre,text="Preset chỉ thay đổi thông số giọng và hiệu ứng, không thay đổi thiết bị audio").pack(side="left",padx=14)
        harm=ttk.LabelFrame(r,text="Chồng bè tự động",padding=10); harm.pack(fill="x",pady=4); self.hm=tk.StringVar(value="Tắt"); self.hl=tk.DoubleVar(value=0); self.ha_on=tk.BooleanVar(value=False); ttk.Checkbutton(harm,text="Bật chồng bè",variable=self.ha_on).pack(side="left"); ttk.Label(harm,text="Kiểu bè").pack(side="left",padx=8); ttk.Combobox(harm,textvariable=self.hm,values=["Tắt","Bè 3","Bè 5","Bè quãng tám trên","Bè quãng tám dưới"],state="readonly",width=22).pack(side="left",padx=8); ttk.Label(harm,text="Âm lượng").pack(side="left",padx=(18,5)); ttk.Scale(harm,from_=0,to=.7,variable=self.hl,orient="horizontal",length=180).pack(side="left")
        fx=ttk.LabelFrame(r,text="Hiệu ứng giọng chuyên nghiệp",padding=10); fx.pack(fill="x",pady=4); self.re_on=tk.BooleanVar(value=False); self.de_on=tk.BooleanVar(value=False); self.rm=tk.DoubleVar(value=0); self.rs=tk.DoubleVar(value=.55); self.dm=tk.DoubleVar(value=0); self.dms=tk.DoubleVar(value=280); self.df=tk.DoubleVar(value=.25)
        ttk.Checkbutton(fx,text="Bật Reverb",variable=self.re_on).grid(row=0,column=0,sticky="w"); ttk.Label(fx,text="Reverb mix").grid(row=0,column=1,sticky="w"); ttk.Scale(fx,from_=0,to=1,variable=self.rm,orient="horizontal",length=145).grid(row=0,column=2,padx=8); ttk.Label(fx,text="Room size").grid(row=0,column=3); ttk.Scale(fx,from_=0,to=1,variable=self.rs,orient="horizontal",length=145).grid(row=0,column=4,padx=8); ttk.Checkbutton(fx,text="Bật Delay",variable=self.de_on).grid(row=0,column=5); ttk.Label(fx,text="Delay mix").grid(row=0,column=6); ttk.Scale(fx,from_=0,to=1,variable=self.dm,orient="horizontal",length=145).grid(row=0,column=7,padx=8); ttk.Label(fx,text="Thời gian (ms)").grid(row=1,column=0,sticky="w"); ttk.Scale(fx,from_=40,to=900,variable=self.dms,orient="horizontal",length=145).grid(row=1,column=1,padx=8); ttk.Label(fx,text="Feedback").grid(row=1,column=2); ttk.Scale(fx,from_=0,to=.8,variable=self.df,orient="horizontal",length=145).grid(row=1,column=3,padx=8); ttk.Label(fx,text="Delay đồng bộ theo tempo có thể bổ sung ở bản sau").grid(row=1,column=4,columnspan=2,padx=8)
        ns=ttk.LabelFrame(r,text="Khử ồn AI thích ứng",padding=10); ns.pack(fill="x",pady=4); self.ne=tk.BooleanVar(value=False); self.nstrength=tk.DoubleVar(value=.65); self.nlearning=tk.BooleanVar(value=False)
        ttk.Checkbutton(ns,text="Bật khử ồn",variable=self.ne).pack(side="left"); ttk.Label(ns,text="Cường độ").pack(side="left",padx=(18,5)); ttk.Scale(ns,from_=0,to=1,variable=self.nstrength,orient="horizontal",length=180).pack(side="left"); ttk.Checkbutton(ns,text="Học tiếng ồn nền",variable=self.nlearning).pack(side="left",padx=15); ttk.Button(ns,text="Đặt lại hồ sơ noise",command=self._reset_noise).pack(side="left"); ttk.Label(ns,text="Bật học ồn khi im lặng 2–5 giây, sau đó tắt học để giữ giọng tự nhiên").pack(side="left",padx=12)
        mon=ttk.LabelFrame(r,text="Giám sát tín hiệu",padding=12); mon.pack(fill="both",expand=True,pady=4); self.note=ttk.Label(mon,text="--",font=("Segoe UI",38,"bold"),foreground="#34d399"); self.note.pack(pady=3); self.pitch=ttk.Label(mon,text="Cao độ: -- Hz | Mức tín hiệu: 0%"); self.pitch.pack(); self.meter=ttk.Progressbar(mon,orient="horizontal",length=650,mode="determinate"); self.meter.pack(pady=14)
        keys=ttk.LabelFrame(r,text="Phím tắt nhanh",padding=8); keys.pack(fill="x",pady=(4,0)); ttk.Label(keys,text="F1 Monitor  |  F2 Autotune  |  F3 Khử ồn  |  F4 Chồng bè  |  F5 Reverb  |  F6 Delay  |  F7 Học noise  |  Ctrl+R Ghi âm").pack(anchor="w"); ttk.Label(keys,text="Ctrl+F2/F3/F4/F5/F6 giảm tham số  •  Shift+F2/F3/F4/F5/F6 tăng tham số").pack(anchor="w"); ttk.Button(keys,text="Quản lý / gán phím tắt",command=self._open_shortcuts).pack(anchor="e")
        b=ttk.Frame(r); b.pack(fill="x",pady=(8,0)); self.btn=ttk.Button(b,text="Bắt đầu monitor",command=self._toggle); self.btn.pack(side="left"); ttk.Button(b,text="Ghi âm 10 giây",command=self._record).pack(side="left",padx=8); self.status=ttk.Label(b,text="Sẵn sàng"); self.status.pack(side="right")
        for v in (self.key,self.scale,self.retune,self.mix,self.at_on,self.bypass,self.hm,self.hl,self.ha_on,self.rm,self.rs,self.re_on,self.dm,self.dms,self.df,self.de_on,self.ne,self.nstrength,self.nlearning):v.trace_add("write",lambda *_:self._apply())
    def _bind_shortcuts(self):
        self.shortcuts = {"Monitor":"F1", "Autotune bật/tắt":"F2", "Khử ồn bật/tắt":"F3", "Chồng bè bật/tắt":"F4", "Reverb bật/tắt":"F5", "Delay bật/tắt":"F6", "Học noise bật/tắt":"F7", "Ghi âm":"Control_R", "Autotune mix giảm":"Control_F2", "Autotune mix tăng":"Shift_F2", "Khử ồn giảm":"Control_F3", "Khử ồn tăng":"Shift_F3", "Bè giảm":"Control_F4", "Bè tăng":"Shift_F4", "Reverb giảm":"Control_F5", "Reverb tăng":"Shift_F5", "Delay giảm":"Control_F6", "Delay tăng":"Shift_F6"}
        self._rebind_all()

    def _rebind_all(self):
        for seq in ("<F1>","<F2>","<F3>","<F4>","<F5>","<F6>","<F7>","<Control-r>","<Control-F2>","<Shift-F2>","<Control-F3>","<Shift-F3>","<Control-F4>","<Shift-F4>","<Control-F5>","<Shift-F5>","<Control-F6>","<Shift-F6>"): self.unbind_all(seq)
        actions = {"Monitor":lambda e:self._toggle(), "Autotune bật/tắt":lambda e:self._flip(self.at_on), "Khử ồn bật/tắt":lambda e:self._flip(self.ne), "Chồng bè bật/tắt":lambda e:self._flip(self.ha_on), "Reverb bật/tắt":lambda e:self._flip(self.re_on), "Delay bật/tắt":lambda e:self._flip(self.de_on), "Học noise bật/tắt":lambda e:self._flip(self.nlearning), "Ghi âm":lambda e:self._record(), "Autotune mix giảm":lambda e:self._step(self.mix,-5,0,100), "Autotune mix tăng":lambda e:self._step(self.mix,5,0,100), "Khử ồn giảm":lambda e:self._step(self.nstrength,-.05,0,1), "Khử ồn tăng":lambda e:self._step(self.nstrength,.05,0,1), "Bè giảm":lambda e:self._step(self.hl,-.05,0,.7), "Bè tăng":lambda e:self._step(self.hl,.05,0,.7), "Reverb giảm":lambda e:self._step(self.rm,-.05,0,1), "Reverb tăng":lambda e:self._step(self.rm,.05,0,1), "Delay giảm":lambda e:self._step(self.dm,-.05,0,1), "Delay tăng":lambda e:self._step(self.dm,.05,0,1)}
        for name, seq in self.shortcuts.items(): self.bind_all("<"+seq.replace("_","-")+">", actions[name])

    def _open_shortcuts(self):
        win=tk.Toplevel(self); win.title("Quản lý phím tắt — QuiLe-Autovocal"); win.geometry("520x560"); win.transient(self)
        ttk.Label(win,text="Bấm nút Gán rồi nhấn tổ hợp phím mới. Không dùng trùng phím.").pack(pady=10)
        rows=[]
        for name, seq in self.shortcuts.items():
            row=ttk.Frame(win); row.pack(fill="x",padx=14,pady=2); ttk.Label(row,text=name,width=25).pack(side="left"); value=tk.StringVar(value=seq.replace("_","+")); ttk.Label(row,textvariable=value,width=16).pack(side="left"); btn=ttk.Button(row,text="Gán"); btn.pack(side="right"); rows.append((name,value,btn))
            btn.config(command=lambda n=name,v=value,b=btn:self._capture_shortcut(win,n,v,b))
        ttk.Button(win,text="Khôi phục mặc định",command=lambda:self._reset_shortcuts(win)).pack(pady=12)

    def _capture_shortcut(self, win, name, value, button):
        button.config(text="Nhấn phím…"); win.focus_force()
        def capture(event):
            parts=[]
            if event.state & 0x4: parts.append("Control")
            if event.state & 0x1: parts.append("Shift")
            key=event.keysym
            if key.lower() in ("control_l","control_r","shift_l","shift_r"): return "break"
            parts.append(key if key.startswith("F") else key.lower())
            seq="_".join(parts)
            if seq in [v for k,v in self.shortcuts.items() if k != name]:
                messagebox.showwarning("Phím tắt bị trùng", "Tổ hợp này đã được gán cho chức năng khác."); button.config(text="Gán"); win.unbind("<Key>"); return "break"
            value.set("+".join(parts)); self.shortcuts[name]=seq; self._rebind_all(); button.config(text="Gán"); win.unbind("<Key>"); return "break"
        win.bind("<Key>",capture)

    def _reset_shortcuts(self, win):
        self._bind_shortcuts(); win.destroy(); self._open_shortcuts()

    def _flip(self, variable):
        variable.set(not variable.get()); self._apply(); return "break"

    def _step(self, variable, amount, low, high):
        try: variable.set(max(low, min(high, variable.get() + amount))); self._apply()
        except tk.TclError: pass
        return "break"

    def _load(self):
        try:
            ds=self.e.devices(); hosts=self.e.hostapis(); ranked=[]
            for i,d in enumerate(ds):
                if d['max_input_channels'] and d['max_output_channels']:
                    host=hosts[d['hostapi']]['name']; ranked.append(("ASIO" not in host.upper(),f"{i}: {d['name']} [{host}] ({d['max_input_channels']} in / {d['max_output_channels']} out)"))
            a=[text for _,text in sorted(ranked,key=lambda x:x[0])]; self.box['values']=a
            inputs=[f"{i}: {d['name']} [{hosts[d['hostapi']]['name']}]" for i,d in enumerate(ds) if d['max_input_channels']>0]; self.ak_box['values']=inputs
            if inputs:self.ak_box.current(0)
            if a:self.box.current(0);self.status.config(text="Đã nhận audio interface")
        except Exception:self.status.config(text="Không tìm thấy thiết bị audio")
    def _apply_preset(self):
        p=self.presets.get(self.preset.get())
        if not p:return
        self.retune.set(p["retune"]); self.mix.set(p["mix"]); self.nstrength.set(p["noise"]); self.hm.set(p["harmony"]); self.hl.set(p["hlevel"]); self.rm.set(p["reverb"]); self.rs.set(p["room"]); self.dm.set(p["delay"]); self.dms.set(p["delay_ms"]); self.df.set(p["feedback"]); self.ne.set(True); self.at_on.set(True); self.re_on.set(p["reverb"]>0); self.de_on.set(p["delay"]>0); self.ha_on.set(p["harmony"]!="Tắt"); self._apply(); self.status.config(text=f"Đã áp dụng preset: {self.preset.get()}")

    def _toggle_auto_key(self):
        try:
            if self.ak_on.get():
                idx=int(self.ak_source.get().split(":",1)[0]); self.e.start_auto_key(idx,int(self.rate.get().split()[0]),2); self.ak_status.set("Đang nghe nguồn nhạc nền…")
            else:
                self.e.stop_auto_key(); self.ak_status.set("Đã dừng Auto Key")
        except Exception as x:
            self.ak_on.set(False); self.ak_status.set("Lỗi nguồn Auto Key"); messagebox.showerror("Không mở được nguồn Auto Key",str(x))

    def _apply(self):
        try:self.e.set_params(note_names().index(self.key.get()),self.scale.get(),self.retune.get(),self.mix.get()/100,self.bypass.get(),self.hm.get(),self.hl.get(),self.rm.get(),self.rs.get(),self.dm.get(),self.dms.get(),self.df.get(),self.ne.get(),self.nstrength.get(),self.nlearning.get(),self.at_on.get(),self.ha_on.get(),self.re_on.get(),self.de_on.get())
        except (ValueError,tk.TclError):pass
    def _reset_noise(self):
        self.e.noise_suppressor.reset(); self.status.config(text="Đã đặt lại hồ sơ tiếng ồn")
    def _toggle(self):
        try:
            if not self.running:
                i=int(self.dev.get().split(":",1)[0]) if self.dev.get() else None; self._apply(); self.e.start(i,i,int(self.rate.get().split()[0]),int(self.buffer.get().split()[0]),True); self.running=True; self.btn.config(text="Dừng monitor"); self.status.config(text="Đang xử lý realtime")
            else:self.e.stop();self.running=False;self.btn.config(text="Bắt đầu monitor");self.status.config(text="Đã dừng")
        except Exception as x:messagebox.showerror("Không mở được audio interface",str(x))
    def _record(self):
        if self.recording:return
        p=filedialog.asksaveasfilename(defaultextension=".wav",filetypes=[("Tệp WAV","*.wav")]);
        if not p:return
        self.recording=True;self.status.config(text="Đang ghi âm…")
        def f():
            try:self.e.save_wav(p);self.after(0,lambda:messagebox.showinfo("Hoàn tất",f"Đã lưu:\n{p}"))
            except Exception as x:self.after(0,lambda:messagebox.showerror("Lỗi ghi âm",str(x)))
            finally:self.recording=False;self.after(0,lambda:self.status.config(text="Sẵn sàng"))
        threading.Thread(target=f,daemon=True).start()
    def _tick(self):
        h=self.e.detected_hz; self.note.config(text=hz_to_note(h)); self.pitch.config(text=f"Cao độ: {h:.1f} Hz | Mức tín hiệu: {self.e.level*100:.0f}%"); self.meter['value']=self.e.level*100
        if self.ak_on.get() and self.e.auto_key.confidence >= .18:
            names=note_names(); self.key.set(names[self.e.key]); self.scale.set(self.e.scale_name)
        self.ak_status.set(self.e.auto_key_status() if self.ak_on.get() else "Auto Key đang tắt"); self.after(100,self._tick)
    def _close(self):self.e.close();self.destroy()

if __name__=="__main__":QuiLeAutovocal().mainloop()
