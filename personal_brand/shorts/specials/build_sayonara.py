# 特別編「さようなら」ショート生成
import json, urllib.request, urllib.parse, os, wave, audioop, subprocess, warnings, math, random, struct
warnings.filterwarnings('ignore')
os.environ['NO_PROXY'] = '127.0.0.1'
BASEDIR = '/tmp/claude-0/-home-user-sentakurono-studio/907dc579-de5f-57c5-893f-d6ea2ffa36f8/scratchpad'
os.makedirs(f'{BASEDIR}/sayonara', exist_ok=True)
os.chdir(f'{BASEDIR}/sayonara')
AV = '/home/user/sentakurono-studio/personal_brand/videos/avatar/production'
BG = f'{BASEDIR}/mystic/mystic_bg_v3.mp4'
WIN = f'{BASEDIR}/nachi/falls_loop.mp4'
MASK = f'{BASEDIR}/nachi/mask.png'
FPS = 30
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
VV = 'http://127.0.0.1:50021'; SPK = 14

CUTS = [
 # (key, 秒, 表情, 声offset, 窓offset, 読み上げ, 画面JP, 画面EN, フォント)
 ('hook', 8.0, 'base_transparent', 1.6, 0.0,
  '世界でいちばん、しずかな別れの言葉が、日本にあります。',
  '世界でいちばん、<br><span class="g">しずかな別れ</span>の言葉。',
  'The quietest farewell in the world.', 76),
 ('world', 16.0, 'base_transparent', 0.8, 8.0,
  '英語のグッバイは、神があなたとともにありますように。中国語のツァイチェンは、またお会いしましょう。フランス語のオルヴォワールも、また会う日まで。世界の別れは、神に祈るか、再会を願うか。そのどちらかでした。',
  '世界の別れは、<br>神に祈るか、再会を願うか。',
  'Goodbye = "God be with you."<br>Au revoir = "until we meet again."', 66),
 ('origin', 12.0, 'base_transparent', 0.8, 24.0,
  'けれど、日本だけが、ちがいました。さようなら。もとのかたちは、左様ならば。そうであるならば、という意味の、ただの接続の言葉です。',
  '<span class="g">さようなら</span><br>= 左様ならば',
  '"Sayonara" = "If it must be so."', 84),
 ('mujo', 15.0, 'happy', 0.8, 36.0,
  '咲いた花は、かならず散る。結ばれたご縁も、いつか別れる。日本人は、終わりを恐れるより、終わりかたの美しさを選びました。すがらず、恨まず、ただ受け入れて、また歩き出す。',
  '恨まず、すがらず、<br>受け入れて、また歩く。',
  'No blame, no clinging —<br>accept, and walk on.', 68),
 ('close', 11.0, 'happy', 0.8, 51.0,
  'それが、この島の、別れかたです。あなたにも、世界にも、しずかな明日が、ありますように。',
  'あなたにも、世界にも、<br><span class="g">しずかな明日</span>がありますように。',
  'May you, and the world,<br>have a quiet tomorrow.', 62),
]
D = sum(c[1] for c in CUTS)

def synth(text, fn, speed=0.95):
    if os.path.exists(fn): return
    q = urllib.parse.urlencode({'text': text, 'speaker': SPK})
    query = json.loads(opener.open(urllib.request.Request(f'{VV}/audio_query?{q}', method='POST'), timeout=300).read())
    query['speedScale'] = speed
    wav = opener.open(urllib.request.Request(f'{VV}/synthesis?speaker={SPK}',
        data=json.dumps(query).encode(), headers={'Content-Type':'application/json'}, method='POST'), timeout=900).read()
    open(fn,'wb').write(wav)

OV = '''<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0}} html,body{{width:1080px;height:1920px;background:transparent;overflow:hidden}}
.chip{{position:absolute;left:0;width:1080px;top:120px;text-align:center}}
.chip span{{display:inline-block;font-family:"Noto Sans JP";font-weight:900;font-size:34px;letter-spacing:.22em;
 color:#0B0710;background:#F5C542;padding:10px 28px}}
.jp{{position:absolute;left:0;width:1080px;top:262px;text-align:center;
 font-family:"Noto Serif JP",serif;font-weight:900;font-size:{fs}px;line-height:1.55;color:#FBF3E4;
 text-shadow:0 0 34px rgba(245,197,66,.55),0 4px 26px rgba(0,0,0,.9)}}
.jp .g{{color:#F5C542}}
.en{{position:absolute;left:0;width:1080px;top:660px;text-align:center;font-family:"Noto Sans JP";
 font-weight:900;font-size:40px;line-height:1.55;color:#FBF3E4;opacity:.93;
 text-shadow:0 3px 18px rgba(0,0,0,.95)}}
.d{{position:absolute;left:0;width:1080px;bottom:30px;text-align:center;font-family:"Noto Sans JP";
 font-weight:700;font-size:26px;color:#FBF3E4;opacity:.55}}
</style></head><body>
<div class="chip"><span>さようなら — THE QUIETEST FAREWELL</span></div>
<div class="jp">{jp}</div>
<div class="en">{en}</div>
<div class="d">音 — 熊野・那智の滝(実録) / Nachi Falls, Kumano</div>
</body></html>'''
HS = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell'

