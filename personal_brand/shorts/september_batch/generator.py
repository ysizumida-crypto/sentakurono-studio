# 9月分 開運祈願ショート 30本量産スクリプト
# 構成(戦略 §6): フック4s → 祓い14s → 縁起物9s → 祈り12s → 締め6s = 45s
# hook/harai/close は全日共通、prayer は4種ローテ、charm のみ日替わり
import json, urllib.request, urllib.parse, os, wave, audioop, subprocess, warnings, sys
warnings.filterwarnings('ignore')
os.environ['NO_PROXY'] = '127.0.0.1'
BASEDIR = '/tmp/claude-0/-home-user-sentakurono-studio/907dc579-de5f-57c5-893f-d6ea2ffa36f8/scratchpad'
WINDUR = 12.0   # 那智の滝ループ(絶対固定版)の長さ
os.chdir(f'{BASEDIR}/kaiun_sep')
AV = '/home/user/sentakurono-studio/personal_brand/videos/avatar/production'
BG = f'{BASEDIR}/mystic/mystic_bg_v3.mp4'
S1 = f'{BASEDIR}/short01'
FPS = 30
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
VV = 'http://127.0.0.1:50021'; SPK = 14

CHARMS = [  # (日, 縁起物名, 読み上げ文, 画面JP, 画面EN)
 (1,'四つ葉のクローバー','きょうの縁起物は、よつばのクローバー。見つかる確率は、いちまんぶんのいち。','四つ葉のクローバー',"The four-leaf clover — one in 10,000."),
 (2,'馬蹄','きょうの縁起物は、ばてい。ユーの字を上に飾ると、幸運がたまると言われます。','馬蹄(ばてい)',"The horseshoe — points up, luck pools in."),
 (3,'てんとう虫','きょうの縁起物は、てんとうむし。幸運をそっと運ぶ、畑の守り神です。','てんとう虫',"The ladybug — a tiny guardian of luck."),
 (4,'招き猫','きょうの縁起物は、まねきねこ。右手は、金運をまねくと言われます。','招き猫',"Maneki-neko — the right paw beckons fortune."),
 (5,'五帝銭','きょうの縁起物は、ごていせん。ふるい銭には、まもりの力が宿るのだとか。','五帝銭',"Five Emperor coins — old coins, old protection."),
 (6,'ダーラナホース','きょうの縁起物は、ダーラナホース。スウェーデンの、赤い木彫りの馬です。','ダーラナホース',"The Dala horse — Sweden's little red charm."),
 (7,'ハムサ','きょうの縁起物は、ハムサ。手のひらの護符が、わざわいをはねかえします。','ハムサ',"The hamsa — the palm that turns harm away."),
 (8,'ナザール・ボンジュウ','きょうの縁起物は、ナザール・ボンジュウ。青い目が、悪意から目を守ります。','ナザール・ボンジュウ',"The nazar — the blue eye that watches over you."),
 (9,'だるま','きょうの縁起物は、だるま。ななころび、やおき。','だるま',"The daruma — fall seven times, rise eight."),
 (10,'鯉','きょうの縁起物は、こい。滝をのぼって、龍になると言われます。','鯉(こい)',"The koi — the carp that climbs waterfalls."),
 (11,'折り鶴','きょうの縁起物は、おりづる。千年の祈りを、一羽にたたみます。','折り鶴',"The paper crane — a thousand years in one fold."),
 (12,'亀','きょうの縁起物は、かめ。まんねんの、ながい繁栄のしるしです。','亀(かめ)',"The turtle — ten thousand years of steady luck."),
 (13,'富士山','きょうの縁起物は、ふじさん。いちばん高いところから、運がくだります。','富士山',"Mt. Fuji — fortune flows from the summit."),
 (14,'打ち出の小槌','きょうの縁起物は、うちでのこづち。ふれば願いがかなう、伝説の槌です。','打ち出の小槌',"The magic mallet — one swing, one wish."),
 (15,'恵比寿様','きょうの縁起物は、えびすさま。商いの神さまが、ほほえんでいます。','恵比寿様',"Ebisu — the smiling god of commerce."),
 (16,'大黒天','きょうの縁起物は、だいこくてん。米俵の上の、豊かさの神さまです。','大黒天',"Daikokuten — abundance upon rice bales."),
 (17,'フクロウ','きょうの縁起物は、ふくろう。ふくろうは、不苦労。くろうを遠ざけます。','フクロウ',"The owl — fukurou, a life without hardship."),
 (18,'白蛇','きょうの縁起物は、しろへび。弁天さまの使いで、金運の象徴です。','白蛇(しろへび)',"The white snake — herald of wealth."),
 (19,'狛犬','きょうの縁起物は、こまいぬ。一対で、わるいものをとおしません。','狛犬(こまいぬ)',"Komainu — the guardian pair at the gate."),
 (20,'鳥居','きょうの縁起物は、とりい。ここから先は、神さまの領域です。','鳥居',"The torii — where the sacred begins."),
 (21,'絵馬','きょうの縁起物は、えま。願いを書けば、馬がとどけてくれます。','絵馬(えま)',"The ema — wishes carried on wooden horses."),
 (22,'お守り','きょうの縁起物は、おまもり。ちいさな袋に、大きな祈り。','お守り',"The omamori — a big prayer in a small pouch."),
 (23,'熊手','きょうの縁起物は、くまで。福を、かきあつめます。','熊手(くまで)',"The kumade — the rake that gathers fortune."),
 (24,'水引','きょうの縁起物は、みずひき。結び目が、ご縁をつなぎます。','水引(みずひき)',"Mizuhiki — knots that tie good bonds."),
 (25,'金魚','きょうの縁起物は、きんぎょ。金の魚は、富のしるしとされてきました。','金魚',"The goldfish — gold in water, wealth at home."),
 (26,'三日月','きょうの縁起物は、みかづき。満ちていく月は、のびていく運です。','三日月',"The waxing moon — luck on the rise."),
 (27,'北極星','きょうの縁起物は、ほっきょくせい。迷ったら、うごかない星を見上げて。','北極星',"The North Star — still, and always guiding."),
 (28,'桜','きょうの縁起物は、さくら。咲くべきときを、知っています。','桜(さくら)',"Sakura — it knows when to bloom."),
 (29,'竹','きょうの縁起物は、たけ。まっすぐ、しなやかに、のびていきます。','竹(たけ)',"Bamboo — straight, supple, unstoppable."),
 (30,'松','きょうの縁起物は、まつ。冬のあいだも、緑をたやしません。','松(まつ)',"The pine — green through every winter."),
]
EMOJI = ['🍀','🐴','🐞','🐱','🪙','🎠','🪬','🧿','🎎','🐟','🕊️','🐢','🗻','🔨','🎣','🌾','🦉','🐍','🦁','⛩️','🪧','🧧','🧹','🎀','🐠','🌙','🌟','🌸','🎋','🌲']
PRAYERS = [  # 4種ローテ (読み上げ, 画面JP, 画面EN)
 ('あなたの金運の扉が、しずかに、ひらきますように。','あなたの<span class="g">金運の扉</span>が、<br>ひらきますように。','May the doors of your fortune<br>quietly open.'),
 ('あなたの努力が、めぐりめぐって、実をむすびますように。','あなたの努力が、<br><span class="g">実をむすびます</span>ように。','May your efforts come back around<br>and bear fruit.'),
 ('あなたのもとに、よいご縁と、よい報せが、とどきますように。','<span class="g">よいご縁</span>と、よい報せが、<br>とどきますように。','May good ties and good news<br>find their way to you.'),
 ('あなたの明日が、きょうより、すこし豊かでありますように。','明日が、きょうより、<br><span class="g">すこし豊か</span>でありますように。','May tomorrow be a little richer<br>than today.'),
]

