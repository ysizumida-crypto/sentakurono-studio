#!/usr/bin/env python3
"""社長にお渡しする「予約の手順書」を機械で作る。

**手で書き写さないこと。** 2026-08-05、手で作った版で2つ事故が起きた:

1. タイトルに `|` が入っているのに markdown の表で書いたため、30本すべての縁起物名が落ちた
2. 概要欄の音声クレジットを手で写したため、実際とは違う声(青山龍星)のまま3本ぶん残った

どちらも「正本を読まずに書いた」ことが原因なので、この手順書は必ず
生成器(`shorts/september_batch/generator.py`)と `metadata.yml` から組み立てる。

  python3 personal_brand/videos/make_upload_guide.py
  python3 personal_brand/videos/make_upload_guide.py --start 2026-09-05 --days 7
"""
import argparse, datetime as dt, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = f'{REPO}/personal_brand/shorts/september_batch/generator.py'
OUT = f'{REPO}/personal_brand/videos/UPLOAD_GUIDE.md'

# 本編の予約先。A-1 は 2026-08-05 に公開済み。以後は毎週水曜 21:00
LONGFORM = [
    ('a01_why_buying',    '2026-08-05', '公開済み'),
    ('a02_where_to_find', '2026-08-12', None),
    ('a03_reading_deals', '2026-08-19', None),
]
JST_HOUR = 15           # 公開時刻。社長指示で 21:00 から 15:00 へ変更(2026-08-05)
#   時刻は動画に焼き込まれていない(焼き込みは日付だけ)。変えるときはこの定数と
#   下の概要欄の文面の両方を直すこと。片方だけ直すと、説明と実際の配信時刻がずれる。
BATCH = 7               # 一度に予約する本数(1回15分ほど)


def charms():
    """生成器から (日, 縁起物名) を機械的に取り出す。記憶で書くと必ず間違える。"""
    s = open(GEN, encoding='utf-8').read()
    i = s.index('CHARMS = [')
    body = s[i:s.index('\n]', i)]
    out = [(int(d), n) for d, n in re.findall(r"^\s*\((\d+),'([^']+)'", body, re.M)]
    if not out:
        sys.exit('CHARMS を読み取れませんでした。生成器の書式が変わっています')
    return out


def longform(name):
    """metadata.yml から題名と概要欄を取り出す。概要欄は正本なので加工しない。"""
    p = f'{REPO}/personal_brand/videos/{name}/metadata.yml'
    s = open(p, encoding='utf-8').read()
    title = re.search(r'^title:\s*"(.+)"\s*$', s, re.M).group(1)
    blk = re.search(r'^description: \|\n((?:  .*\n|\n)+)', s, re.M).group(1)
    desc = '\n'.join(l[2:] if l.startswith('  ') else l for l in blk.split('\n')).strip()
    return title, desc


def shorts_desc():
    """ショート30本で共通の概要欄。声のクレジットは本編の正本から引き写す。"""
    _, d = longform('a01_why_buying')
    voice = re.search(r'^.*VOICEVOX:.*$', d, re.M).group(0).strip()
    bgm = d[d.index('▼BGM'):].split('\n\n')[0]
    return f'''毎日{JST_HOUR}時、導きの八咫烏くろのんが、あなたの金運を祓い清めます。

祓い給え、清め給え、守り給い、幸え給え。

▼このチャンネルについて
現役サラリーマンの僕が、小さな会社を「買えるまで」を記録するチャンネルです。本編(週1)では、案件の探し方から交渉・契約まで、失敗も含めてすべて公開します。

※開運演出はエンターテインメントです(効果を保証するものではありません)
※{voice}
※環境音: 熊野・那智の滝(チャンネル管理者が現地で録音した実音)

{bgm}

---
Every day at {JST_HOUR}:00 JST, Kuronon — the guiding three-legged sun crow of Japanese myth — purifies your money luck with the fourfold Shinto prayer: purify, cleanse, protect, and bless. Entertainment only. Narration is AI-generated (VOICEVOX: Meimei Himari).

May the sun crow guide your fortune today.'''