KX,KY,KW = 130,1010,820
F = KW/1254
MW,MH = int(130*F),int(122*F)
MX,MY = int(KX+575*F),int(KY+588*F)
EW,EH = int(390*F), int(185*F)
EX,EY = int(KX+435*F), int(KY+425*F)

# --- 効果音(62秒) ---
if not os.path.exists('sfx.wav'):
    random.seed(11); R=44100; N=int(R*D); buf=[0.0]*N
    def tuner(t0,amp=0.30,freq=4096.0,dur=3.5):
        n0=int(t0*R)
        for i in range(int(dur*R)):
            t=i/R; env=math.exp(-t*1.9)*min(1,t*400)
            v=amp*env*(math.sin(2*math.pi*freq*t)+0.35*math.sin(2*math.pi*(freq+2.4)*t))/1.35
            if n0+i<N: buf[n0+i]+=v
    def suzu(t0,amp=0.20,dur=2.2):
        n0=int(t0*R); parts=[(2780,1.0),(3390,.8),(4230,.9),(5160,.6),(6340,.45),(7480,.3)]
        ph=[random.random()*6.28 for _ in parts]
        for i in range(int(dur*R)):
            t=i/R; env=math.exp(-t*2.6)*min(1,t*300)
            trem=.72+.28*math.sin(2*math.pi*9.5*t+math.sin(t*3)*2)
            v=sum(a*math.sin(2*math.pi*f*t+p) for (f,a),p in zip(parts,ph))
            if n0+i<N: buf[n0+i]+=v*amp*env*trem/3.6
    def om(t0,dur,amp=0.045,freq=136.1):
        n0=int(t0*R)
        for i in range(int(dur*R)):
            t=i/R; env=min(1,t/1.5)*min(1,(dur-t)/2.0)
            if n0+i<N: buf[n0+i]+=amp*env*math.sin(2*math.pi*freq*t)
    tuner(0.4); suzu(24.2); om(36.0, 14.0); suzu(51.2); tuner(57.0, amp=0.22)
    mx=max(abs(v) for v in buf); sc=0.9/mx if mx>0.9 else 1.0
    w=wave.open('sfx.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(R)
    w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,v*sc))*32767)) for v in buf)); w.close()