def synth(text, speed, fn):
    if os.path.exists(fn): return
    q = urllib.parse.urlencode({'text': text, 'speaker': SPK})
    query = json.loads(opener.open(urllib.request.Request(f'{VV}/audio_query?{q}', method='POST'), timeout=300).read())
    query['speedScale'] = speed
    wav = opener.open(urllib.request.Request(f'{VV}/synthesis?speaker={SPK}',
        data=json.dumps(query).encode(), headers={'Content-Type':'application/json'}, method='POST'), timeout=900).read()
    open(fn,'wb').write(wav)

OV_TPL = '''<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0}} html,body{{width:1080px;height:1920px;background:transparent;overflow:hidden}}
.chip{{position:absolute;left:0;width:1080px;top:120px;text-align:center}}
.chip span{{display:inline-block;font-family:"Noto Sans JP";font-weight:900;font-size:36px;letter-spacing:.25em;
 color:#0B0710;background:#F5C542;padding:10px 30px}}
.jp{{position:absolute;left:0;width:1080px;top:260px;text-align:center;
 font-family:"Noto Serif JP",serif;font-weight:900;font-size:{fs}px;line-height:1.5;color:#FBF3E4;
 text-shadow:0 0 34px rgba(245,197,66,.55),0 4px 26px rgba(0,0,0,.85)}}
.jp .g{{color:#F5C542}}
.en{{position:absolute;left:0;width:1080px;top:{entop}px;text-align:center;font-family:"Noto Sans JP";
 font-weight:900;font-size:44px;line-height:1.55;color:#FBF3E4;opacity:.92;
 text-shadow:0 3px 18px rgba(0,0,0,.9)}}
.d{{position:absolute;left:0;width:1080px;bottom:30px;text-align:center;font-family:"Noto Sans JP";
 font-weight:700;font-size:26px;color:#FBF3E4;opacity:.55}}
</style></head><body>
<div class="chip"><span>{chip}</span></div>
<div class="jp">{jp}</div>
<div class="en">{en}</div>
<div class="d">※開運演出はエンターテインメントです / Entertainment only</div>
</body></html>'''