def build(start, days):
    L, add = [], lambda *t: L.extend(t)
    end = start + dt.timedelta(days=days - 1)
    add(f'# 予約の手順書({start:%-m/%-d}〜{end:%-m/%-d})', '',
        '**毎日アップする必要はありません。** YouTube の「予約」に入れておけば、',
        f'あとは毎日 {JST_HOUR}:00 に自動で公開されます。社長の作業は週1回・15分だけです。', '',
        '> この手順書は生成器から機械で作っています。手で書き直さないでください',
        '> (手書き版で、30本の縁起物名が全部落ちる事故が起きました)。', '')

    add('## 1本あたりの手順(1〜2分)', '',
        '1. YouTubeアプリ下の **「+」** → **「動画をアップロード」**',
        '2. 動画を選ぶ(縦長・49秒なので自動でショートになります)',
        '3. **タイトル**を貼る(下の一覧から、ファイル名に対応するもの)',
        '4. **説明**を貼る(次の共通文。30本すべて同じ)',
        '5. **「視聴者」→「いいえ、子ども向けではありません」**',
        '6. **AI音声の開示を「はい」**(合成音声のため必須)',
        f'7. **「公開設定」→「スケジュール設定」→ ファイル名の日付の {JST_HOUR}:00**',
        '8. アップロード', '',
        '> **6番が見つからないとき**: 項目名はアプリの版で変わります。',
        '> 「変更/合成コンテンツ」「AI生成」などの語がある項目を「はい」にしてください。', '',
        '> **画面に日付が焼き込まれています。** ファイル名の日付と予約日を必ず合わせてください。', '')

    add('## ショート共通の説明文', '', '```', shorts_desc(), '```', '')

    cs = dict(charms())
    add(f'## ショートの予約表({days}本)', '',
        f'**{BATCH}本ずつ、週に1回**入れてください。1回15分ほどで、1週間ぶん先まで埋まります。', '')
    for i in range(0, days, BATCH):
        grp = range(i + 1, min(i + BATCH, days) + 1)
        d0, d1 = start + dt.timedelta(grp[0] - 1), start + dt.timedelta(grp[-1] - 1)
        add(f'### {d0:%-m/%-d}〜{d1:%-m/%-d}({len(grp)}本)', '')
        for n in grp:
            d = start + dt.timedelta(n - 1)
            add(f'**{d:%-m/%-d} {JST_HOUR}:00 — `kaiun_{d:%m%d}.mp4`**', '',
                '```', f'{d:%-m月%-d日}の金運祈願|{cs[n]}【くろのん】#Shorts', '```', '')

    add('## 本編(横長・週1本)', '',
        'ショートと同じ手順ですが、**サムネイル**を自分で設定します。',
        'サムネイルを使うには `youtube.com/verify` で電話番号の登録が必要です。', '')
    for name, day, note in LONGFORM:
        t, desc = longform(name)
        d = dt.date.fromisoformat(day)
        head = f'### {d:%-m/%-d} {JST_HOUR}:00 — {name}'
        add(f'{head}({note})' if note else head, '')
        if note:
            add(f'{note}のため、作業は不要です。', '')
            continue
        add('**タイトル**', '', '```', t, '```', '', '**説明**', '', '```', desc, '```', '')

    add('## 特別編「さようなら」', '',
        '2分24秒の横長。日付が入っていないので、いつ公開しても大丈夫です。',
        '他が軌道に乗ってから単独で出すのがよいと思います。', '',
        '## よくあるつまずき', '',
        '**縦の動画がショートにならない** — 60秒未満・縦長なら自動です。タイトルに `#Shorts` があるか確認。', '',
        '**予約が選べない** — チャンネル作成直後は使えないことがあります。数時間おいてお試しください。', '',
        '**一度にたくさん上げられない** — 新しいチャンネルには1日の上限があります。'
        f'弾かれたら{BATCH}本で止めて、翌日に続けてください。', '',
        '**サムネイルが設定できない** — `youtube.com/verify` の電話番号登録が済んでいません。', '',
        '**間違えて公開してしまった** — YouTube Studio から「非公開」に戻せます。慌てなくて大丈夫です。', '',
        '**日付を間違えて予約した** — 公開前なら Studio でいつでも直せます。', '')
    return '\n'.join(L)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2026-08-06')
    ap.add_argument('--days', type=int, default=30)
    ap.add_argument('-o', '--out', default=OUT)
    a = ap.parse_args()
    txt = build(dt.date.fromisoformat(a.start), a.days)
    open(a.out, 'w', encoding='utf-8').write(txt + '\n')
    import re as _re
    n = len(_re.findall(r'^\d+月\d+日の金運祈願\|(.+?)【くろのん】#Shorts$', txt, _re.M))
    if n != a.days:
        sys.exit(f'タイトルが {n} 本しか出ていません(期待 {a.days} 本)')
    print(f'{a.out}: ショート {n}本ぶんの予約表 / {len(txt)}文字')
