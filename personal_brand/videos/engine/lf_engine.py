# 本編(1920x1080)生成エンジン v4 — 窓・瞬き・鈴・滝音・口パク対応
import json, urllib.request, urllib.parse, os, wave, audioop, subprocess, warnings, math, random, struct, re
warnings.filterwarnings('ignore')
os.environ['NO_PROXY'] = '127.0.0.1'
BASEDIR = '/tmp/claude-0/-home-user-sentakurono-studio/907dc579-de5f-57c5-893f-d6ea2ffa36f8/scratchpad'
AV = '/home/user/sentakurono-studio/personal_brand/videos/avatar/production'
BG = {'a': f'{BASEDIR}/mystic/mystic_bg_loop.mp4',
      'b': f'{BASEDIR}/mystic/mystic_bg_b.mp4',
      'c': f'{BASEDIR}/mystic/mystic_bg_c.mp4'}
WIN = f'{BASEDIR}/nachi/falls_loop.mp4'
MASK = f'{BASEDIR}/nachi/mask.png'
HS = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell'
FPS = 30
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
VV = 'http://127.0.0.1:50021'; SPK = 14

KX,KY,KW = 1220,510,640
F = KW/1254
MW,MH = int(130*F),int(122*F)
MX,MY = int(KX+575*F),int(KY+588*F)
EW,EH = int(390*F),int(185*F)
EX,EY = int(KX+435*F),int(KY+425*F)
# 窓(横型): 蝕の位置は a/c=中央(50%,46%)・b=右上(72%,30%)。文字と干渉しない a/c のみ使用
WOX,WOY = 960-320, 497-340

def synth(text, fn, speed=1.15, pause=None, vol=None):
    if os.path.exists(fn): return
    q = urllib.parse.urlencode({'text': text, 'speaker': SPK})
    query = json.loads(opener.open(urllib.request.Request(f'{VV}/audio_query?{q}', method='POST'), timeout=300).read())
    query['speedScale'] = speed
    if pause is not None and 'pauseLengthScale' in query: query['pauseLengthScale'] = pause
    if vol is not None: query['volumeScale'] = vol
    wav = opener.open(urllib.request.Request(f'{VV}/synthesis?speaker={SPK}',
        data=json.dumps(query).encode(), headers={'Content-Type':'application/json'}, method='POST'), timeout=1800).read()
    open(fn,'wb').write(wav)

def clean(t):
    t = t.replace('**','').strip()
    return re.sub(r'([一-龯々]+)\(([ぁ-ん]+)\)', r'\2', t)

def analyze(path):
    w=wave.open(path); rate=w.getframerate(); sw=w.getsampwidth()
    data=w.readframes(w.getnframes()); w.close()
    dur=len(data)/(rate*sw)
    hop=int(rate*0.03); step=hop*sw
    rms=[audioop.rms(data[o:o+step],sw) for o in range(0,len(data)-step,step)]
    thr=max(rms)*0.06; iv=[]; st=None
    for i,v in enumerate(rms):
        t=i*0.03
        if v>thr and st is None: st=t
        elif v<=thr and st is not None: iv.append([st,t]); st=None
    if st is not None: iv.append([st,len(rms)*0.03])
    merged=[]
    for s,e in iv:
        if merged and s-merged[-1][1]<0.32: merged[-1][1]=e
        else: merged.append([s,e])
    speech=[(s,e) for s,e in merged if e-s>=0.12]
    gaps=[(a[1]+b[0])/2 for a,b in zip(speech,speech[1:])]
    return data,rate,sw,dur,speech,gaps

OV_TPL = '''<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0}} html,body{{width:1920px;height:1080px;background:transparent;overflow:hidden}}
.h{{position:absolute;left:70px;top:56px;font-family:"Noto Sans JP";font-weight:900;font-size:30px;
 letter-spacing:.12em;color:#0B0710;background:#F5C542;padding:8px 22px;opacity:.92}}
.t{{position:absolute;left:0;width:1920px;top:{top}px;text-align:center;
 font-family:"Noto Serif JP",serif;font-weight:900;font-size:{fs}px;line-height:1.5;color:#FBF3E4;
 text-shadow:0 0 30px rgba(245,197,66,.5),0 4px 24px rgba(0,0,0,.8);letter-spacing:.02em}}
.t .g{{color:#F5C542}}
.d{{position:absolute;left:0;width:1920px;bottom:34px;text-align:center;font-family:"Noto Sans JP";
 font-weight:700;font-size:27px;color:#FBF3E4;opacity:.6}}
</style></head><body>
<div class="h">{header}</div>
<div class="t">{main}</div>{telop}
</body></html>'''

def render_overlay(path_png, header, main, telop, fs, top):
    if os.path.exists(path_png): return
    t = f'<div class="d">{telop}</div>' if telop else ''
    html = OV_TPL.format(header=header, main=main, telop=t, fs=fs, top=top)
    hp = path_png.replace('.png','.html')
    open(hp,'w').write(html)
    subprocess.run([HS,'--no-sandbox','--disable-gpu','--hide-scrollbars','--force-device-scale-factor=1',
        '--default-background-color=00000000','--window-size=1920,1080',f'--screenshot={path_png}',
        f'file://{os.path.abspath(hp)}'], capture_output=True)