HS = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell'
def render_overlay(fn_html, fn_png, **kw):
    if os.path.exists(fn_png): return
    open(fn_html,'w').write(OV_TPL.format(**kw))
    subprocess.run([HS,'--no-sandbox','--disable-gpu','--hide-scrollbars',
        '--force-device-scale-factor=1','--default-background-color=00000000',
        '--window-size=1080,1920',f'--screenshot={fn_png}',f'file://{os.getcwd()}/{fn_html}'],
        capture_output=True)

KX,KY,KW = 130,1010,820
F = KW/1254
MW,MH = int(130*F),int(122*F)
MX,MY = int(KX+575*F),int(KY+588*F)

def speech_gate(wavfn, voff):
    w = wave.open(wavfn); r=w.getframerate(); sw=w.getsampwidth()
    data = w.readframes(w.getnframes()); w.close()
    hop=int(r*0.03); step=hop*sw
    rms=[audioop.rms(data[o:o+step],sw) for o in range(0,len(data)-step,step)]
    thr=max(rms)*0.06; iv=[]; st=None
    for k,v in enumerate(rms):
        t=k*0.03
        if v>thr and st is None: st=t
        elif v<=thr and st is not None: iv.append([st,t]); st=None
    if st is not None: iv.append([st,len(rms)*0.03])
    merged=[]
    for s,e in iv:
        if merged and s-merged[-1][1]<0.32: merged[-1][1]=e
        else: merged.append([s,e])
    sp=[(s+voff,e+voff) for s,e in merged if e-s>=0.1]
    return ('+'.join(f'between(t,{a:.2f},{b:.2f})' for a,b in sp) or '0'), data, r, sw

