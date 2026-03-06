# AI競馬予想 動画自動生成基盤

MoviePyとAI音声合成を使用した予想動画の自動生成システム（YouTube投稿前の生成基盤）

## 機能

- ✅ グラデーション背景デザイン
- ✅ AIナレーション（OpenAI TTS / gTTS）
- ✅ BGM追加機能
- ✅ 本命・対抗・単穴の自動表示
- ✅ 完全自動化対応

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements-automation.txt
```

### 2. 環境変数の設定

#### OpenAI TTS + AI背景を使用する場合（最高品質）

```bash
export OPENAI_API_KEY="sk-..."
export TTS_ENGINE="openai"
export USE_AI_BACKGROUNDS="true"
```

#### OpenAI TTSのみ使用（グラデーション背景）

```bash
export OPENAI_API_KEY="sk-..."
export TTS_ENGINE="openai"
export USE_AI_BACKGROUNDS="false"
```

#### gTTSを使用する場合（完全無料）

```bash
export TTS_ENGINE="gtts"
export USE_AI_BACKGROUNDS="false"
```

## 使用方法

### 基本的な動画生成

```python
from video_generator import PredictionVideoGenerator

# 予想データ
article_data = {
    'track': '川崎',
    'date': '2026年3月5日',
    'predictions': [
        {
            'race': {
                'raceInfo': {
                    'raceNumber': '1R',
                    'raceName': 'サラ4歳以上',
                    'distance': '1400',
                    'surface': 'ダート',
                    'startTime': '15:00'
                }
            },
            'prediction': {
                'predictions': [
                    {'number': 4, 'name': 'ジーティーラピッド', 'win_probability': 0.35},
                    {'number': 9, 'name': 'イノ', 'win_probability': 0.25},
                    {'number': 6, 'name': 'キタサンブリリアン', 'win_probability': 0.15}
                ]
            }
        }
    ]
}

# gTTSで動画生成
generator = PredictionVideoGenerator(tts_engine='gtts')
video_path = generator.generate_video(article_data, "output.mp4")
```

### OpenAI TTS + AI背景で最高品質動画

```python
# OpenAI TTS + DALL-E背景（最高品質）
generator = PredictionVideoGenerator(
    tts_engine='openai',
    use_ai_backgrounds=True,
    openai_api_key='sk-...'  # または環境変数OPENAI_API_KEY
)
video_path = generator.generate_video(article_data, "output_premium.mp4")
```

### OpenAI TTSのみ（グラデーション背景）

```python
# OpenAI TTS + グラデーション背景
generator = PredictionVideoGenerator(
    tts_engine='openai',
    use_ai_backgrounds=False,
    openai_api_key='sk-...'
)
video_path = generator.generate_video(article_data, "output.mp4")
```

### BGM付き動画生成

```python
generator = PredictionVideoGenerator(tts_engine='openai')
video_path = generator.generate_video(
    article_data,
    output_path="output_with_bgm.mp4",
    bgm_path="bgm/racing_theme.mp3",  # BGMファイルのパス
    enable_narration=True
)
```

### ナレーションなしの動画

```python
video_path = generator.generate_video(
    article_data,
    output_path="silent.mp4",
    enable_narration=False
)
```

## サービス比較

### TTS（音声生成）

| サービス | 品質 | コスト | 特徴 |
|---------|------|--------|------|
| **OpenAI TTS** | ⭐⭐⭐⭐⭐ | $15/100万文字 | 最高品質、自然な日本語、安定性高い |
| **gTTS** | ⭐⭐⭐ | 無料 | 品質は中程度、商用利用OK |

### 背景画像生成

| サービス | 品質 | コスト | キャッシュ効果 |
|---------|------|--------|---------------|
| **DALL-E 3** | ⭐⭐⭐⭐⭐ | $0.040/枚 (1792x1024) | 競馬場ごとにキャッシュで実質$0.12/競馬場（3枚） |
| **グラデーション** | ⭐⭐⭐ | 無料 | - |

### 推奨構成

| 用途 | TTS | 背景 | 月間コスト（30本） |
|-----|-----|------|------------------|
| **最高品質** | OpenAI TTS | DALL-E | 初月 $1.65、2ヶ月目以降 **$0.45** |
| **バランス** | OpenAI TTS | グラデーション | **$0.45** |
| **完全無料** | gTTS | グラデーション | **$0** |

※ DALL-E背景は初回のみ生成、以降はキャッシュ再利用のため実質無料

## 動画構成（3階層フォーマット）

### 1. Shorts（30秒・縦型 1080x1920）
- フック（3秒）: 競馬場 + レース番号
- レース詳細（20秒）: 本命・対抗・単穴
- CTA（7秒）: チャンネル登録誘導

### 2. 通常動画（70-90秒）
- フック（3秒）: 本日の注目レース
- 今日の注目（5秒）: 競馬場 + 日付
- レース紹介（各15秒 × 3レース）: 本命を中心に解説
- CTA（10秒）: 概要欄誘導

### 3. 長編フォーマット（レース数に応じて可変）
- オープニング（10秒）: 全レース予想
- 本日のポイント（30秒）: 注目TOP3
- 各レース（20-25秒 × レース数）: 全レース網羅
- まとめ（30秒）: 詳細予想リンク

**現状:** 3レース版で実装完了（12レース対応は基盤のみ）

## GitHub Actions自動化

### 最高品質版（OpenAI TTS + DALL-E背景）

```yaml
- name: Generate Prediction Video (Premium)
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    TTS_ENGINE: openai
    USE_AI_BACKGROUNDS: true
  run: |
    python src/automation/video_generator.py