def encode_cut(out, bgkey, ovpng, expr, gate, frames, vdur, bgoff, fade_in, fade_out, window, woff):
    if os.path.exists(out): return
    bob = "7*sin(2*PI*1.5*t)"
    fades = ''
    if fade_in: fades += ',fade=t=in:st=0:d=0.45:color=0x0B0710'
    if fade_out: fades += f',fade=t=out:st={vdur-0.45:.2f}:d=0.45:color=0x0B0710'
    blink = expr in ('base_transparent','serious','troubled','surprised')
    n = 5
    inputs = ['-ss',f'{bgoff:.2f}','-stream_loop','-1','-i',BG[bgkey]]
    if expr:
        inputs += ['-loop','1','-i',f'{AV}/kuronon_{expr}.png',
                   '-loop','1','-i',f'{AV}/kuronon_mouth_half.png',
                   '-loop','1','-i',f'{AV}/kuronon_mouth_open.png',
                   '-loop','1','-i',ovpng]
        if blink:
            inputs += ['-loop','1','-i',f'{AV}/kuronon_happy.png']; n = 6
        wi = n
        if window:
            inputs += ['-ss',f'{woff:.2f}','-stream_loop','-1','-i',WIN,'-loop','1','-i',MASK]
        whead = (f"[{wi}:v]format=rgba[wj];[{wi+1}:v]format=gray[mk];[wj][mk]alphamerge[win];"
                 f"[0:v][win]overlay={WOX}:{WOY}[bgw];") if window else ''
        src = '[bgw]' if window else '[0:v]'
        blink_tail = (f"[5:v]crop=390:185:435:425,scale={EW}:{EH}[eyes];"
                      f"[v3][eyes]overlay={EX}:y='{EY}+{bob}':enable='lt(mod(t+2.6,3.2),0.14)+lt(mod(t+1.05,5.1),0.12)'[v4];"
                      f"[v4][txt]overlay=0:0{fades}[vout]") if blink else f"[v3][txt]overlay=0:0{fades}[vout]"
        fc = f"""{whead}
[1:v]scale={KW}:-1[k];
[2:v]crop=130:122:575:588,scale={MW}:{MH}[mh];
[3:v]crop=130:122:575:588,scale={MW}:{MH}[mo];
[4:v]format=rgba[txt];
{src}[k]overlay={KX}:y='{KY}+{bob}'[v1];
[v1][mh]overlay={MX}:y='{MY}+{bob}':enable='({gate})*(lt(mod(t,0.20),0.05)+gte(mod(t,0.20),0.15))'[v2];
[v2][mo]overlay={MX}:y='{MY}+{bob}':enable='({gate})*between(mod(t,0.20),0.05,0.15)'[v3];
{blink_tail}"""
    else:
        inputs += ['-loop','1','-i',ovpng]
        wi = 2
        if window:
            inputs += ['-ss',f'{woff:.2f}','-stream_loop','-1','-i',WIN,'-loop','1','-i',MASK]
        whead = (f"[{wi}:v]format=rgba[wj];[{wi+1}:v]format=gray[mk];[wj][mk]alphamerge[win];"
                 f"[0:v][win]overlay={WOX}:{WOY}[bgw];") if window else ''
        src = '[bgw]' if window else '[0:v]'
        fc = f"{whead}[1:v]format=rgba[txt];{src}[txt]overlay=0:0{fades}[vout]"
    fcf = out.replace('.mp4','.fc.txt'); open(fcf,'w').write(fc)
    r = subprocess.run(['ffmpeg','-y']+inputs+['-filter_complex_script',fcf,'-map','[vout]',
        '-frames:v',str(frames),'-r','30','-c:v','libx264','-preset','superfast','-crf','20',
        '-pix_fmt','yuv420p','-an',out], capture_output=True, text=True)
    assert r.returncode==0, r.stderr[-500:]