def encode_seg(out, ovpng, wavfn, dur, expr, voff, bgoff, fade_in=False, fade_out=False, window=None, woff=0.0):
    if os.path.exists(out): return
    frames=round(dur*FPS); vdur=frames/FPS
    gate,_,_,_ = speech_gate(wavfn, voff)
    bob="6*sin(2*PI*1.4*t)"
    fades=''
    if fade_in: fades+=',fade=t=in:st=0:d=0.5:color=0x0B0710'
    if fade_out: fades+=f',fade=t=out:st={vdur-0.6:.2f}:d=0.6:color=0x0B0710'
    blink = (expr == 'base_transparent')
    EW,EH = int(390*F), int(185*F)
    EX,EY = int(KX+435*F), int(KY+425*F)
    tail = (f"[5:v]crop=390:185:435:425,scale={EW}:{EH}[eyes];"
            f"[v3][eyes]overlay={EX}:y='{EY}+{bob}':enable='lt(mod(t+2.6,3.2),0.14)+lt(mod(t+1.05,5.1),0.12)'[v4];"
            f"[v4][txt]overlay=0:0{fades}[vout]") if blink else f"[v3][txt]overlay=0:0{fades}[vout]"
    wi = 5 + (1 if blink else 0)
    if window:
        whead = (f"[{wi}:v]format=rgba[wj];[{wi+1}:v]format=gray[mk];[wj][mk]alphamerge[win];"
                 f"[0:v][win]overlay=220:236[bgw];")
        src = '[bgw]'
    else:
        whead = ''; src = '[0:v]'
    fc=f"""[1:v]scale={KW}:-1[k];
[2:v]crop=130:122:575:588,scale={MW}:{MH}[mh];
[3:v]crop=130:122:575:588,scale={MW}:{MH}[mo];
[4:v]format=rgba,fade=t=in:st=0.15:d=0.5:alpha=1[txt];
{whead}
{src}[k]overlay={KX}:y='{KY}+{bob}'[v1];
[v1][mh]overlay={MX}:y='{MY}+{bob}':enable='({gate})*(lt(mod(t,0.20),0.05)+gte(mod(t,0.20),0.15))'[v2];
[v2][mo]overlay={MX}:y='{MY}+{bob}':enable='({gate})*between(mod(t,0.20),0.05,0.15)'[v3];
{tail}"""
    fcf=out.replace('.mp4','.fc.txt'); open(fcf,'w').write(fc)
    inputs_extra = ['-loop','1','-i',f'{AV}/kuronon_happy.png'] if blink else []
    if window:
        inputs_extra += ['-ss', f'{woff % WINDUR:.2f}', '-stream_loop','-1','-i', window, '-loop','1','-i', f'{BASEDIR}/nachi/mask.png']
    r=subprocess.run(['ffmpeg','-y','-ss',f'{bgoff:.2f}','-stream_loop','-1','-i',BG,
        '-loop','1','-i',f'{AV}/kuronon_{expr}.png',
        '-loop','1','-i',f'{AV}/kuronon_mouth_half.png',
        '-loop','1','-i',f'{AV}/kuronon_mouth_open.png',
        '-loop','1','-i',ovpng] + inputs_extra + [
        '-filter_complex_script',fcf,'-map','[vout]',
        '-frames:v',str(frames),'-r','30','-c:v','libx264','-preset','superfast','-crf','20',
        '-pix_fmt','yuv420f' if False else 'yuv420p','-an',out],capture_output=True,text=True)
    assert r.returncode==0, r.stderr[-400:]

def audio_chunk(wavfn, voff, dur):
    w=wave.open(wavfn); r=w.getframerate(); sw=w.getsampwidth()
    data=w.readframes(w.getnframes()); w.close()
    ns=int(round(dur*r)); pre=int(round(voff*r))
    chunk=b'\x00'*pre*sw+data
    return chunk[:ns*sw]+b'\x00'*max(0,ns*sw-len(chunk)), r

# ---- 共通セグメント(short01 の資産を再利用) ----
DUR = dict(hook=6.0, harai=16.0, charm=9.0, prayer=12.0, close=6.0)
VOFF = dict(hook=2.4, harai=1.2, charm=0.8, prayer=1.5, close=0.6)
os.makedirs('segs', exist_ok=True)
# 共通カットは瞬き付きで自前エンコード(hook/harai=丸目なので瞬き、close=にこにこ目なので不要)
encode_seg('segs/hook.mp4',  f'{S1}/ov_hook.png',  f'{S1}/hook.wav',  DUR['hook'],  'base_transparent', VOFF['hook'],  0.0, fade_in=True, window=f'{BASEDIR}/nachi/falls_loop.mp4', woff=0.0)
encode_seg('segs/harai.mp4', f'{S1}/ov_harai.png', f'{S1}/harai.wav', DUR['harai'], 'base_transparent', VOFF['harai'], 2.3, window=f'{BASEDIR}/nachi/falls_loop.mp4', woff=6.0)
encode_seg('segs/close.mp4', f'{S1}/ov_close.png', f'{S1}/close.wav', DUR['close'], 'happy',            VOFF['close'], 5.2, fade_out=True, window=f'{BASEDIR}/nachi/falls_loop.mp4', woff=43.0)
# 祈り4種
for pi,(ptext,pjp,pen) in enumerate(PRAYERS):
    synth(ptext, 0.95, f'segs/prayer{pi}.wav')
    render_overlay(f'segs/ov_prayer{pi}.html', f'segs/ov_prayer{pi}.png',
        fs=74, entop=640, chip='今日の金運祈願 — DAILY FORTUNE PRAYER', jp=pjp, en=pen)
    encode_seg(f'segs/prayer{pi}.mp4', f'segs/ov_prayer{pi}.png', f'segs/prayer{pi}.wav',
        DUR['prayer'], 'happy', VOFF['prayer'], (3+pi*1.9)%8, window=f'{BASEDIR}/nachi/falls_loop.mp4', woff=31.0)
    print(f'prayer{pi} ok', flush=True)