audio=[]; rate=None; segs=[]
for idx,(key,dur,expr,voff,woff,spoken,jp,en,fs) in enumerate(CUTS):
    wavf=f'{key}.wav'; synth(spoken, wavf)
    w=wave.open(wavf); r=w.getframerate(); sw=w.getsampwidth()
    data=w.readframes(w.getnframes()); w.close(); rate=r
    frames=round(dur*FPS); vdur=frames/FPS
    ns=int(round(vdur*r)); pre=int(round(voff*r))
    chunk=b'\x00'*pre*sw+data
    audio.append(chunk[:ns*sw]+b'\x00'*max(0,ns*sw-len(chunk)))
    hop=int(r*0.03); step=hop*sw
    rms=[audioop.rms(data[o:o+step],sw) for o in range(0,len(data)-step,step)]
    thr=max(rms)*0.06; iv=[]; st=None
    for k,v in enumerate(rms):
        t=k*0.03
        if v>thr and st is None: st=t
        elif v<=thr and st is not None: iv.append([st,t]); st=None
    if st is not None: iv.append([st,len(rms)*0.03])
    mg=[]
    for s,e in iv:
        if mg and s-mg[-1][1]<0.32: mg[-1][1]=e
        else: mg.append([s,e])
    sp=[(s+voff,e+voff) for s,e in mg if e-s>=0.1]
    gate='+'.join(f'between(t,{a:.2f},{b:.2f})' for a,b in sp) or '0'
    ovh=f'ov_{key}.html'; ovp=f'ov_{key}.png'
    open(ovh,'w').write(OV.format(fs=fs, jp=jp, en=en))
    subprocess.run([HS,'--no-sandbox','--disable-gpu','--hide-scrollbars','--force-device-scale-factor=1',
        '--default-background-color=00000000','--window-size=1080,1920',f'--screenshot={ovp}',
        f'file://{os.getcwd()}/{ovh}'], capture_output=True)
    bob="6*sin(2*PI*1.4*t)"
    blink = (expr=='base_transparent')
    fades=''
    if idx==0: fades+=',fade=t=in:st=0:d=0.7:color=0x070510'
    if idx==len(CUTS)-1: fades+=f',fade=t=out:st={vdur-1.0:.2f}:d=1.0:color=0x070510'
    inputs=['-ss',f'{(idx*2.1)%8:.2f}','-stream_loop','-1','-i',BG,
            '-loop','1','-i',f'{AV}/kuronon_{expr}.png',
            '-loop','1','-i',f'{AV}/kuronon_mouth_half.png',
            '-loop','1','-i',f'{AV}/kuronon_mouth_open.png',
            '-loop','1','-i',ovp]
    wi=5
    if blink:
        inputs += ['-loop','1','-i',f'{AV}/kuronon_happy.png']; wi=6
    inputs += ['-ss',f'{woff:.2f}','-stream_loop','-1','-i',WIN,'-loop','1','-i',MASK]
    blink_tail = (f"[5:v]crop=390:185:435:425,scale={EW}:{EH}[eyes];"
                  f"[v3][eyes]overlay={EX}:y='{EY}+{bob}':enable='lt(mod(t+2.6,3.2),0.14)+lt(mod(t+1.05,5.1),0.12)'[v4];"
                  f"[v4][txt]overlay=0:0{fades}[vout]") if blink else f"[v3][txt]overlay=0:0{fades}[vout]"
    fc=f"""[{wi}:v]format=rgba[wj];[{wi+1}:v]format=gray[mk];[wj][mk]alphamerge[win];
[0:v][win]overlay=220:236[bgw];
[1:v]scale={KW}:-1[k];
[2:v]crop=130:122:575:588,scale={MW}:{MH}[mh];
[3:v]crop=130:122:575:588,scale={MW}:{MH}[mo];
[4:v]format=rgba,fade=t=in:st=0.2:d=0.6:alpha=1[txt];
[bgw][k]overlay={KX}:y='{KY}+{bob}'[v1];
[v1][mh]overlay={MX}:y='{MY}+{bob}':enable='({gate})*(lt(mod(t,0.20),0.05)+gte(mod(t,0.20),0.15))'[v2];
[v2][mo]overlay={MX}:y='{MY}+{bob}':enable='({gate})*between(mod(t,0.20),0.05,0.15)'[v3];
{blink_tail}"""
    open(f'fc_{key}.txt','w').write(fc)
    r2=subprocess.run(['ffmpeg','-y']+inputs+['-filter_complex_script',f'fc_{key}.txt','-map','[vout]',
        '-frames:v',str(frames),'-r','30','-c:v','libx264','-preset','superfast','-crf','20',
        '-pix_fmt','yuv420p','-an',f'seg_{key}.mp4'], capture_output=True, text=True)
    assert r2.returncode==0, r2.stderr[-500:]
    segs.append(f'seg_{key}.mp4'); print(key,'ok',flush=True)

vw=wave.open('voice.wav','wb'); vw.setnchannels(1); vw.setsampwidth(2); vw.setframerate(rate)
for c in audio: vw.writeframes(c)
vw.close()
open('cc.txt','w').write('\n'.join(f"file '{s}'" for s in segs))
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i','cc.txt','-c','copy','v.mp4'],check=True,capture_output=True)
subprocess.run(['ffmpeg','-y','-i','v.mp4','-i','voice.wav','-stream_loop','-1','-i',f'{BASEDIR}/bgm_test.mp3',
  '-i','sfx.wav','-i',f'{BASEDIR}/nachi/nachi_amb45.wav','-filter_complex',
  f"[2:a]atrim=0:{D},volume=0.15,afade=t=in:st=2.2:d=2.5[bgm];"
  f"[4:a]aloop=loop=-1:size=2200000,atrim=0:{D},volume=0.34,afade=t=in:st=0:d=0.4[amb0];"
  f"[1:a]asplit=3[voice][sc1][sc2];"
  f"[bgm][sc1]sidechaincompress=threshold=0.015:ratio=8:attack=20:release=500[bgmd];"
  f"[amb0][sc2]sidechaincompress=threshold=0.02:ratio=2.5:attack=30:release=600[ambd];"
  f"[3:a]volume=0.9[sfx];"
  f"[voice][bgmd][ambd][sfx]amix=inputs=4:duration=first:normalize=0,afade=t=out:st={D-2.0}:d=2.0[a]",
  '-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','160k','-shortest','sayonara_short.mp4'],
  check=True, capture_output=True)
print('DONE', D, 'sec')