- name: Cache AI Backgrounds
  uses: actions/cache@v3
  with:
    path: cache/backgrounds
    key: ai-backgrounds-${{ hashFiles('cache/backgrounds/*.png') }}
    restore-keys: |
      ai-backgrounds-
```

### バランス版（OpenAI TTS + グラデーション）

```yaml
- name: Generate Prediction Video (Balanced)
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    TTS_ENGINE: openai
    USE_AI_BACKGROUNDS: false
  run: |
    python src/automation/video_generator.py
```

### 無料版（gTTS + グラデーション）

```yaml
- name: Generate Prediction Video (Free)
  env:
    TTS_ENGINE: gtts
    USE_AI_BACKGROUNDS: false
  run: |
    python src/automation/video_generator.py
```

## コスト詳細試算

### シナリオ1: 最高品質（OpenAI TTS + DALL-E）

**初回のみ（背景画像生成）:**
- 全10競馬場 × 3種類（opening, race, ending） = 30枚
- 30枚 × $0.040 = **$1.20**（一度きり）

**毎月（音声生成 + 動画生成）:**
- 1レースあたり約100文字
- 10レース動画 = 約1,000文字 = $0.015
- 月30本投稿 = **$0.45/月**

**実質コスト:**
- 初月: $1.20 + $0.45 = $1.65
- 2ヶ月目以降: $0.45/月（背景はキャッシュ再利用）

### シナリオ2: バランス型（OpenAI TTS + グラデーション）

- 月30本投稿 = **$0.45/月**

### シナリオ3: 完全無料（gTTS + グラデーション）

- **$0/月**

## キャッシュシステム

AI背景画像は競馬場ごとにキャッシュされます:

```
cache/backgrounds/
  ├── 川崎_opening.png
  ├── 川崎_race.png
  ├── 川崎_ending.png
  ├── 大井_opening.png
  └── ...
```

- **初回**: DALL-Eで画像生成（約10秒/枚）
- **2回目以降**: キャッシュから即座に読み込み（0秒）
- 同じ競馬場なら何度でも無料で再利用可能

### YouTube自動投稿

```python
from youtube_uploader import upload_video

upload_video(
    video_path="output.mp4",
    title="【AI予想】川崎競馬 2026/3/5",
    description="...",
    tags=["競馬", "AI予想", "川崎競馬"]
)
```

## トラブルシューティング

### フォントエラー

```bash
# Ubuntu/Debian
sudo apt-get install fonts-noto-cjk

