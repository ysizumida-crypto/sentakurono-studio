#!/usr/bin/env python3
"""読み上げ文が、合成器にどう読まれるかを一覧で出す。**納品前に必ず通すこと。**

2026-08-05、祝詞が次のように読まれたまま30本を作って納品していた:

    祓い給え → ハライ・アタエ      清め給え → キヨメアタエ
    幸え給え → コオエタマエ        略拝詞  → リャクハイシト

神事の言葉を誤読したまま出すのは、品質の問題ではなく礼を失する。
音を聞かなくても、ここで文字として確かめられる。**声を変えても直らない**ので、
直し方は原文をかなで書くか、生成器の `kana=` に読みを渡すこと。

  python3 check_reading.py                     # 生成器の全行を出す
  python3 check_reading.py --speaker 13
  python3 check_reading.py --text "祓い給え、清め給え"
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request

VV = 'http://127.0.0.1:50021'
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GEN = f'{REPO}/personal_brand/shorts/september_batch/generator.py'
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

# (読みに出たら疑う, 原文にこれがあるときだけ, 説明)。
# 片側だけで判定すると誤検出する。「こづち」は正しく づち、「しるしと」は正しい(2026-08-05)。
SUSPECT = [
    ('アタエ',     '給え',  '「給え」を「あたえ」と読んでいます'),
    ('コオエ',     '幸え',  '「幸え」を「こおえ」と読んでいます'),
    ('ハイシト',   '略拝詞', '「略拝詞」を「りゃくはいしと」と読んでいます'),
    ('チトセ',     '千年',  '「千年」を「ちとせ」と読んでいます'),
    ('ベエタワラ', '米俵',  '「米俵」を「べえたわら」と読んでいます'),
    ('ズチ',       '槌',    '「槌」を「づち」と読んでいます'),
]


def kana(text, spk, pin=None):
    """実際に合成される読みを返す。生成器が読みを固定している行は、その固定を通す。"""
    if pin:
        u = urllib.parse.urlencode({'text': pin, 'speaker': spk, 'is_kana': 'true'})
        ap = json.loads(op.open(urllib.request.Request(f'{VV}/accent_phrases?{u}', method='POST'),
                                timeout=180).read())
        return ''.join(m['text'] for p in ap for m in p['moras'])
    q = urllib.parse.urlencode({'text': text, 'speaker': spk})
    return json.loads(op.open(urllib.request.Request(f'{VV}/audio_query?{q}', method='POST'),
                              timeout=180).read())['kana']


def lines_from_generator():
    s = open(GEN, encoding='utf-8').read()
    out = []
    for key in ('CHARMS = [', 'PRAYERS = ['):
        b = s[s.index(key):s.index('\n]', s.index(key))]
        for m in re.finditer(r"^\s*\((\d+),'[^']*','([^']*)'", b, re.M):
            out.append((f'縁起物{m.group(1)}', m.group(2), None))
        for m in re.finditer(r"^\s*\('([^']*)','", b, re.M):
            out.append(('祈り', m.group(1), None))
    # 固定ナレーションは (文, 話速, 読みの固定) の3つ組。読みの固定はダブルクオートで書いてある
    pat = r"""^\s*'(\w+)':\s*\('([^']*)',\s*[\d.]+,\s*(None|"[^"]*")"""
    for m in re.finditer(pat, s, re.M):
        pin = None if m.group(3) == 'None' else m.group(3).strip('"')
        out.append((m.group(1), m.group(2), pin))
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--speaker', type=int, default=13)
    ap.add_argument('--text')
    a = ap.parse_args()
    rows = [('指定', a.text, None)] if a.text else lines_from_generator()

    bad = 0
    for name, text, pin in rows:
        k = kana(text, a.speaker, pin)
        hits = [msg for bad_k, src, msg in SUSPECT if bad_k in k and src in text]
        mark = '×' if hits else ' '
        print(f'{mark} [{name}]{"(読み固定)" if pin else ""} {text}\n    {k}')
        for h in hits:
            print(f'    ★ {h}')
            bad += 1
    print(f'\n=== {len(rows)}行 / 疑わしい読み {bad}件 ===')
    print('※この一覧は「知っている誤読」しか見つけません。祝詞・地名・固有名詞は必ず目で読むこと。')
    sys.exit(1 if bad else 0)
