# YouTube API セットアップガイド

YouTube自動投稿を有効化するための完全ガイドです。

## 前提条件

- Googleアカウント
- YouTubeチャンネル（投稿先）
- ローカル開発環境（Mac/Linux/Windows）

## ステップ1: Google Cloud Consoleでプロジェクト作成

### 1.1 プロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 画面上部の「プロジェクトを選択」→「新しいプロジェクト」
3. プロジェクト名: `keiba-ai-youtube`（任意）
4. 「作成」をクリック

### 1.2 YouTube Data API v3 を有効化

1. 左メニュー「APIとサービス」→「ライブラリ」
2. 検索バーで「YouTube Data API v3」を検索
3. 「YouTube Data API v3」を選択
4. 「有効にする」をクリック

## ステップ2: OAuth 2.0 認証情報の作成

### 2.1 同意画面の設定

1. 左メニュー「APIとサービス」→「OAuth同意画面」
2. ユーザータイプ: **外部**（個人利用の場合）
3. 「作成」をクリック

**アプリ情報**
- アプリ名: `keiba-ai-predictor`
- ユーザーサポートメール: 自分のメールアドレス
- デベロッパーの連絡先: 自分のメールアドレス

4. 「保存して次へ」

**スコープ**
- 「スコープを追加または削除」
- `YouTube Data API v3` の `.../auth/youtube.upload` を選択
- 「更新」→「保存して次へ」

**テストユーザー**
- 「ADD USERS」
- 自分のGoogleアカウントを追加
- 「保存して次へ」

5. 「ダッシュボードに戻る」

### 2.2 OAuth クライアントID 作成

1. 左メニュー「APIとサービス」→「認証情報」
2. 「認証情報を作成」→「OAuth クライアントID」
3. アプリケーションの種類: **デスクトップアプリ**
4. 名前: `keiba-ai-youtube-client`（任意）
5. 「作成」

### 2.3 認証情報のダウンロード

1. 作成されたクライアントIDの右側のダウンロードアイコンをクリック
2. JSONファイルがダウンロードされる
3. ファイル名を `youtube_credentials.json` にリネーム
4. プロジェクトの `credentials/` ディレクトリに配置

```bash
mv ~/Downloads/client_secret_*.json credentials/youtube_credentials.json
```

## ステップ3: ローカルで初回認証

### 3.1 依存関係インストール

```bash
pip install -r requirements-automation.txt
```

### 3.2 認証スクリプト実行

```bash
python src/automation/init_youtube_auth.py
```

**実行内容:**
1. ブラウザが自動的に開く
2. Googleアカウントでログイン
3. アプリへのアクセス許可を求められる
4. 「許可」をクリック
5. ブラウザに「認証が完了しました」と表示される

**成功すると:**
```
✅ 認証成功！トークンを保存しました
保存先: credentials/youtube_token.json
```

### 3.3 認証確認

```bash
python src/automation/youtube_uploader.py
```

**期待される出力:**
```
✅ YouTube API認証OK
チャンネル名: あなたのチャンネル名
登録者数: XXX
総再生数: XXX
```

## ステップ4: GitHub Secrets登録

### 4.1 認証情報をコピー

**youtube_credentials.json:**
```bash
cat credentials/youtube_credentials.json | pbcopy  # macOS
# または
cat credentials/youtube_credentials.json  # 手動でコピー
```

**youtube_token.json:**
```bash
cat credentials/youtube_token.json | pbcopy  # macOS
```

### 4.2 GitHubリポジトリに登録

1. GitHubリポジトリページを開く
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret**

**Secret 1:**
- Name: `YOUTUBE_CREDENTIALS_JSON`
- Value: `youtube_credentials.json` の全内容を貼り付け

**Secret 2:**
- Name: `YOUTUBE_TOKEN_JSON`
- Value: `youtube_token.json` の全内容を貼り付け

## ステップ5: テスト動画での疎通確認

### 5.1 5秒テスト動画を作成