# macOS（通常は不要）
# システムフォントが自動検出されます
```

### OpenAI APIエラー

```python
# APIキーを確認
echo $OPENAI_API_KEY

# gTTSにフォールバック
export TTS_ENGINE="gtts"
```

## GitHub Actions 自動化

### 設定方法

#### 1. GitHub Secrets 設定

リポジトリの Settings > Secrets and variables > Actions で以下を設定:

**必須:**
- `API_BASE_URL`: データソースURL（デフォルト: https://keiba-data-shared.netlify.app）

**OpenAI使用時のみ:**
- `OPENAI_API_KEY`: OpenAI APIキー（TTS + DALL-E背景用）

#### 2. ワークフロー実行

**手動実行:**
1. Actions タブを開く
2. "Daily Video Generation Automation" を選択
3. "Run workflow" をクリック
4. パラメータを設定:
   - `target_track`: nankan, ooi, funabashi, urawa など
   - `tts_engine`: gtts (無料) または openai (高品質)
   - `use_ai_backgrounds`: true (AI背景) または false (グラデーション)

**自動実行:**
- 毎日 14:00 JST (05:00 UTC) に自動実行
- 対象競馬場は `nankan` (南関東)

#### 3. 生成結果確認

- Actions タブの実行履歴から Artifacts をダウンロード
- 含まれるファイル:
  - `shorts_YYYYMMDD.mp4` - 30秒縦型動画 (1080x1920)
  - `youtube_YYYYMMDD.mp4` - 70-90秒通常動画 (1920x1080)
  - `full_version_YYYYMMDD.mp4` - 長編動画（レース数に応じて可変）
  - `thumbnail_shorts_YYYYMMDD.png` - Shortsサムネイル
  - `thumbnail_youtube_YYYYMMDD.png` - 通常動画サムネイル
  - `thumbnail_full_YYYYMMDD.png` - 長編動画サムネイル
  - `metadata_YYYYMMDD.json` - タイトル・概要欄・タグ
  - `prediction_data.json` - 入力予想データ
  - `generation_summary.json` - 生成結果サマリー

### コスト最適化

#### 無料版 (gTTS + グラデーション背景)
```yaml
tts_engine: gtts
use_ai_backgrounds: false
```
- **月間コスト: $0**
- 毎日30本投稿しても完全無料

#### バランス版 (OpenAI TTS + グラデーション背景)
```yaml
tts_engine: openai
use_ai_backgrounds: false
```
- **月間コスト: $0.45** (30本投稿時)
- 音声品質が大幅向上

#### 最高品質版 (OpenAI TTS + DALL-E背景)
```yaml
tts_engine: openai
use_ai_backgrounds: true
```
- **初月: $1.65** (背景生成 $1.20 + 音声 $0.45)
- **2ヶ月目以降: $0.45/月** (背景はキャッシュ再利用)

### AI背景キャッシュ

GitHub Actions の cache 機能で背景画像を保存:
- 競馬場ごとに3種類 (opening, race, ending)
- 一度生成すれば永続的に再利用
- キャッシュヒット率 99% 以上

## ローカル実行

### 1. 予想データ取得

```bash
export API_BASE_URL="https://keiba-data-shared.netlify.app"
export TARGET_TRACK="nankan"
python src/automation/fetch_predictions.py
```

### 2. 動画生成

```bash
export TTS_ENGINE="gtts"  # または "openai"
export USE_AI_BACKGROUNDS="false"  # または "true"
export OPENAI_API_KEY="sk-..."  # OpenAI使用時のみ
python src/automation/generate_videos.py
```

### 3. 個別テスト

```python
from youtube_format_generator import YouTubeFormatGenerator

generator = YouTubeFormatGenerator(
    tts_engine='gtts',
    use_ai_backgrounds=False
)

# 3階層動画生成
results = generator.generate_all_formats(
    article_data,
    bgm_path=None,
    generate_metadata=True
)
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
