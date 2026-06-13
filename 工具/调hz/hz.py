#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时音频均衡器 — 10 套全新差异化主题
"""

import os, sys, subprocess, importlib, threading, time, queue, tkinter as tk
from tkinter import messagebox
import numpy as np
import sounddevice as sd
from scipy import signal
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family'] = 'sans-serif'
try: matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
except: pass

for imp_name, pkg in [('numpy','numpy'),('scipy','scipy'),('sounddevice','sounddevice'),('matplotlib','matplotlib')]:
    try: importlib.import_module(imp_name)
    except:
        print(f"安装 {pkg}...")
        subprocess.check_call([sys.executable,'-m','pip','install',pkg], timeout=120)

BAND_LABELS = ['32Hz','64Hz','125Hz','250Hz','500Hz','1kHz','2kHz','4kHz','8kHz','16kHz']
BAND_RANGES = [(20,45),(45,90),(90,180),(180,355),(355,710),(710,1400),(1400,2800),(2800,5600),(5600,11200),(11200,20000)]
# 每个频率的通俗说明
BAND_DESCS = ["超重低音","大鼓·贝斯","低音力度","吉他·人声","人声主体","人声清晰度","弦乐明亮度","乐器细节","镲片·空气感","极高频泛音"
]

# ===== 10 套全新差异化主题 =====
THEMES = {
    "☁️ 极简白": {
        'bg':'#ffffff','card':'#f8f9fa','accent':'#4361ee','accent2':'#3a86ff',
        'text':'#1a1a2e','text2':'#6c757d','slider_bg':'#e9ecef','red':'#dc3545',
        'border':'#dee2e6','hover':'#e8f0fe','wave_alpha':0.15,
        'font_family':'Microsoft YaHei','border_relief':'flat','slider_w':14,'slider_len':160,
    },
    "🌙 暗夜黑": {
        'bg':'#0a0a0a','card':'#141414','accent':'#bb86fc','accent2':'#03dac6',
        'text':'#e1e1e1','text2':'#888888','slider_bg':'#2a2a2a','red':'#cf6679',
        'border':'#333333','hover':'#1e1e1e','wave_alpha':0.3,
        'font_family':'Segoe UI','border_relief':'flat','slider_w':13,'slider_len':170,
    },
    "💜 赛博朋克": {
        'bg':'#0d0221','card':'#150534','accent':'#ff2d95','accent2':'#00f5ff',
        'text':'#e0d0ff','text2':'#8070aa','slider_bg':'#2a1050','red':'#ff0040',
        'border':'#4a2080','hover':'#200848','wave_alpha':0.35,
        'font_family':'Consolas','border_relief':'groove','slider_w':16,'slider_len':180,
    },
    "🌿 森林绿": {
        'bg':'#f0f7f0','card':'#ffffff','accent':'#2d6a4f','accent2':'#52b788',
        'text':'#1b4332','text2':'#6b8e6b','slider_bg':'#d8edd8','red':'#e63946',
        'border':'#a7d8a7','hover':'#e8f5e8','wave_alpha':0.2,
        'font_family':'Georgia','border_relief':'ridge','slider_w':12,'slider_len':155,
    },
    "🌅 落日橙": {
        'bg':'#1a0a00','card':'#2a1500','accent':'#ff6b35','accent2':'#ffb703',
        'text':'#ffedd8','text2':'#cc9966','slider_bg':'#3d2000','red':'#d00000',
        'border':'#5a3500','hover':'#3d2000','wave_alpha':0.3,
        'font_family':'Trebuchet MS','border_relief':'sunken','slider_w':15,'slider_len':175,
    },
    "🌸 樱花粉": {
        'bg':'#fef0f5','card':'#ffffff','accent':'#e84393','accent2':'#a29bfe',
        'text':'#6c1442','text2':'#a0658a','slider_bg':'#fce4ec','red':'#e17055',
        'border':'#f8b4c8','hover':'#fef0f5','wave_alpha':0.18,
        'font_family':'Microsoft YaHei','border_relief':'flat','slider_w':11,'slider_len':150,
    },
    "🧊 极地蓝": {
        'bg':'#e8f4f8','card':'#ffffff','accent':'#0096c7','accent2':'#48cae4',
        'text':'#023e8a','text2':'#5e8b9e','slider_bg':'#caf0f8','red':'#e63946',
        'border':'#90e0ef','hover':'#dcf2f8','wave_alpha':0.2,
        'font_family':'Calibri','border_relief':'flat','slider_w':12,'slider_len':160,
    },
    "🎞️ 复古棕": {
        'bg':'#f4ecd8','card':'#faf3e0','accent':'#8b5a2b','accent2':'#c4956a',
        'text':'#3e2723','text2':'#8d6e63','slider_bg':'#e8dcc8','red':'#a52a2a',
        'border':'#d4c4a8','hover':'#f0e8d4','wave_alpha':0.22,
        'font_family':'Times New Roman','border_relief':'raised','slider_w':14,'slider_len':165,
    },
    "🌊 深海蓝": {
        'bg':'#0a1628','card':'#0f2544','accent':'#00b4d8','accent2':'#0077b6',
        'text':'#caf0f8','text2':'#7ba0b8','slider_bg':'#1a3050','red':'#e63946',
        'border':'#1e4060','hover':'#162d50','wave_alpha':0.3,
        'font_family':'Segoe UI','border_relief':'groove','slider_w':13,'slider_len':170,
    },
    "🎨 波普彩": {
        'bg':'#f5e6ff','card':'#ffffff','accent':'#ff006e','accent2':'#8338ec',
        'text':'#3a0ca3','text2':'#7209b7','slider_bg':'#e8d5f5','red':'#f72585',
        'border':'#d5b8f0','hover':'#f0e0ff','wave_alpha':0.2,
        'font_family':'Arial','border_relief':'ridge','slider_w':15,'slider_len':175,
    },
}

class RealTimeEQ:
    def __init__(self):
        self.gains = [0.0]*10
        self.bass_boost = 30
        self.sr = 48000
        self.bs = 1024
        self.ch = 2
        self.running = False
        self.istream = None
        self.out_dev = None
        self.lock = threading.RLock()
        self._sos = [None]*10; self._zi = [None]*10
        self._bsos = None; self._bzi = None
        self._dirty = True
        self._ol_thread = None
        self.buf = queue.Queue(maxsize=16)
        self.wf = queue.Queue(maxsize=2)
        self.in_dev = None
        self._probe()

    def _probe(self):
        devs = sd.query_devices()
        ha = sd.query_hostapis()
        wi = None
        for i,a in enumerate(ha):
            if 'WASAPI' in a['name'].upper(): wi=i; break
        # 打印所有设备信息（方便调试）
        print("="*60)
        print("可用的音频设备列表:")
        for i,d in enumerate(devs):
            ic=int(d['max_input_channels'])
            oc=int(d['max_output_channels'])
            ha_name = ha[d['hostapi']]['name'] if d['hostapi']<len(ha) else '?'
            print(f"  [{i}] {d['name']}  (in:{ic} out:{oc}) [{ha_name}]")
        print("="*60)
        # 1) 找 WASAPI loopback 设备
        cs = []
        for i,d in enumerate(devs):
            n=d['name'].lower(); ic=int(d['max_input_channels'])
            if ic==0: continue
            sc=10
            if wi is not None and d['hostapi']==wi:
                if 'loopback' in n or '回环' in n: sc=100
                elif '扬声器' in n and 'realtek' in n: sc=85
                elif '扬声器' in n or 'speaker' in n: sc=80
                elif '耳机' in n or 'headphone' in n: sc=70
                elif 'output' in n: sc=60
            if '立体声混音' in n or 'stereo mix' in n: sc=max(sc,90)
            # MME 下的立体声混音
            if '立体声混音' in n or 'stereo mix' in n: sc=max(sc,85)
            cs.append((sc,i,d,int(d['max_output_channels'])>0))
        cs.sort(key=lambda x:-x[0])
        if cs:
            _,i,d,ho=cs[0]
            print(f"  → 选中输入设备: [{i}] {d['name']}")
            self.in_dev=i; self.sr=int(d.get('default_samplerate',48000))
            self.ch=min(int(d['max_input_channels']),2); self._ho=ho
        else:
            # 2) 没找到输入设备：用默认输出设备做 loopback（WASAPI 方式）
            out_dev = sd.default.device[1] or 0
            out_info = sd.query_devices(out_dev)
            print(f"  → 未找到专用输入设备，尝试用输出设备做 loopback")
            print(f"  → 尝试设备: [{out_dev}] {out_info['name']}")
            # 在 WASAPI 下，可以用输出设备 + loopback 标志
            # 但 sounddevice 不直接支持 loopback，需要特殊处理
            # 尝试使用设备本身作为输入（某些 WASAPI 驱动支持）
            self.in_dev = out_dev
            self.sr = int(out_info.get('default_samplerate', 48000))
            self.ch = 2
            self._ho = True
            print(f"  → 如果仍无效，请启用「立体声混音」或安装 VB-Cable")
        self.out_dev = sd.default.device[1] or 0
        print(f"  → 输出设备: [{self.out_dev}] {sd.query_devices(self.out_dev)['name']}")
        print("="*60)

    def _rebuild(self):
        with self.lock:
            nyq=self.sr/2
            self._sos=[None]*10; self._zi=[None]*10
            for i in range(10):
                if abs(self.gains[i])<0.5: continue
                lo,hi=BAND_RANGES[i]
                lo_n=max(lo/nyq,1e-5); hi_n=min(hi/nyq,0.9999)
                if lo_n>=hi_n: continue
                s=signal.butter(4,[lo_n,hi_n],btype='band',output='sos')
                z=signal.sosfilt_zi(s)
                if self.ch>1: z=np.stack([z]*self.ch,axis=-1)
                self._sos[i]=s; self._zi[i]=z
            if self.bass_boost>0:
                c=min(150/nyq,0.9999)
                self._bsos=signal.butter(2,c,btype='low',output='sos')
                bz=signal.sosfilt_zi(self._bsos)
                if self.ch>1: bz=np.stack([bz]*self.ch,axis=-1)
                self._bzi=bz
            else: self._bsos=None; self._bzi=None
            self._dirty=False

    def process(self,d):
        with self.lock:
            if self._dirty: self._rebuild()
            r=d.copy(); h=False
            for i in range(10):
                s=self._sos[i]
                if s is None: continue
                g=10**(self.gains[i]/20)
                f,self._zi[i]=signal.sosfilt(s,d,zi=self._zi[i],axis=0)
                r+=f*g; h=True
            if h and np.max(np.abs(r))>0.99: r/=np.max(np.abs(r))*0.95
            if self._bsos is not None:
                b,self._bzi=signal.sosfilt(self._bsos,d,zi=self._bzi,axis=0)
                r+=b*(self.bass_boost/100*3.0)
                if np.max(np.abs(r))>0.99: r/=np.max(np.abs(r))*0.95
            return r.astype(np.float32)

    def _icb(self,indata,fr,ti,st):
        if indata.shape[0]==0: return
        try:
            p=self.process(indata.copy())
            try: self.buf.put_nowait(p)
            except queue.Full:
                try: self.buf.get_nowait(); self.buf.put_nowait(p)
                except: pass
            try: self.wf.put_nowait(indata[-200:])
            except: pass
        except: pass

    def _dcb(self,indata,outdata,fr,ti,st):
        if indata.shape[0]==0: outdata[:]=0; return
        try:
            p=self.process(indata.copy())
            if p.shape[1]!=outdata.shape[1]:
                if p.shape[1]<outdata.shape[1]: p=np.repeat(p,outdata.shape[1],axis=1)
                else: p=p[:,:outdata.shape[1]]
            outdata[:]=p[:fr]
            try: self.wf.put_nowait(indata[-200:])
            except: pass
        except: outdata[:]=indata[:fr]

    def _ol(self):
        while self.running:
            try:
                if not self.buf.empty():
                    ch=[]
                    try:
                        while True: ch.append(self.buf.get_nowait())
                    except queue.Empty: pass
                    c=np.concatenate(ch,axis=0)
                    if len(c)>self.sr: c=c[-self.sr:]
                    try:
                        sd.play(c,self.sr,device=self.out_dev); w=0
                        while self.running:
                            s=sd.get_stream()
                            if s is None: break
                            try:
                                if not s.active: break
                            except: break
                            w+=1
                            if w>100: break
                            time.sleep(0.01)
                    except: pass
                else: time.sleep(0.01)
            except: time.sleep(0.01)

    def start(self):
        if self.running: return
        self._rebuild()
        while not self.buf.empty():
            try: self.buf.get_nowait()
            except: break
        for ch in [self.ch,2,1]:
            try:
                self.istream=sd.InputStream(device=self.in_dev,channels=ch,
                    samplerate=self.sr,blocksize=self.bs,dtype='float32',
                    callback=self._icb,latency='low')
                self.istream.start()
                self.ch=ch; self.running=True
                # ★★★ 关键：启动输出线程，把处理后的声音发出去 ★★★
                self._ol_thread = threading.Thread(target=self._ol, daemon=True)
                self._ol_thread.start()
                return
            except Exception as e:
                if self.istream:
                    try: self.istream.close()
                    except: pass; self.istream=None
        for ch in [self.ch,2,1]:
            try:
                self.istream=sd.Stream(device=(self.in_dev,self.out_dev),
                    channels=(ch,2),samplerate=self.sr,blocksize=self.bs,
                    dtype='float32',callback=self._dcb,latency='low')
                self.istream.start()
                self.ch=ch; self.running=True
                # ★★★ 关键：启动输出线程，把处理后的声音发出去 ★★★
                self._ol_thread = threading.Thread(target=self._ol, daemon=True)
                self._ol_thread.start()
                return
            except Exception as e:
                if self.istream:
                    try: self.istream.close()
                    except: pass; self.istream=None
        raise Exception("所有模式均失败")

    def stop(self):
        self.running=False; time.sleep(0.15)
        try: sd.stop()
        except: pass
        if self._ol_thread and self._ol_thread.is_alive():
            self._ol_thread.join(timeout=1); self._ol_thread=None
        if self.istream:
            try: self.istream.abort()
            except: pass
            try: self.istream.close()
            except: pass
            self.istream=None
        try: sd.stop()
        except: pass

    def sg(self,i,v): self.gains[i]=v; self._dirty=True
    def sb(self,v): self.bass_boost=v; self._dirty=True
    def reset(self): self.gains=[0.0]*10; self.bass_boost=30; self._dirty=True; self._zi=[None]*10; self._bzi=None


# ===== 10 套全新差异化主题（5种布局 × 2配色） =====
THEMES = {
    "▐ 经典蓝白▐": {'bg':'#f5f5f5','card':'#ffffff','accent':'#4361ee','accent2':'#3a86ff','text':'#1e293b','text2':'#64748b','slider_bg':'#e2e8f0','red':'#ef4444','border':'#dee2e6','hover':'#eef2ff','wave_alpha':0.2,'font':'Microsoft YaHei','sw':14,'sl':170,'layout':'vert','br':'flat'},
    "▐ 暗夜黑紫▐": {'bg':'#0a0a0a','card':'#141414','accent':'#bb86fc','accent2':'#03dac6','text':'#e1e1e1','text2':'#888','slider_bg':'#2a2a2a','red':'#cf6679','border':'#333','hover':'#1e1e1e','wave_alpha':0.3,'font':'Segoe UI','sw':13,'sl':175,'layout':'vert','br':'flat'},

    "▐ 森林双行▐": {'bg':'#f0f7f0','card':'#ffffff','accent':'#2d6a4f','accent2':'#52b788','text':'#1b4332','text2':'#6b8e6b','slider_bg':'#d8edd8','red':'#e63946','border':'#a7d8a7','hover':'#e8f5e8','wave_alpha':0.2,'font':'Georgia','sw':13,'sl':150,'layout':'dual','br':'ridge'},
    "▐ 赛博双行▐": {'bg':'#0d0221','card':'#150534','accent':'#ff2d95','accent2':'#00f5ff','text':'#e0d0ff','text2':'#8070aa','slider_bg':'#2a1050','red':'#ff0040','border':'#4a2080','hover':'#200848','wave_alpha':0.35,'font':'Consolas','sw':15,'sl':160,'layout':'dual','br':'groove'},

    "▐ 落日横条▐": {'bg':'#1a0a00','card':'#2a1500','accent':'#ff6b35','accent2':'#ffb703','text':'#ffedd8','text2':'#cc9966','slider_bg':'#3d2000','red':'#d00000','border':'#5a3500','hover':'#3d2000','wave_alpha':0.3,'font':'Trebuchet MS','sw':14,'sl':0,'layout':'horz','br':'sunken'},
    "▐ 霓虹横条▐": {'bg':'#0f0f1a','card':'#1a1a2e','accent':'#ff2d95','accent2':'#00f5ff','text':'#e0e0ff','text2':'#8888aa','slider_bg':'#2a2a4a','red':'#ff0055','border':'#333355','hover':'#2a2a4a','wave_alpha':0.3,'font':'Segoe UI','sw':14,'sl':0,'layout':'horz','br':'flat'},

    "▐ 冰蓝分栏▐": {'bg':'#e8f4f8','card':'#ffffff','accent':'#0096c7','accent2':'#48cae4','text':'#023e8a','text2':'#5e8b9e','slider_bg':'#caf0f8','red':'#e63946','border':'#90e0ef','hover':'#dcf2f8','wave_alpha':0.2,'font':'Calibri','sw':12,'sl':200,'layout':'split','br':'flat'},
    "▐ 深海分栏▐": {'bg':'#0a1628','card':'#0f2544','accent':'#00b4d8','accent2':'#0077b6','text':'#caf0f8','text2':'#7ba0b8','slider_bg':'#1a3050','red':'#e63946','border':'#1e4060','hover':'#162d50','wave_alpha':0.3,'font':'Segoe UI','sw':12,'sl':200,'layout':'split','br':'groove'},

    "▐ 复古紧凑▐": {'bg':'#f4ecd8','card':'#faf3e0','accent':'#8b5a2b','accent2':'#c4956a','text':'#3e2723','text2':'#8d6e63','slider_bg':'#e8dcc8','red':'#a52a2a','border':'#d4c4a8','hover':'#f0e8d4','wave_alpha':0.22,'font':'Times New Roman','sw':10,'sl':0,'layout':'compact','br':'raised'},
    "▐ 波普紧凑▐": {'bg':'#f5e6ff','card':'#ffffff','accent':'#ff006e','accent2':'#8338ec','text':'#3a0ca3','text2':'#7209b7','slider_bg':'#e8d5f5','red':'#f72585','border':'#d5b8f0','hover':'#f0e0ff','wave_alpha':0.2,'font':'Arial','sw':10,'sl':0,'layout':'compact','br':'ridge'},
}

# ===== 10 套全新差异化主题 =====
THEMES = {
    "经典蓝白": {'bg':'#f5f5f5','card':'#ffffff','accent':'#4361ee','accent2':'#3a86ff','text':'#1e293b','text2':'#64748b','sbg':'#e2e8f0','red':'#ef4444','border':'#dee2e6','hover':'#eef2ff','wa':0.2,'fn':'Microsoft YaHei','sw':14,'sl':170,'lay':'vert','br':'flat'},
    "暗夜黑紫": {'bg':'#0a0a0a','card':'#141414','accent':'#bb86fc','accent2':'#03dac6','text':'#e1e1e1','text2':'#888','sbg':'#2a2a2a','red':'#cf6679','border':'#333','hover':'#1e1e1e','wa':0.3,'fn':'Segoe UI','sw':13,'sl':175,'lay':'vert','br':'flat'},
    "森林双行": {'bg':'#f0f7f0','card':'#ffffff','accent':'#2d6a4f','accent2':'#52b788','text':'#1b4332','text2':'#6b8e6b','sbg':'#d8edd8','red':'#e63946','border':'#a7d8a7','hover':'#e8f5e8','wa':0.2,'fn':'Georgia','sw':13,'sl':150,'lay':'dual','br':'ridge'},
    "赛博双行": {'bg':'#0d0221','card':'#150534','accent':'#ff2d95','accent2':'#00f5ff','text':'#e0d0ff','text2':'#8070aa','sbg':'#2a1050','red':'#ff0040','border':'#4a2080','hover':'#200848','wa':0.35,'fn':'Consolas','sw':15,'sl':160,'lay':'dual','br':'groove'},
    "落日横条": {'bg':'#1a0a00','card':'#2a1500','accent':'#ff6b35','accent2':'#ffb703','text':'#ffedd8','text2':'#cc9966','sbg':'#3d2000','red':'#d00000','border':'#5a3500','hover':'#3d2000','wa':0.3,'fn':'Trebuchet MS','sw':14,'sl':0,'lay':'horz','br':'sunken'},
    "霓虹横条": {'bg':'#0f0f1a','card':'#1a1a2e','accent':'#ff2d95','accent2':'#00f5ff','text':'#e0e0ff','text2':'#8888aa','sbg':'#2a2a4a','red':'#ff0055','border':'#333355','hover':'#2a2a4a','wa':0.3,'fn':'Segoe UI','sw':14,'sl':0,'lay':'horz','br':'flat'},
    "冰蓝分栏": {'bg':'#e8f4f8','card':'#ffffff','accent':'#0096c7','accent2':'#48cae4','text':'#023e8a','text2':'#5e8b9e','sbg':'#caf0f8','red':'#e63946','border':'#90e0ef','hover':'#dcf2f8','wa':0.2,'fn':'Calibri','sw':12,'sl':200,'lay':'split','br':'flat'},
    "深海分栏": {'bg':'#0a1628','card':'#0f2544','accent':'#00b4d8','accent2':'#0077b6','text':'#caf0f8','text2':'#7ba0b8','sbg':'#1a3050','red':'#e63946','border':'#1e4060','hover':'#162d50','wa':0.3,'fn':'Segoe UI','sw':12,'sl':200,'lay':'split','br':'groove'},
    "复古紧凑": {'bg':'#f4ecd8','card':'#faf3e0','accent':'#8b5a2b','accent2':'#c4956a','text':'#3e2723','text2':'#8d6e63','sbg':'#e8dcc8','red':'#a52a2a','border':'#d4c4a8','hover':'#f0e8d4','wa':0.22,'fn':'Times New Roman','sw':10,'sl':0,'lay':'compact','br':'raised'},
    "波普紧凑": {'bg':'#f5e6ff','card':'#ffffff','accent':'#ff006e','accent2':'#8338ec','text':'#3a0ca3','text2':'#7209b7','sbg':'#e8d5f5','red':'#f72585','border':'#d5b8f0','hover':'#f0e0ff','wa':0.2,'fn':'Arial','sw':10,'sl':0,'lay':'compact','br':'ridge'},
}
LAYOUT_NAMES = {'vert':'数字式','dual':'双行排列','horz':'水平滑条','split':'左右分栏','compact':'紧凑型'}

class ThemeGallery(tk.Toplevel):
    """主题画廊窗口 — 一次性展示全部10个主题"""
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("🎨 选择主题风格 — 点击预览图即可应用")
        self.geometry("960x580")
        self.resizable(False, False)
        self.configure(bg='#1a1a2e')
        self.transient(parent)
        self.grab_set()
        # 标题
        tk.Label(self, text="🎨 选择你喜欢的界面风格", font=('Microsoft YaHei', 16, 'bold'),
                 bg='#1a1a2e', fg='#ffffff').pack(pady=(15,5))
        tk.Label(self, text="点击任意主题卡片，立即切换到该风格", font=('Microsoft YaHei', 10),
                 bg='#1a1a2e', fg='#aaaacc').pack(pady=(0,10))
        # 卡片网格
        mf = tk.Frame(self, bg='#1a1a2e')
        mf.pack(expand=True, padx=10, pady=(0,10))
        names = list(THEMES.keys())
        for row in range(2):
            for col in range(5):
                idx = row * 5 + col
                if idx >= len(names): break
                name = names[idx]
                th = THEMES[name]
                card = tk.Frame(mf, width=175, height=220, bg=th['card'],
                                highlightbackground=th.get('border','#ccc'), highlightthickness=2,
                                cursor='hand2', relief='raised')
                card.grid(row=row, column=col, padx=6, pady=6)
                card.pack_propagate(False)
                # 缩略预览 - 用 Canvas 绘制 mini UI
                cv = tk.Canvas(card, width=165, height=145, bg=th['card'], bd=0, highlightthickness=0)
                cv.pack(pady=(5,0))
                # 顶部条（模拟标题栏）
                cv.create_rectangle(5, 3, 160, 18, fill=th['accent'], outline='', width=0)
                cv.create_text(12, 10, text='均衡器', font=('Arial', 6, 'bold'),
                               fill='#ffffff', anchor=tk.W)
                # 波形线（模拟波形图）
                pts = []
                for wx in range(10, 155, 3):
                    wy = 35 + 10 * __import__('math').sin(wx * 0.3)
                    pts.extend([wx, wy])
                if len(pts) >= 4:
                    cv.create_line(*pts, fill=th['accent'], width=1.2, smooth=True)
                # 滑块模拟（根据布局类型）
                cv.create_text(82, 63, text=LAYOUT_NAMES.get(th.get('lay','vert'),''),
                               font=('Arial', 7), fill=th['text2'], anchor=tk.CENTER)
                lay = th.get('lay', 'vert')
                if lay in ('vert', 'dual', 'compact'):
                    n_sliders = 10 if lay == 'vert' else 5
                    for si in range(n_sliders):
                        sx = 12 + si * (140 // max(n_sliders, 1))
                        sy = 72
                        bar_h = 35 + int(12 * __import__('math').sin(si * 1.5))
                        cv.create_rectangle(sx, sy + (50 - bar_h), sx + 7, sy + 50,
                                            fill=th['accent'], outline='', width=0)
                        cv.create_rectangle(sx, sy, sx + 7, sy + 50,
                                            fill=th['sbg'], outline='', width=0)
                        cv.create_rectangle(sx, sy + (50 - bar_h), sx + 7, sy + 50,
                                            fill=th['accent'], outline='', width=0)
                elif lay == 'horz':
                    for hi in range(5):
                        hy = 72 + hi * 14
                        bar_w = 30 + int(40 * __import__('math').sin(hi * 2.0))
                        cv.create_rectangle(20, hy, 20 + bar_w, hy + 8,
                                            fill=th['accent'], outline='', width=0)
                        cv.create_rectangle(20, hy, 145, hy + 8,
                                            fill=th['sbg'], outline='', width=0)
                        cv.create_rectangle(20, hy, 20 + bar_w, hy + 8,
                                            fill=th['accent'], outline='', width=0)
                elif lay == 'split':
                    for si in range(3):
                        sx = 12 + si * 25
                        bar_h = 30 + int(10 * __import__('math').sin(si * 1.8))
                        cv.create_rectangle(sx, 72 + (40 - bar_h), sx + 10, 72 + 40,
                                            fill=th['accent'], outline='', width=0)
                        cv.create_rectangle(sx, 72, sx + 10, 72 + 40,
                                            fill=th['sbg'], outline='', width=0)
                        cv.create_rectangle(sx, 72 + (40 - bar_h), sx + 10, 72 + 40,
                                            fill=th['accent'], outline='', width=0)
                    # 中间的波形
                    pts2 = []
                    for wx in range(80, 135, 3):
                        wy = 90 + 8 * __import__('math').sin(wx * 0.3 + 1)
                        pts2.extend([wx, wy])
                    if len(pts2) >= 4:
                        cv.create_line(*pts2, fill=th['accent2'], width=1, smooth=True)
                    for si in range(3):
                        sx = 135 + si * 25
                        bar_h = 30 + int(10 * __import__('math').sin(si * 1.8 + 3))
                        cv.create_rectangle(sx, 72 + (40 - bar_h), sx + 10, 72 + 40,
                                            fill=th['accent2'], outline='', width=0)
                        cv.create_rectangle(sx, 72, sx + 10, 72 + 40,
                                            fill=th['sbg'], outline='', width=0)
                        cv.create_rectangle(sx, 72 + (40 - bar_h), sx + 10, 72 + 40,
                                            fill=th['accent2'], outline='', width=0)
                # 底部 - 频段标签
                for bi, bl in enumerate(['32','500','1k','8k','16k']):
                    cv.create_text(12 + bi * 32, 125, text=bl, font=('Arial', 5), fill=th['text2'], anchor=tk.W)
                # 主题名称
                tk.Label(card, text=name, font=('Microsoft YaHei', 10, 'bold'),
                         bg=th['card'], fg=th['text']).pack(pady=(2,0))
                tk.Label(card, text=f"布局: {LAYOUT_NAMES.get(th.get('lay','vert'),'')}",
                         font=('Arial', 7), bg=th['card'], fg=th['text2']).pack()
                # 点击事件
                card.bind('<Button-1>', lambda e, n=name: self._pick(n))
                for w in card.winfo_children():
                    w.bind('<Button-1>', lambda e, n=name: self._pick(n))

    def _pick(self, name):
        self.callback(name)
        self.destroy()


# ===== 10 套全新差异化主题（5种布局 × 2种配色） =====
THEMES = {
    "☀️ 晴空白":   {'bg':'#f5f5f7','card':'#ffffff','accent':'#0071e3','accent2':'#34c759','text':'#1d1d1f','text2':'#86868b','sbg':'#e8e8ed','red':'#ff3b30','border':'#d2d2d7','hover':'#e8f0fe','wa':0.12,'fn':'Microsoft YaHei','sw':14,'sl':180,'lay':'vert','br':'flat'},
    "🌑 午夜黑":   {'bg':'#1c1c1e','card':'#2c2c2e','accent':'#0a84ff','accent2':'#5e5ce6','text':'#f5f5f7','text2':'#98989d','sbg':'#3a3a3c','red':'#ff453a','border':'#48484a','hover':'#333335','wa':0.25,'fn':'Segoe UI','sw':13,'sl':190,'lay':'vert','br':'flat'},
    "🌿 森林绿":   {'bg':'#f0f7f0','card':'#ffffff','accent':'#2d6a4f','accent2':'#52b788','text':'#1b4332','text2':'#6b8e6b','sbg':'#d8edd8','red':'#e63946','border':'#a7d8a7','hover':'#e8f5e8','wa':0.18,'fn':'Georgia','sw':12,'sl':150,'lay':'dual','br':'ridge'},
    "💜 暗夜紫":   {'bg':'#0d0221','card':'#150534','accent':'#bb86fc','accent2':'#03dac6','text':'#e0d0ff','text2':'#8070aa','sbg':'#2a1050','red':'#cf6679','border':'#4a2080','hover':'#200848','wa':0.30,'fn':'Consolas','sw':14,'sl':155,'lay':'dual','br':'groove'},
    "🍑 暖阳橙":   {'bg':'#fff8f0','card':'#ffffff','accent':'#ff9500','accent2':'#ffb340','text':'#2d1b00','text2':'#b28040','sbg':'#ffe8cc','red':'#d00000','border':'#ffd599','hover':'#fff1e0','wa':0.15,'fn':'Trebuchet MS','sw':16,'sl':0,'lay':'horz','br':'flat'},
    "🔥 熔岩红":   {'bg':'#1a0500','card':'#2d0e00','accent':'#ff4500','accent2':'#ff6b35','text':'#ffd7c0','text2':'#cc7744','sbg':'#4a1a00','red':'#ff0000','border':'#6b2a00','hover':'#3d1500','wa':0.28,'fn':'Impact','sw':15,'sl':0,'lay':'horz','br':'sunken'},
    "🌊 海洋蓝":   {'bg':'#f0f8ff','card':'#ffffff','accent':'#0077b6','accent2':'#00b4d8','text':'#023e8a','text2':'#6096b4','sbg':'#d0ebff','red':'#dc3545','border':'#a0c4e8','hover':'#e0f0ff','wa':0.15,'fn':'Arial','sw':12,'sl':0,'lay':'split','br':'flat'},
    "👾 赛博朋克": {'bg':'#0a0015','card':'#160026','accent':'#ff2d95','accent2':'#00f5ff','text':'#e0d0ff','text2':'#8060cc','sbg':'#2a0040','red':'#ff0040','border':'#5a0080','hover':'#200040','wa':0.35,'fn':'Courier New','sw':13,'sl':0,'lay':'split','br':'groove'},
    "🌸 樱花粉":   {'bg':'#fef0f5','card':'#ffffff','accent':'#e84393','accent2':'#fd79a8','text':'#4a1942','text2':'#b07a9a','sbg':'#fce4ec','red':'#d63031','border':'#f5c6d0','hover':'#fdf0f5','wa':0.12,'fn':'Microsoft YaHei','sw':11,'sl':110,'lay':'compact','br':'flat'},
    "🖤 极简黑":   {'bg':'#000000','card':'#111111','accent':'#ffffff','accent2':'#aaaaaa','text':'#eeeeee','text2':'#777777','sbg':'#222222','red':'#ff4444','border':'#333333','hover':'#1a1a1a','wa':0.20,'fn':'Arial','sw':10,'sl':100,'lay':'compact','br':'flat'},
}
LAYOUT_NAMES = {'vert':'垂直经典','dual':'双行排列','horz':'水平滑条','split':'左右分栏','compact':'紧凑网格'}

class ThemeGallery(tk.Toplevel):
    """主题画廊 — 10套主题一次性预览，点击即用"""
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("🎨 选择界面风格")
        self.geometry("1000x620")
        self.resizable(False, False)
        self.configure(bg='#1c1c1e')
        self.transient(parent)
        self.grab_set()
        tk.Label(self, text="🎨 10 套界面风格 · 点击即用",
                 font=('Helvetica Neue', 18, 'bold'), bg='#1c1c1e', fg='#ffffff').pack(pady=(18,2))
        tk.Label(self, text="每套包含独特的布局和配色，总有一款适合你",
                 font=('Helvetica Neue', 8), bg='#1c1c1e', fg='#98989d').pack(pady=(0,12))
        mf = tk.Frame(self, bg='#1c1c1e')
        mf.pack(expand=True, padx=12, pady=(0,10))
        names = list(THEMES.keys())
        for row in range(2):
            for col in range(5):
                idx = row * 5 + col
                if idx >= len(names): break
                name = names[idx]
                th = THEMES[name]
                card = tk.Frame(mf, width=178, height=248, bg='#2c2c2e',
                                highlightbackground='#48484a', highlightthickness=1,
                                cursor='hand2', relief='flat')
                card.grid(row=row, column=col, padx=5, pady=5)
                card.pack_propagate(False)
                cv = tk.Canvas(card, width=168, height=165, bg=th['card'],
                               bd=0, highlightthickness=0)
                cv.pack(pady=(6,0))
                # 缩略图
                import math as _m
                cv.create_rectangle(4, 3, 164, 18, fill=th['accent'], outline='', width=0)
                cv.create_text(10, 10, text='均衡器', font=('Helvetica Neue', 6, 'bold'),
                               fill='#ffffff', anchor=tk.W)
                lay = th.get('lay', 'vert')
                if lay == 'vert':
                    for i in range(10):
                        sx = 8 + i * 15; bh = 30 + int(15 * _m.sin(i * 1.3 + 0.5))
                        cv.create_rectangle(sx, 26, sx+9, 72, fill=th['sbg'], outline='', width=0)
                        cv.create_rectangle(sx, 72-bh, sx+9, 72, fill=th['accent'], outline='', width=0)
                        cv.create_text(sx+4, 76, text=['32','64','125','250','500','1k','2k','4k','8k','16k'][i],
                                       font=('Helvetica Neue', 4), fill=th['text2'], anchor=tk.N)
                elif lay == 'dual':
                    for ri in range(2):
                        for ci in range(5):
                            sx = 10 + ci * 31; sy = 26 + ri * 40
                            bh = 20 + int(10 * _m.sin(ri*5+ci*1.5))
                            cv.create_rectangle(sx, sy, sx+20, sy+28, fill=th['sbg'], outline='', width=0)
                            cv.create_rectangle(sx, sy+28-bh, sx+20, sy+28, fill=th['accent'], outline='', width=0)
                            cv.create_text(sx+10, sy+30, text=['32','125','500','2k','8k'][ci],
                                           font=('Helvetica Neue', 4), fill=th['text2'], anchor=tk.N)
                elif lay == 'horz':
                    for i in range(8):
                        hy = 26 + i * 8; bw = 30 + int(80 * _m.sin(i * 1.1 + 0.3))
                        cv.create_rectangle(10, hy, 155, hy+6, fill=th['sbg'], outline='', width=0)
                        cv.create_rectangle(10, hy, 10+int(bw*0.7), hy+6, fill=th['accent'], outline='', width=0)
                    for i in range(8):
                        cv.create_text(3, 26 + i*8 + 3, text=['32','64','125','250','500','1k','2k','4k'][i],
                                       font=('Helvetica Neue', 3), fill=th['text2'], anchor=tk.W)
                elif lay == 'split':
                    for si in range(2):
                        for j in range(4):
                            sx = 8 + si * 80 + j * 18; bh = 20 + int(8 * _m.sin(j * 1.8 + si * 2.0))
                            clr = th['accent'] if si==0 else th['accent2']
                            cv.create_rectangle(sx, 26, sx+12, 70, fill=th['sbg'], outline='', width=0)
                            cv.create_rectangle(sx, 70-bh, sx+12, 70, fill=clr, outline='', width=0)
                    pts = []
                    for wx in range(75, 93):
                        wy = 45 + 12 * _m.sin(wx * 0.5 + 1); pts.extend([wx, wy])
                    if len(pts) >= 4:
                        cv.create_line(*pts, fill=th['accent2'], width=1.2, smooth=True)
                elif lay == 'compact':
                    for ri in range(2):
                        for ci in range(5):
                            sx = 8 + ci * 31; sy = 24 + ri * 38
                            bh = 14 + int(8 * _m.sin(ri*5+ci*1.7))
                            cv.create_rectangle(sx, sy, sx+24, sy+28, fill=th['sbg'], outline='', width=0)
                            cv.create_rectangle(sx, sy+28-bh, sx+24, sy+28, fill=th['accent'], outline='', width=0)
                            cv.create_text(sx+12, sy+30, text=['32','125','500','2k','8k'][ci],
                                           font=('Helvetica Neue', 4), fill=th['text2'], anchor=tk.N)
                # 底部波形装饰
                pts = []
                for wx in range(5, 163, 4):
                    wy = 145 + int(6 * _m.sin(wx * 0.2 + 2)); pts.extend([wx, wy])
                if len(pts) >= 4:
                    cv.create_line(*pts, fill=th.get('accent2', th['accent']), width=1.0, smooth=True)
                # 主题名称
                tk.Label(card, text=name, font=('Helvetica Neue', 10, 'bold'),
                         bg='#2c2c2e', fg='#ffffff').pack(pady=(3,0))
                tk.Label(card, text=LAYOUT_NAMES.get(th.get('lay',''), ''),
                         font=('Helvetica Neue', 7), bg='#2c2c2e', fg='#98989d').pack()
                # 点击
                card.bind('<Button-1>', lambda e, n=name: self._pick(n))
                for w in card.winfo_children():
                    w.bind('<Button-1>', lambda e, n=name: self._pick(n))
                card.bind('<Enter>', lambda e, c=card: c.configure(highlightbackground='#0a84ff', highlightthickness=2))
                card.bind('<Leave>', lambda e, c=card: c.configure(highlightbackground='#48484a', highlightthickness=1))
    def _pick(self, name):
        self.callback(name)
        self.destroy()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("实时音频均衡器")
        self.geometry("1000x520")
        self.minsize(800, 420)
        self.theme_name = list(THEMES.keys())[0]
        self.C = dict(THEMES[self.theme_name])
        self.configure(bg=self.C['bg'])
        self.eq = RealTimeEQ()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._all_sls = []
        self._all_vls = []
        self._all_blls = []
        self._eq_frame = None
        self._pbs = []
        self._resize_timer = None
        self.bind('<Configure>', self._on_resize)
        self._build()
        self._apply_theme()

    def _open_gallery(self):
        ThemeGallery(self, self._switch)

    # ── 内置使用说明 ──
    def _show_help(self):
        win = tk.Toplevel(self)
        win.title("使用说明")
        win.geometry("720x580")
        win.resizable(False, False)
        win.configure(bg='#f5f5f7')
        win.transient(self)
        win.grab_set()
        # 标题区
        tk.Label(win, text="🎵 实时音频均衡器 — 使用说明",
                 font=('Helvetica Neue', 16, 'bold'), bg='#f5f5f7', fg='#1d1d1f').pack(pady=(18,4))
        tk.Label(win, text="调高音、调低音，让电脑声音更动听",
                 font=('Helvetica Neue', 8), bg='#f5f5f7', fg='#86868b').pack(pady=(0,12))
        # 可滚动内容
        mf = tk.Frame(win, bg='#f5f5f7')
        mf.pack(fill=tk.BOTH, expand=True, padx=20)
        cv = tk.Canvas(mf, bg='#f5f5f7', bd=0, highlightthickness=0)
        sbar = tk.Scrollbar(mf, orient=tk.VERTICAL, command=cv.yview)
        inf = tk.Frame(cv, bg='#f5f5f7')
        inf.bind('<Configure>', lambda e: cv.configure(scrollregion=cv.bbox('all')))
        cv.create_window((0,0), window=inf, anchor='nw', width=670)
        cv.configure(yscrollcommand=sbar.set)
        cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sbar.pack(side=tk.RIGHT, fill=tk.Y)
        # 鼠标滚轮
        def _on_mousewheel(e):
            cv.yview_scroll(int(-1*(e.delta/120)), 'units')
        cv.bind_all('<MouseWheel>', _on_mousewheel)
        win.protocol("WM_DELETE_WINDOW", lambda: (cv.unbind_all('<MouseWheel>'), win.destroy()))

        def section(parent, icon, title, text_lines):
            sf = tk.Frame(parent, bg='#ffffff', highlightbackground='#d2d2d7', highlightthickness=1, relief='flat')
            sf.pack(fill=tk.X, pady=4)
            tk.Label(sf, text=f"{icon}  {title}", font=('Helvetica Neue', 12, 'bold'),
                     bg='#ffffff', fg='#1d1d1f', anchor=tk.W).pack(fill=tk.X, padx=15, pady=(8,2))
            for line in text_lines:
                if line.startswith('  ─'):
                    tk.Frame(sf, height=1, bg='#e8e8ed').pack(fill=tk.X, padx=15, pady=4)
                elif line.startswith('  ▸'):
                    tk.Label(sf, text=line, font=('Helvetica Neue', 8),
                             bg='#ffffff', fg='#3a3a3c', anchor=tk.W, justify=tk.LEFT).pack(fill=tk.X, padx=25, pady=1)
                else:
                    tk.Label(sf, text=line, font=('Helvetica Neue', 8),
                             bg='#ffffff', fg='#1d1d1f', anchor=tk.W, justify=tk.LEFT).pack(fill=tk.X, padx=15, pady=1)
            tk.Label(sf, text='', bg='#ffffff').pack(pady=(0,4))

        section(inf, "🎯", "这个程序是干什么的？", [
            "这是一个 实时音频均衡器（EQ），可以调节电脑播放的所有声音。",
            "",
            "  ▸ 放音乐时：让低音更沉、人声更清晰",
            "  ▸ 看电影时：增强对白、营造环绕感",
            "  ▸ 打游戏时：放大脚步声、枪声",
            "",
            "它处理的是 整个电脑 的声音，不是某个单独软件。",
        ])

        section(inf, "🧩", "界面布局（从上到下）", [
            "① 顶部标题栏 — 程序名称 + 换皮肤 + 看本说明",
            "② 波形图 — 声音的「心跳」，有声音时会跳动",
            "③ 均衡器 — 10 个滑块，每个控制一段频率",
            "④ 控制栏 — 启动/停止 + 低音 + 预设方案",
            "⑤ 状态栏 — 显示当前工作状态",
        ])

        section(inf, "🎚", "10 个滑块分别控制什么？", [
            "   滑块       频率范围       影响什么声音",
            "  ─────────────────────────────────────",
            "  ▸ 32 Hz  — 超低频     →  地震般的超重低音",
            "  ▸ 64 Hz  — 低频       →  大鼓、贝斯",
            "  ▸ 125 Hz — 中低频     →  低音提琴、鼓的力度",
            "  ▸ 250 Hz — 中低频     →  吉他、人声下部",
            "  ▸ 500 Hz — 中频       →  人声主体、中音乐器",
            "  ▸ 1 kHz  — 中频       →  人声清晰度、电话音",
            "  ▸ 2 kHz  — 中高频     →  人声明亮度、弦乐",
            "  ▸ 4 kHz  — 高频       →  乐器细节、齿音",
            "  ▸ 8 kHz  — 高频       →  镲片、空气感",
            "  ▸ 16 kHz — 超高频     →  极高频泛音",
            "",
            "  往上推 ↗ = 增强该频率   往下拉 ↘ = 减弱该频率",
        ])

        section(inf, "🎮", "一步一步使用教程", [
            "第 1 步：打开程序后，先放一首歌或打开视频",
            "第 2 步：点击「▶ 启动」按钮（均衡器开始工作）",
            "第 3 步：看波形图有没有跳动——跳动说明正常",
            "第 4 步：上下拖动滑块，感受声音变化",
            "第 5 步：想快速体验？点下面的预设按钮：",
            "        「低音」→ 增强鼓声，更震撼",
            "        「人声」→ 让唱歌更清晰通透",
            "        「摇滚」→ 整体更有力度",
            "        「古典」→ 更自然平衡",
            "        「舞曲」→ 动感强劲",
            "        「平坦」→ 恢复原始声音",
            "第 6 步：想换界面风格？右上角选主题或点「🎨 全部主题」",
            "第 7 步：点「停止」或关窗口结束",
        ])

        section(inf, "💡", "小技巧", [
            "  ▸ 先全部归零（点「重置」），再慢慢调，更容易听出变化",
            "  ▸ 低音滑块调太高可能喇叭会破音，建议不超过 +6",
            "  ▸ 调高音时小心齿音（嘶嘶声），适度即可",
            "  ▸ 不同耳机/音箱听感不同，以您自己的耳朵为准",
            "  ▸ 窗口可以自由拉大拉小，全屏也能用",
        ])

        section(inf, "❓", "常见问题", [
            "Q: 点启动后听不到变化？",
            "  A: 确保正在播放音乐/视频，看波形图是否跳动。",
            "     有些电脑需要选择正确的音频输入设备。",
            "",
            "Q: 声音有杂音/爆音？",
            "  A: 滑块不要调太极端，尤其是低音不要超过 +8。",
            "",
            "Q: 怎么恢复原始声音？",
            "  A: 点击「重置」即可归零，或选择预设「平坦」。",
            "",
            "Q: 关掉程序效果还在吗？",
            "  A: 关掉即恢复原始声音，不会永久改变。",
        ])

    def _on_resize(self, event):
        if event.widget is not self:
            return
        if self._resize_timer:
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(150, self._do_resize, event.width, event.height)

    def _do_resize(self, w, h):
        self._resize_timer = None
        if hasattr(self, '_fig') and hasattr(self, '_canvas'):
            new_w = max(3, min(w / 100, 20))
            # ★ 全屏时波形图自动填满所有剩余空间 ★
            # 计算公式：窗口可用高度 ÷ 100（英寸转像素）
            new_h = max(0.2, (h - 200) / 100)
            self._fig.set_size_inches(new_w, new_h)
            self._canvas.draw_idle()
        # 数字式数值字体随窗口略为放大
        if hasattr(self, '_all_vls'):
            for vl in self._all_vls:
                if vl.winfo_exists() and vl.winfo_ismapped():
                    fs = min(8 + int(w / 700), 13)
                    vl.configure(font=('Helvetica Neue', fs, 'bold'))

    def _clear(self):
        for w in list(self.winfo_children()):
            try: w.destroy()
            except: pass
        self._all_sls.clear()
        self._all_vls.clear()
        self._all_blls.clear()
        self._eq_frame = None
        self._pbs = []
        pass  # spacer 已移除

    def _build_top(self):
        f = tk.Frame(self, relief=tk.FLAT)
        f.pack(fill=tk.X, padx=4, pady=(2,0))
        self._topf = f
        tk.Label(f, text="🎛 EQ", font=('Helvetica Neue', 9, 'bold')).pack(side=tk.LEFT, padx=4)
        tk.Button(f, text="❓", font=('Helvetica Neue', 7),
                  relief=tk.FLAT, padx=4, pady=0, cursor='hand2',
                  command=self._show_help, bd=0).pack(side=tk.LEFT, padx=(0,2))
        tk.Button(f, text="🎨 全部主题", font=('Helvetica Neue', 7),
                  relief=tk.FLAT, padx=12, pady=4, cursor='hand2',
                  command=self._open_gallery, bd=0).pack(side=tk.RIGHT, padx=(0,5))
        tk.Label(f, text="主题:", font=('Helvetica Neue', 9)).pack(side=tk.RIGHT, padx=(0,3))
        self._tv = tk.StringVar(value=self.theme_name)
        self._tm = tk.OptionMenu(f, self._tv, *THEMES.keys(), command=self._switch)
        self._tm.config(font=('Helvetica Neue', 7), relief=tk.FLAT, bd=0,
                        indicatoron=False, highlightthickness=0)
        self._tm.pack(side=tk.RIGHT, padx=(0,8))
        self._st = tk.Label(f, text="就绪", font=('Helvetica Neue', 10))
        self._st.pack(side=tk.RIGHT, padx=15)

    def _build_wave(self, h=0.3):
        self._fig = Figure(figsize=(10, h), dpi=80)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_ylim([-1, 1])
        self._canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=(6,0))
        self._canvas.draw()

    def _build_status(self):
        f = tk.Frame(self, height=26)
        f.pack(fill=tk.X, side=tk.BOTTOM)
        f.pack_propagate(False)
        self._sbl = tk.Label(f, text="就绪 - 点击「启动」开始处理", font=('Helvetica Neue', 7), anchor=tk.W)
        self._sbl.pack(side=tk.LEFT, padx=20)

    def _build_ctrl(self):
        cf = tk.Frame(self, relief=tk.FLAT)
        cf.pack(fill=tk.X, padx=20, pady=(5,0))
        self._ctf = cf
        self._ctf._is_ctrl = True
        # macOS 风格按钮 — 圆角药丸形
        self._bt = tk.Button(cf, text="▶ 启动", font=('Helvetica Neue', 11, 'bold'),
            relief=tk.FLAT, padx=28, pady=4, cursor='hand2', command=self._toggle, bd=0)
        self._bt.pack(side=tk.LEFT, padx=(0,8), pady=4)
        self._bt.bind('<Enter>', lambda e: self._sbl.config(text="▶ 点击启动均衡器，开始处理所有系统音频"))
        self._bt.bind('<Leave>', lambda e: self._sbl.config(text="就绪 - 点击「启动」开始处理"))
        self._rst = tk.Button(cf, text="↺ 重置", font=('Helvetica Neue', 8),
            relief=tk.FLAT, padx=16, pady=4, cursor='hand2', command=self._reset, bd=0)
        self._rst.pack(side=tk.LEFT, padx=(0,15), pady=4)
        self._rst.bind('<Enter>', lambda e: self._sbl.config(text="↺ 将所有滑块归零，恢复原始声音"))
        self._rst.bind('<Leave>', lambda e: self._sbl.config(text="就绪 - 点击「启动」开始处理"))
        tk.Label(cf, text="低音", font=('Helvetica Neue', 10)).pack(side=tk.LEFT, padx=(0,2))
        tk.Label(cf, text="(整体震撼感)", font=('Helvetica Neue', 7), fg='#86868b').pack(side=tk.LEFT, padx=(0,5))
        self._bv = tk.IntVar(value=30)
        tk.Scale(cf, from_=100, to=0, orient=tk.HORIZONTAL, variable=self._bv,
            length=60, width=10, sliderrelief=tk.FLAT, bd=0, font=('Helvetica Neue', 7),
            command=self._bcb).pack(side=tk.LEFT)
        self._bvl = tk.Label(cf, text="30%", font=('Helvetica Neue', 10, 'bold'), width=4)
        self._bvl.pack(side=tk.LEFT, padx=5)
        # 分隔线
        tk.Frame(cf, width=1, bg='#d2d2d7').pack(side=tk.LEFT, fill=tk.Y, padx=(15,10), pady=6)
        tk.Label(cf, text="预设:", font=('Helvetica Neue', 10)).pack(side=tk.LEFT, padx=(0,5))
        tk.Label(cf, text="(一键切换风格)", font=('Helvetica Neue', 7), fg='#86868b').pack(side=tk.LEFT, padx=(0,5))
        presets = [("平坦",[0]*10,30),("低音",[6,5,3,1,0,-1,-2,-2,-3,-4],70),
                   ("人声",[-2,-1,2,4,5,5,3,1,0,-1],20),("摇滚",[4,3,2,0,0,1,2,3,3,2],50),
                   ("古典",[2,2,1,1,1,1,1,2,2,2],30),("舞曲",[7,6,4,2,0,-1,0,1,2,2],80)]
        for n,g,b in presets:
            pb = tk.Button(cf, text=n, font=('Helvetica Neue', 7),
                relief=tk.FLAT, padx=12, pady=3, cursor='hand2',
                command=lambda gg=g,bb=b: self._apply(gg,bb), bd=0)
            pb.pack(side=tk.LEFT, padx=2)
            self._pbs.append(pb)

    # ═══ 5种布局 — macOS 风格═ ══
    def _eq_vert(self):
        """数字式均衡器 — 不使用滑块，更省空间"""
        ef = tk.Frame(self, relief=tk.FLAT)
        ef.pack(fill=tk.X, padx=8, pady=(2,0))
        self._eq_frame = ef
        self._dig_values = [0.0] * 10
        for ri in range(2):
            rf = tk.Frame(ef)
            rf.pack(fill=tk.X, padx=4, pady=(0,2))
            for ci in range(5):
                i = ri * 5 + ci
                bf = tk.Frame(rf, bd=1, relief=tk.GROOVE, bg='#f0f0f0')
                bf.pack(side=tk.LEFT, fill=tk.X, padx=2, expand=True)
                # 频率名
                tk.Label(bf, text=BAND_LABELS[i], font=('Helvetica Neue', 5, 'bold'),
                         bg='#f0f0f0', fg='#555').pack(pady=(1,0))
                # 数值（大字显示）
                vl = tk.Label(bf, text=" 0.0", font=('Helvetica Neue', 11, 'bold'),
                              bg='#f0f0f0', fg='#333')
                vl.pack(pady=(0,0))
                self._all_vls.append(vl)
                # +/- 按钮
                bf2 = tk.Frame(bf, bg='#f0f0f0')
                bf2.pack(pady=(0,1))
                btn_m = tk.Button(bf2, text="−", font=('Helvetica Neue', 7, 'bold'),
                                  width=2, relief=tk.FLAT, padx=0, pady=0, bd=0,
                                  command=lambda idx=i: self._adj(idx, -0.5))
                btn_m.pack(side=tk.LEFT, padx=1)
                btn_p = tk.Button(bf2, text="+", font=('Helvetica Neue', 7, 'bold'),
                                  width=2, relief=tk.FLAT, padx=0, pady=0, bd=0,
                                  command=lambda idx=i: self._adj(idx, 0.5))
                btn_p.pack(side=tk.LEFT, padx=1)

    def _eq_dual(self):
        ef = tk.Frame(self, relief=tk.FLAT)
        ef.pack(fill=tk.BOTH, padx=10, pady=(2,0), expand=True)
        self._eq_frame = ef
        tk.Label(ef, text="均衡器 · 双行排列", font=('Helvetica Neue', 13, 'bold')).pack(anchor=tk.W, padx=15, pady=(8,2))
        for ri in range(2):
            rf = tk.Frame(ef)
            rf.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,2))
            for ci in range(5):
                i = ri*5+ci
                bf = tk.Frame(rf)
                bf.pack(side=tk.LEFT, fill=tk.BOTH, padx=4, expand=True)
                vl = tk.Label(bf, text="0.0", font=('Helvetica Neue', 8))
                vl.pack(pady=(0,1)); self._all_vls.append(vl)
                sl = tk.Scale(bf, from_=12, to=-12, resolution=0.5, length=60, width=14,
                    sliderrelief=tk.FLAT, bd=0, font=('Helvetica Neue', 6),
                    command=lambda _, idx=i: self._scb(idx))
                sl.set(0); sl.pack(fill=tk.BOTH, pady=1, expand=True); self._all_sls.append(sl)
                lbl = tk.Label(bf, text=BAND_LABELS[i], font=('Helvetica Neue', 8, 'bold'))
                lbl.pack(); self._all_blls.append(lbl)
                # 说明文字已移至状态栏显示

    def _eq_horz(self):
        ef = tk.Frame(self, relief=tk.FLAT)
        ef.pack(fill=tk.BOTH, padx=10, pady=(2,0), expand=True)
        self._eq_frame = ef
        tk.Label(ef, text="均衡器 · 水平滑条", font=('Helvetica Neue', 13, 'bold')).pack(anchor=tk.W, padx=15, pady=(8,2))
        cf = tk.Frame(ef)
        cf.pack(fill=tk.BOTH, padx=20, pady=(0,5), expand=True)
        for i,lb in enumerate(BAND_LABELS):
            rf = tk.Frame(cf)
            rf.pack(fill=tk.BOTH, pady=2, expand=True)
            tk.Label(rf, text=lb, font=('Helvetica Neue', 8, 'bold'), width=5, anchor=tk.E).pack(side=tk.LEFT, padx=(0,2))
            sl = tk.Scale(rf, from_=12, to=-12, resolution=0.5, orient=tk.HORIZONTAL,
                length=0, width=16, sliderrelief=tk.FLAT, bd=0, font=('Helvetica Neue', 6),
                command=lambda _, idx=i: self._scb(idx))
            sl.set(0); sl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2); self._all_sls.append(sl)
            vl = tk.Label(rf, text="0.0dB", font=('Helvetica Neue', 7), width=7, anchor=tk.W)
            vl.pack(side=tk.LEFT, padx=(3,0)); self._all_vls.append(vl)

    def _eq_split(self):
        ef = tk.Frame(self, relief=tk.FLAT)
        ef.pack(fill=tk.BOTH, padx=12, pady=(2,0), expand=True)
        self._eq_frame = ef
        mf = tk.Frame(ef)
        mf.pack(fill=tk.BOTH, expand=True, padx=3, pady=(0,2))
        for side_idx in (0,1):
            sf = tk.Frame(mf)
            sf.pack(side=tk.LEFT if side_idx==0 else tk.RIGHT, fill=tk.BOTH, expand=True, padx=3)
            for j in range(5):
                i = side_idx*5+j
                bf = tk.Frame(sf)
                bf.pack(fill=tk.BOTH, padx=2, pady=2, expand=True)
                tk.Label(bf, text=BAND_LABELS[i], font=('Helvetica Neue', 7, 'bold'), width=4, anchor=tk.E).pack(side=tk.LEFT, padx=(0,2))
                sl = tk.Scale(bf, from_=12, to=-12, resolution=0.5, orient=tk.HORIZONTAL,
                    length=0, width=12, sliderrelief=tk.FLAT, bd=0, font=('Helvetica Neue', 5),
                    command=lambda _, idx=i: self._scb(idx))
                sl.set(0); sl.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=2); self._all_sls.append(sl)
                vl = tk.Label(bf, text="0.0", font=('Helvetica Neue', 7), width=4)
                vl.pack(side=tk.LEFT); self._all_vls.append(vl)
        self._fig2 = Figure(figsize=(3,2.5), dpi=70)
        self._ax2 = self._fig2.add_subplot(111)
        self._ax2.set_ylim([-1,1])
        self._canvas2 = FigureCanvasTkAgg(self._fig2, master=mf)
        self._canvas2.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._canvas2.draw()

    def _eq_compact(self):
        ef = tk.Frame(self, relief=tk.FLAT)
        ef.pack(fill=tk.BOTH, padx=10, pady=(2,0), expand=True)
        self._eq_frame = ef
        tk.Label(ef, text="均衡器 · 紧凑型", font=('Helvetica Neue', 12, 'bold')).pack(anchor=tk.W, padx=15, pady=(6,2))
        for ri in range(2):
            rf = tk.Frame(ef)
            rf.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,1))
            for ci in range(5):
                i = ri*5+ci
                bf = tk.Frame(rf)
                bf.pack(side=tk.LEFT, fill=tk.BOTH, padx=2, expand=True)
                vl = tk.Label(bf, text="0.0", font=('Helvetica Neue', 7))
                vl.pack(pady=(0,0)); self._all_vls.append(vl)
                sl = tk.Scale(bf, from_=12, to=-12, resolution=1, length=50, width=10,
                    sliderrelief=tk.FLAT, bd=0, font=('Helvetica Neue', 5),
                    command=lambda _, idx=i: self._scb(idx))
                sl.set(0); sl.pack(fill=tk.BOTH, pady=1, expand=True); self._all_sls.append(sl)
                lbl = tk.Label(bf, text=BAND_LABELS[i], font=('Helvetica Neue', 7, 'bold'))
                lbl.pack(); self._all_blls.append(lbl)
                # 说明文字已移至状态栏显示

    def _build(self):
        self._clear()
        self._build_top()
        tk.Frame(self, height=1, bg='#d2d2d7').pack(fill=tk.X, padx=10)
        lay = self.C.get('lay', 'vert')
        self._build_wave(0.3)
        getattr(self, f'_eq_{lay}')()
        self._build_ctrl()
        # ★ 全屏时波形图自动放大填满剩余空间 ★
        self._build_status()
        self.after(300, self._upd)

    def _apply_theme(self):
        c = self.C
        fn = c.get('fn','Helvetica Neue')
        self.configure(bg=c['bg'])
        # spacer 已移除
        if hasattr(self,'_topf'):
            self._topf.configure(bg=c['card'])
            for ch in self._topf.winfo_children():
                if isinstance(ch, tk.Label):
                    try: ch.configure(bg=c['card'], fg=c['text'] if 'bold' in (ch.cget('font') or '') else c['text2'])
                    except: pass
                elif isinstance(ch, tk.OptionMenu):
                    try: ch.configure(bg=c['card'], fg=c['text'], relief='flat')
                    except: pass
                elif isinstance(ch, tk.Button):
                    try: ch.configure(bg=c['accent'] if '全部' in (ch.cget('text') or '') else c['sbg'],
                                      fg='white' if '全部' in (ch.cget('text') or '') else c['text'],
                                      activebackground=c.get('accent2',c['accent']), relief='flat')
                    except: pass
        if hasattr(self,'_fig'):
            self._fig.set_facecolor(c['card']); self._ax.set_facecolor(c['card'])
            self._ax.tick_params(colors=c['text2'],labelsize=7)
            for s in ['bottom','top','left','right']: self._ax.spines[s].set_visible(False)
            self._canvas.draw_idle()
        if hasattr(self,'_fig2'):
            self._fig2.set_facecolor(c['card']); self._ax2.set_facecolor(c['card'])
            self._ax2.tick_params(colors=c['text2'],labelsize=6)
            for s in ['bottom','top','left','right']: self._ax2.spines[s].set_visible(False)
            self._canvas2.draw_idle()
        if self._eq_frame:
            self._eq_frame.configure(bg=c['card'], highlightbackground=c.get('border',c['card']), highlightthickness=1, relief='flat')
            def apply_to_children(w):
                try:
                    if isinstance(w, tk.Label): w.configure(bg=c['card'], fg=c['text'], font=(fn, max(7, int((w.cget('font') or 'Helvetica Neue 8').split()[-1]) if (w.cget('font') or 'Helvetica Neue 8').split()[-1].isdigit() else 8)))
                    elif isinstance(w, tk.Scale): w.configure(bg=c['card'], fg=c['accent'], troughcolor=c['sbg'], sliderrelief='flat')
                    elif isinstance(w, tk.Frame):
                        w.configure(bg=c['card'])
                        for sub in w.winfo_children(): apply_to_children(sub)
                except: pass
            for sub in self._eq_frame.winfo_children(): apply_to_children(sub)
        for sl in self._all_sls:
            try: sl.configure(bg=c['card'], fg=c['accent'], troughcolor=c['sbg'], sliderrelief='flat')
            except: pass
        for vl in self._all_vls:
            try: vl.configure(bg=c['card'], fg=c['accent'], font=(fn, 8))
            except: pass
        if hasattr(self,'_ctf'):
            self._ctf.configure(bg=c['card'])
            self._bt.configure(bg=c['accent'], fg='white', activebackground=c.get('accent2',c['accent']), font=(fn,11,'bold'), relief='flat')
            self._rst.configure(bg=c['sbg'], fg=c['text'], activebackground=c.get('hover',c['card']), font=(fn,10), relief='flat')
            for ch in self._ctf.winfo_children():
                if isinstance(ch, tk.Button) and ch not in (self._bt, self._rst):
                    try: ch.configure(bg=c['sbg'], fg=c['text'], activebackground=c.get('hover',c['card']), font=(fn,9), relief='flat')
                    except: pass
                elif isinstance(ch, tk.Label):
                    try: ch.configure(bg=c['card'], fg=c['text'], font=(fn, 10))
                    except: pass
                elif isinstance(ch, tk.Scale):
                    try: ch.configure(bg=c['card'], fg=c['accent'], troughcolor=c['sbg'], sliderrelief='flat')
                    except: pass
                elif isinstance(ch, tk.Frame) and ch.winfo_width() == 1:
                    try: ch.configure(bg=c.get('border','#d2d2d7'))
                    except: pass
            if hasattr(self,'_bvl'): self._bvl.configure(bg=c['card'], fg=c['accent'], font=(fn,10,'bold'))
        sb = self.winfo_children()[-1] if self.winfo_children() else None
        if sb:
            try:
                sb.configure(bg=c['card'])
                for ch in sb.winfo_children():
                    if isinstance(ch, tk.Label): ch.configure(bg=c['card'], fg=c['text2'], font=(fn,9))
            except: pass
        self._tv.set(self.theme_name)

    def _switch(self, name):
        if name == self.theme_name: return
        self.theme_name = name
        self.C = dict(THEMES[name])
        self._build()
        self._apply_theme()

    def _upd(self):
        if self.eq and self.eq.running:
            try:
                d = self.eq.wf.get_nowait()
                cfg = self.C
                self._ax.clear(); self._ax.set_facecolor(cfg['card'])
                for s in ['bottom','top','left','right']: self._ax.spines[s].set_visible(False)
                self._ax.tick_params(colors=cfg['text2'],labelsize=7); self._ax.set_ylim([-1,1])
                mono = np.mean(d,axis=1) if d.ndim>1 and d.shape[1]>1 else d[:,0]
                self._ax.fill_between(range(len(mono)),mono,0,alpha=cfg['wa'],color=cfg['accent'])
                self._ax.plot(mono,color=cfg['accent'],linewidth=0.8)
                self._ax.axhline(y=0,color=cfg.get('border','#ccc'),linewidth=0.5)
                self._canvas.draw_idle()
                if hasattr(self,'_ax2'):
                    self._ax2.clear(); self._ax2.set_facecolor(cfg['card'])
                    for s in ['bottom','top','left','right']: self._ax2.spines[s].set_visible(False)
                    self._ax2.tick_params(colors=cfg['text2'],labelsize=6); self._ax2.set_ylim([-1,1])
                    self._ax2.fill_between(range(len(mono)),mono,0,alpha=cfg['wa'],color=cfg['accent2'])
                    self._ax2.plot(mono,color=cfg['accent2'],linewidth=0.6)
                    self._canvas2.draw_idle()
            except queue.Empty: pass
        self.after(300, self._upd)

    def _scb(self, i):
        if hasattr(self, '_dig_values') and i < len(self._dig_values):
            v = self._dig_values[i]
        else:
            v = self._all_sls[i].get()
        if i < len(self._all_vls):
            self._all_vls[i].config(text=f"{v:+.1f}")
        self.eq.sg(i, v)
        # 状态栏显示实时反馈
        label = BAND_LABELS[i]
        desc = BAND_DESCS[i] if i < len(BAND_DESCS) else ""
        if v > 0:
            feel = f"↑ {desc}增强"
        elif v < 0:
            feel = f"↓ {desc}减弱"
        else:
            feel = f"• {desc} 平直"
        self._sbl.config(text=f"{label} {feel}  ({v:+.1f}dB)")

    def _adj(self, i, delta):
        """数字式：增减数值"""
        if not hasattr(self, '_dig_values') or i >= len(self._dig_values):
            return
        v = self._dig_values[i] + delta
        v = max(-12, min(12, round(v * 2) / 2))
        self._dig_values[i] = v
        if i < len(self._all_vls):
            self._all_vls[i].config(text=f"{v:+.1f}")
        self.eq.sg(i, v)
        label = BAND_LABELS[i]
        desc = BAND_DESCS[i] if i < len(BAND_DESCS) else ""
        if v > 0: feel = f"↑ {desc}增强"
        elif v < 0: feel = f"↓ {desc}减弱"
        else: feel = f"• {desc} 平直"
        self._sbl.config(text=f"{label} {feel}  ({v:+.1f}dB)")

    def _bcb(self, v):
        iv = int(float(v))
        self._bvl.config(text=f"{iv}%")
        self.eq.sb(iv)
        if iv > 50:
            feel = "🔊 低音强劲"
        elif iv > 20:
            feel = "🔉 低音适中"
        else:
            feel = "🔈 低音轻柔"
        self._sbl.config(text=f"低音: {iv}% — {feel}")

    def _toggle(self):
        if self.eq and self.eq.running:
            self.eq.stop(); self._bt.config(text="▶ 启动")
            self._sbl.config(text="均衡器已停止")
        else:
            try:
                self._sbl.config(text="启动中...")
                self.eq.start()
                self._bt.config(text="⏹ 停止")
                dev_name = sd.query_devices(self.eq.in_dev)['name']
                self._sbl.config(text=f"均衡器运行中 - 输入: {dev_name}")
            except Exception as e:
                messagebox.showerror("错误",str(e))
                self._sbl.config(text=f"失败: {e}")

    def _apply(self, gains, bass):
        for i,v in enumerate(gains):
            if i<len(self._all_sls):
                try: self._all_sls[i].set(v)
                except: pass
            if i<len(self._all_vls):
                self._all_vls[i].config(text=f"{v:+.1f}")
            if hasattr(self, '_dig_values') and i < len(self._dig_values):
                self._dig_values[i] = v
            self.eq.sg(i,v)
        self._bv.set(bass); self._bvl.config(text=f"{bass}%"); self.eq.sb(bass)

    def _reset(self):
        self.eq.reset()
        if hasattr(self, '_dig_values'):
            self._dig_values = [0.0] * 10
        for s in self._all_sls:
            try: s.set(0)
            except: pass
        for vl in self._all_vls:
            try: vl.config(text="0.0")
            except: pass
        self._bv.set(30); self._bvl.config(text="30%")
        self._sbl.config(text="已重置")

    def _close(self):
        self.eq.stop()
        try: self.quit()
        except: pass
        os._exit(0)

if __name__ == '__main__':
    App().mainloop()
