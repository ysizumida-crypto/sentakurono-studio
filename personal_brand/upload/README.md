# YouTube アップロードパイプライン

ぷろたん個人ブランド動画の YouTube Shorts 投稿フロー。**手動 → 半自動 → 完全自動**の3段階を用意。

---

## 前提: YouTube チャンネル開設(まだなら最初だけ)

1. https://www.youtube.com/ にぷろたん個人 Googleアカウントでログイン
2. 右上アイコン → **チャンネルを作成**
3. チャンネル名: 帝国不動産・スマートクレジットの社名は出さない方針(例: 「ぷろたんの石庭」「岩として在る夜」等)
4. プロフィール画像・バナー: Adobe Firefly or DALL-E で和風モチーフ生成
5. アカウント確認(電話番号認証): 15分以上の動画アップに必要(Shortsだけなら不要だが先にやっておく)

---

## 段階1: 手動アップロード(初回〜数本はこれで十分)

**所要時間**: 1本あたり5分

1. **YouTube Studio** (https://studio.youtube.com/) にアクセス
2. 右上 **作成 → 動画をアップロード**
3. `personal_brand/videos/001_iwanagahime_short/final.mp4` をドラッグ&ドロップ
4. **詳細**:
   - タイトル: `動けない夜に、石長姫を思う #Shorts`(タイトルに `#Shorts` を入れると Shorts判定が確実)
   - 説明: `metadata.yml` の description をコピペ
   - タグ: `metadata.yml` の tags をコピペ
   - サムネイル: Shorts は自動生成のまま OK(自前なら別途アップ)
   - 再生リスト: 「石長姫シリーズ」等を作って追加
5. **動画の要素**: 終了画面・カードは Shorts では使えないのでスキップ
6. **チェック**: 自動チェック完了を待つ(著作権スキャン)
7. **公開設定**:
   - **プライバシー**: 非公開 / 限定公開 / 公開
   - **スケジュール設定**: 平日21:00公開 など指定
8. **公開** ボタン or **スケジュール** ボタン

**Shorts として認識される条件**:
- 縦動画(9:16)、60秒以下、解像度 ≧ 1080×1920
- タイトル or 説明に `#Shorts` を含める(推奨・必須ではない)

---

## 段階2: 半自動(YouTube Studio の予約公開機能)

撮りためた複数本を**夜に一気にアップ → 平日朝・夜にスケジュール公開**するだけ。

**運用例**:
- 日曜夜: 翌週分の動画3本まとめて Studio にアップ → 月・水・金 21:00 公開予約
- 平日: 何もしない(自動公開)
- ぷろたんの本業時間ゼロ侵食

これで実用上ほぼ困らない。**まずは段階2で3〜5本回してから段階3を検討**するのが規律的に正しい。

---

## 段階3: 完全自動アップロード(YouTube Data API v3)

撮影済み動画とメタデータYAMLを `python upload_to_youtube.py <dir>` 一発で投稿。

### 初回セットアップ(30分・1回限り)

#### A. Google Cloud プロジェクト作成

1. https://console.cloud.google.com/ にぷろたん個人 Googleアカウントでログイン
2. **新しいプロジェクト** → 名前: `pro-tan-personal-brand`
3. 左メニュー **APIとサービス → ライブラリ → "YouTube Data API v3" → 有効にする**

#### B. OAuth 2.0 認証情報作成

1. **APIとサービス → 認証情報 → 認証情報を作成 → OAuth クライアント ID**
2. **同意画面の設定**(初回のみ):
   - User Type: **外部**
   - アプリ名: `pro-tan-uploader`
   - サポートメール: ぷろたん個人 Gmail
   - スコープ: `youtube.upload` を追加
   - **テストユーザー**: ぷろたん個人 Gmail を追加
3. **OAuth クライアントID 作成**:
   - アプリケーションの種類: **デスクトップアプリ**
   - 名前: `pro-tan-uploader-desktop`
4. **JSON をダウンロード** → `personal_brand/upload/client_secrets.json` に配置
   - **重要**: このファイルは絶対に Git にコミットしない(.gitignore済)

#### C. Python 環境構築

```bash
cd personal_brand/upload
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### D. 初回認証

```bash
python upload_to_youtube.py ../videos/001_iwanagahime_short
```

- ブラウザが自動で開く → ぷろたんの Google アカウントでログイン → 権限を許可
- `token.json` が自動生成される(以降のアップロードはこれで自動認証)

### 2回目以降の運用(1コマンド)

```bash
# 動画ディレクトリに final.mp4 と metadata.yml を置いて、
python upload_to_youtube.py ../videos/002_xxx_short

# → アップロード進捗が出て、最後に https://youtu.be/<videoId> が表示される
```

### メタデータYAMLの書き方

`personal_brand/videos/<dir>/metadata.yml`:

```yaml
title: "動けない夜に、石長姫を思う #Shorts"
description: |
  動けない夜が、ある。
  そんな夜、古事記の石長姫を思い出してほしい。
  派手な花が散っても、岩は残る。
  誰にも見られない一日が、孫の代に届く。
  明日また、机の前に座ろう。それで、十分だ。

  #古事記 #石長姫 #継続は力なり

tags:
  - 古事記
  - 石長姫
  - エッセイ
  - モチベーション
  - 動けない夜
  - 継続
  - Shorts

category_id: "22"   # People & Blogs(エッセイ系の標準)
language: ja
privacy: private    # private / unlisted / public

# 予約公開する場合(ISO 8601形式・JST→UTCに変換)
# scheduled_at: "2026-05-10T12:00:00Z"   # = JST 21:00
```

### API 制限と運用

- **無料枠**: 1日 10,000ユニット、動画アップ1本 = 1,600ユニット → **最大6本/日**
- 週1〜3本ペースのぷろたん運用なら**完全に無料枠内**
- 通信途中で失敗しても resumable upload なので自動リトライ可能

---

## 段階4: マルチプラットフォーム自動配信(YouTube + X + LinkedIn + Instagram + TikTok)

**所要時間**: 初回セットアップ60分・運用後は0分(完全自動)

### アーキテクチャ

```
[git push] or [10分ごとの cron]
   ↓
[GitHub Actions: personal_brand_publish.yml]
   ↓
[scheduler.py が videos/posts を走査]
   ↓
[scheduled_at <= 現在 かつ status==pending のエントリを抽出]
   ↓
[platforms/ 配下の各モジュールが並行アップロード]
   ↓ (成功時)
[metadata.yml の status を uploaded:<url> に更新 → 自動コミット]
```

### 必要な作業(ぷろたん側)

ローカルでの作業は不要。**GitHub の Settings → Secrets and variables → Actions** に下記を登録するだけ。

| Secret 名 | 取得元 | 必須? |
|---|---|---|
| `YOUTUBE_CLIENT_SECRETS_JSON` | Google Cloud Console (Stage 3 で生成済) | YouTube 配信時 |
| `YOUTUBE_REFRESH_TOKEN` | 初回ローカル認証後の `token.json` から抽出 | YouTube 配信時 |
| `X_API_KEY` / `X_API_SECRET` / `X_ACCESS_TOKEN` / `X_ACCESS_SECRET` | https://developer.x.com (Free tier OK) | X 配信時 |
| `LINKEDIN_ACCESS_TOKEN` / `LINKEDIN_PERSON_URN` | https://developer.linkedin.com (Sign In with LinkedIn + Share API) | LinkedIn 配信時 |
| `META_ACCESS_TOKEN` / `META_INSTAGRAM_BUSINESS_ID` | https://developers.facebook.com (Business Account 必須) | Instagram 配信時 |
| `INSTAGRAM_VIDEO_BASE_URL` | 動画を S3/R2/GitHub Releases に置いた公開URL | Instagram 配信時 |
| `TIKTOK_ACCESS_TOKEN` | https://developers.tiktok.com (Content Posting API・要審査) | TikTok 配信時 |

### 配信トリガー

`metadata.yml` に下記を追加すれば、対象媒体すべてに自動配信される:

```yaml
scheduled_at: "2026-05-10T12:00:00Z"   # JST 21:00
platforms:
  - youtube
  - x
  - linkedin
status:
  youtube: pending
  x: pending
  linkedin: pending
```

ぷろたんは **動画ファイル + metadata.yml を push するだけ**。残りは GitHub Actions が処理。

### ローカルテスト

```bash
# Dry-run(実際には投稿しない、対象エントリだけ表示)
python personal_brand/upload/scheduler.py --dry-run

# 本番実行(環境変数が揃っていれば実投稿)
python personal_brand/upload/scheduler.py
```

### 媒体別メモ

- **note**: 公式 API なし。RSS/Webhook 経由の Zapier/IFTTT 連携を Stage 5 で検討
- **Apple/Spotify Podcast**: RSS フィードを Anchor.fm で生成してホスト → そこから自動配信
- **Voicy / stand.fm**: 公式 API なし、手動投稿継続

詳細戦略・ロードマップは `personal_brand/strategy/` 配下を参照。

---

## .gitignore 追加項目(自動追加済)

```
personal_brand/upload/client_secrets.json
personal_brand/upload/token.json
personal_brand/upload/venv/
personal_brand/videos/*/final.mp4
personal_brand/videos/*/*.mp3
personal_brand/videos/*/*.wav
personal_brand/videos/*/*.png
personal_brand/videos/*/*.jpg
```

動画・音声・画像の実体ファイルは Git に入れない(リポジトリ肥大化防止)。スクリプトとメタデータ・台本のみコミット。

---

## 法令・規定の最終チェック(壬生確認指示・公開前必読)

公開ボタンを押す前、以下を確認:

- [ ] 帝国不動産の対外発信規程・取締役の SNS ガイドラインを確認(壬生)
- [ ] 副業届出の必要性(無償発信なら原則不要、収益化開始時に再確認)
- [ ] 動画内・説明欄に社名・案件名・関係者名なし
- [ ] チャンネル名・プロフィールに本業を匂わせる表現なし
- [ ] BGM・画像素材の商用利用ライセンス確認
- [ ] 古事記引用は原典ベース(著作権切れ・問題なし)

**収益化開始時は必ず壬生確認**。広告収益が発生 = 副業扱い → 帝国不動産の副業規程に該当する可能性あり。