```python
# test_video.py
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip

# 5秒の赤い背景
bg = ColorClip(size=(1920, 1080), color=(255, 0, 0), duration=5)

# テキスト
txt = TextClip("TEST", fontsize=100, color='white', size=(1920, 1080))
txt = txt.set_position('center').set_duration(5)

# 合成
video = CompositeVideoClip([bg, txt])
video.write_videofile("output/test.mp4", fps=24)
```

```bash
python test_video.py
```

### 5.2 Private投稿テスト

```bash
# run_daily.py を手動実行（private設定）
export YOUTUBE_PRIVACY=private
export RUN_MODE=test
python src/automation/run_daily.py
```

または直接アップロードテスト:

```python
from src.automation.youtube_uploader import YouTubeUploader

uploader = YouTubeUploader()
url = uploader.upload_video(
    video_path="output/test.mp4",
    title="【テスト】AI競馬予想システム",
    description="これはテスト動画です",
    privacy_status="private"
)
print(f"Uploaded: {url}")
```

### 5.3 YouTubeで確認

1. [YouTube Studio](https://studio.youtube.com/) にアクセス
2. 左メニュー「コンテンツ」
3. アップロードされた動画を確認
4. 公開設定が「非公開」になっていることを確認

## ステップ6: GitHub Actionsでのテスト

### 6.1 手動実行

1. GitHubリポジトリの **Actions** タブ
2. **Daily AI Prediction Automation** を選択
3. **Run workflow** → **Run workflow**

### 6.2 ログ確認

- 各ステップの実行状況を確認
- エラーがある場合はログを確認

### 6.3 Artifacts確認

- 実行完了後、Artifactsセクションから動画ファイルをダウンロード
- 日本語が豆腐になっていないか確認

## トラブルシューティング

### Q1: ブラウザが開かない

**原因:** ローカル環境でポートが使用中

**解決策:**
```bash
# 別のポートを試す
# または手動でURLをブラウザに貼り付け
```

### Q2: 「アプリがGoogleで確認されていません」

**原因:** OAuth同意画面が未公開

**解決策:**
- これは正常です（テストユーザーとして自分を追加済みのため）
- 「詳細」→「keiba-ai-predictor（安全ではないページ）に移動」をクリック

### Q3: GitHub Actionsで認証エラー

**確認事項:**
- Secretsの名前が正確か（大文字小文字区別）
- JSON形式が正しいか（改行なし、整形なし）
- トークンの有効期限

**解決策:**
```bash
# ローカルで再認証
rm credentials/youtube_token.json
python src/automation/init_youtube_auth.py

# 新しいトークンをSecretsに再登録
```

### Q4: 日本語が豆腐になる

**原因:** フォントが正しくインストールされていない

**解決策（Ubuntu/GitHub Actions）:**
```bash
sudo apt-get install fonts-noto-cjk
```

**解決策（macOS）:**
- ヒラギノフォントは標準インストール済み

### Q5: quota exceeded エラー

**原因:** YouTube Data API の無料枠を超過

**制限:**
- 1日あたり10,000ユニット
- 動画アップロード: 1600ユニット/本
- 1日最大6本程度

**解決策:**
- 翌日まで待つ
- Google Cloud Consoleで quota確認

## セキュリティ注意事項

### 認証情報の管理

- `credentials/*.json` は絶対にGitにcommitしない
- `.gitignore` に含まれていることを確認
- GitHub Secretsのみで管理

### トークンの有効期限

- アクセストークン: 約1時間
- リフレッシュトークン: 無期限（revoke可能）
- 定期的な再認証は不要（自動refresh）

### 権限の最小化

- OAuth scopeは `youtube.upload` のみ
- 動画の削除・編集権限は含まない

## 参考リンク

- [YouTube Data API - 公式ドキュメント](https://developers.google.com/youtube/v3)
- [OAuth 2.0 - Google](https://developers.google.com/identity/protocols/oauth2)
- [YouTube API - Quota](https://developers.google.com/youtube/v3/getting-started#quota)

---

**作成日:** 2026-03-06
**最終更新:** 2026-03-06