# ---- 日替わり縁起物+日次合成 ----
os.makedirs('out', exist_ok=True)
for day,cname,cspoken,cjp,cen in CHARMS:
    tag=f'day{day:02d}'
    synth(cspoken, 1.1, f'segs/charm{day:02d}.wav')
    render_overlay(f'segs/ov_charm{day:02d}.html', f'segs/ov_charm{day:02d}.png',
        fs=(74 if len(cjp)<=8 else 64), entop=640,
        chip=f'9月{day}日の金運祈願 — DAILY FORTUNE PRAYER',
        jp=f'今日の縁起物<br><span class="g">{cjp}</span>',
        en=cen + f'<div style="margin-top:36px;font-size:150px;font-family:\'Noto Color Emoji\'">{EMOJI[day-1]}</div>')
    encode_seg(f'segs/charm{day:02d}.mp4', f'segs/ov_charm{day:02d}.png', f'segs/charm{day:02d}.wav',
        DUR['charm'], 'happy', VOFF['charm'], (day*1.7)%8, window=f'{BASEDIR}/nachi/falls_loop.mp4', woff=22.0)
    pi=(day-1)%4
    final=f'out/kaiun_sep{day:02d}.mp4'
    if not os.path.exists(final):
        # 映像連結
        cc=f'segs/cc{day:02d}.txt'
        open(cc,'w').write('\n'.join([
            "file 'hook.mp4'","file 'harai.mp4'",f"file 'charm{day:02d}.mp4'",
            f"file 'prayer{pi}.mp4'","file 'close.mp4'"]))
        subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',f'cc{day:02d}.txt','-c','copy',f'v{day:02d}.mp4'],
                       check=True,capture_output=True,cwd='segs')
        # 音声組み立て
        parts=[]; rate=None
        for name,wf in [('hook',f'{S1}/hook.wav'),('harai',f'{S1}/harai.wav'),
                        ('charm',f'segs/charm{day:02d}.wav'),('prayer',f'segs/prayer{pi}.wav'),
                        ('close',f'{S1}/close.wav')]:
            c,rate=audio_chunk(wf, VOFF[name], DUR[name]); parts.append(c)
        vw=wave.open(f'segs/voice{day:02d}.wav','wb'); vw.setnchannels(1); vw.setsampwidth(2); vw.setframerate(rate)
        for c in parts: vw.writeframes(c)
        vw.close()
        D=sum(DUR.values())
        subprocess.run(['ffmpeg','-y','-i',f'segs/v{day:02d}.mp4','-i',f'segs/voice{day:02d}.wav',
            '-stream_loop','-1','-i',f'{BASEDIR}/bgm_test.mp3','-i',f'{S1}/sfx49.wav',
            '-i',f'{BASEDIR}/nachi/nachi_amb.wav','-filter_complex',
            f"[2:a]atrim=0:{D},volume=0.15,afade=t=in:st=2.2:d=2.5[bgm];"
            f"[4:a]aloop=loop=-1:size=2200000,atrim=0:{D},volume=0.55,afade=t=in:st=0:d=0.4[amb0];"
            f"[1:a]asplit=3[voice][sc1][sc2];"
            f"[bgm][sc1]sidechaincompress=threshold=0.015:ratio=8:attack=20:release=500[bgmd];"
            f"[amb0][sc2]sidechaincompress=threshold=0.02:ratio=2.5:attack=30:release=600[ambd];"
            f"[3:a]volume=0.9[sfx];"
            f"[voice][bgmd][ambd][sfx]amix=inputs=4:duration=first:normalize=0,afade=t=out:st={D-1.5}:d=1.5[a]",
            '-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','160k','-shortest',final],
            check=True,capture_output=True)
    print(f'{tag} {cname} ok', flush=True)
print('ALL 30 DONE')