def build(ep, header, script_path, section_texts, SPEC, workdir, out_name, sfx_marks=None):
    """SPEC: {sec:[(marker,bg,layout,expr,main,telop,window),...]} layout: main/huge"""
    os.makedirs(workdir, exist_ok=True)
    os.makedirs(f'{workdir}/segs', exist_ok=True)
    os.chdir(workdir)
    audio_parts=[]; seg_files=[]; rate=None; g=0; sec_starts={}; tcum=0.0
    for sec in sorted(SPEC.keys()):
        wavf=f'segs/sec{sec:02d}.wav'
        synth(section_texts[sec], wavf)
        data,rate,sw,dur,speech,gaps = analyze(wavf)
        text = section_texts[sec]
        subs = SPEC[sec]
        bounds=[0.0]
        for m in subs[1:]:
            off = text.find(m[0]) if m[0] else -1
            tgt = dur*off/len(text) if off>=0 else dur*0.5
            cand=[x for x in gaps if abs(x-tgt)<2.2]
            b=min(cand,key=lambda x:abs(x-tgt)) if cand else tgt
            bounds.append(max(b,bounds[-1]+2.5))
        bounds.append(dur)
        sec_starts[sec]=tcum
        for j,(marker,bgk,layout,expr,main,telop,window) in enumerate(subs):
            cs,ce=bounds[j],bounds[j+1]
            seg=ce-cs+(0.55 if j==len(subs)-1 else 0)
            frames=max(1,round(seg*FPS)); vdur=frames/FPS
            sp=[(max(0,s-cs),min(vdur,e-cs)) for s,e in speech if e>cs and s<ce+0.01]
            sp=[(s,e) for s,e in sp if e-s>0.05]
            gate='+'.join(f'between(t,{a:.2f},{b:.2f})' for a,b in sp) or '0'
            fs,top = (150,400) if layout=='huge' else (96,150)
            ovp=f'segs/ov{g:03d}.png'
            render_overlay(ovp, header, main, telop, fs, top)
            outp=f'segs/c{g:03d}.mp4'
            encode_cut(outp, bgk, ovp, expr, gate, frames, vdur, (g*1.7)%8,
                       j==0 and sec==min(SPEC.keys()), j==len(subs)-1 and sec==max(SPEC.keys()),
                       window, (tcum+cs)%18.2)
            seg_files.append(outp)
            ns=int(round(vdur*rate)); s0=int(round(cs*rate))
            chunk=data[s0*sw:(s0+ns)*sw]; chunk+=b'\x00'*(ns*sw-len(chunk))
            audio_parts.append(chunk); g+=1
            print(f'{ep} s{sec}c{j} ok', flush=True)
        tcum += dur + 0.55
    total = tcum
    vw=wave.open('voice_full.wav','wb'); vw.setnchannels(1); vw.setsampwidth(2); vw.setframerate(rate)
    for c in audio_parts: vw.writeframes(c)
    vw.close()
    open('vcc.txt','w').write('\n'.join(f"file '{f}'" for f in seg_files))
    subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i','vcc.txt','-c','copy','video_silent.mp4'],
                   check=True, capture_output=True)
    # 効果音(開始チューナー・チャーム節の鈴・終了チューナー)
    random.seed(5); R=44100; N=int(R*total); buf=[0.0]*N
    def tuner(t0,amp=0.28):
        n0=int(t0*R)
        for i in range(int(3.5*R)):
            t=i/R; env=math.exp(-t*1.9)*min(1,t*400)
            v=amp*env*(math.sin(2*math.pi*4096*t)+0.35*math.sin(2*math.pi*4098.4*t))/1.35
            if n0+i<N: buf[n0+i]+=v
    def suzu(t0,amp=0.18):
        n0=int(t0*R); parts=[(2780,1.0),(3390,.8),(4230,.9),(5160,.6),(6340,.45),(7480,.3)]
        ph=[random.random()*6.28 for _ in parts]
        for i in range(int(2.2*R)):
            t=i/R; env=math.exp(-t*2.6)*min(1,t*300)
            trem=.72+.28*math.sin(2*math.pi*9.5*t)
            v=sum(a*math.sin(2*math.pi*f*t+p) for (f,a),p in zip(parts,ph))
            if n0+i<N: buf[n0+i]+=v*amp*env*trem/3.6
    tuner(0.4)
    for m in (sfx_marks or []):
        kind, sec = m
        t0 = sec_starts.get(sec, 0)+0.3
        (suzu if kind=='suzu' else tuner)(t0)
    tuner(max(0,total-6), amp=0.2)
    mx=max(abs(v) for v in buf); sc=0.9/mx if mx>0.9 else 1.0
    w=wave.open('sfx.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(R)
    w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,v*sc))*32767)) for v in buf)); w.close()
    D=total
    subprocess.run(['ffmpeg','-y','-i','video_silent.mp4','-i','voice_full.wav',
        '-stream_loop','-1','-i',f'{BASEDIR}/bgm_test.mp3','-i','sfx.wav',
        '-i',f'{BASEDIR}/nachi/nachi_amb45.wav','-filter_complex',
        f"[2:a]atrim=0:{D},volume=0.15,afade=t=in:st=0:d=2[bgm];"
        f"[4:a]aloop=loop=-1:size=2200000,atrim=0:{D},volume=0.20,afade=t=in:st=0:d=0.5[amb0];"
        f"[1:a]asplit=3[voice][sc1][sc2];"
        f"[bgm][sc1]sidechaincompress=threshold=0.015:ratio=8:attack=20:release=500[bgmd];"
        f"[amb0][sc2]sidechaincompress=threshold=0.02:ratio=2.5:attack=30:release=600[ambd];"
        f"[3:a]volume=0.9[sfx];"
        f"[voice][bgmd][ambd][sfx]amix=inputs=4:duration=first:normalize=0,afade=t=out:st={D-4}:d=4[a]",
        '-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','160k','-shortest',out_name],
        check=True, capture_output=True)
    print(f'{ep} DONE {total/60:.1f} min', flush=True)
    return total
