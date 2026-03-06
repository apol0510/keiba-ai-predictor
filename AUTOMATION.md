# 🤖 コンテンツ自動化ガイド

競馬AI予想の自動化システムのドキュメントです。

**現在のステータス: 本番前テスト段階**

## ⚠️ 本番運用前の必須確認事項

このシステムは初期実装が完了していますが、以下の項目が**未検証**です。
本番運用前に必ず確認してください。

### 1. YouTube認証・投稿テスト
- [ ] ローカルで `init_youtube_auth.py` を実行し、トークン生成
- [ ] GitHub Secretsに `YOUTUBE_TOKEN_JSON` を登録
- [ ] `privacy_status='private'` で5秒テスト動画を投稿
- [ ] 日本語タイトル・説明文の文字化け確認

### 2. 動画生成の動作確認
- [ ] GitHub Actions上でのffmpeg動作確認
- [ ] 日本語フォント（fonts-noto-cjk）の表示確認
- [ ] MoviePyでの動画書き出し成功確認
- [ ] 生成動画の目視チェック（豆腐文字・崩れ）

### 3. 二重投稿防止の検証
- [ ] 同日2回実行して自動スキップ確認
- [ ] `publish_key` の適切性確認（日付+track+mode）
- [ ] `automation_state.json` のcommit/push動作確認

### 4. CMS連携・RSS反映
- [ ] 記事のCMS公開機能実装（現在は未実装）
- [ ] RSS更新の確認
- [ ] dlvr.it による X投稿の動作確認

### 5. 状態管理の移行計画
- [ ] `automation_state.json` は暫定方式であることを認識
- [ ] 長期運用時はCMS側記事ID管理またはAirtable/Supabase等への移行検討

### 6. トークンリフレッシュの永続化
- [ ] GitHub Actions上でのtoken refresh動作確認
- [ ] refresh後tokenの保存先検討（現在は次回実行時に元tokenから再開）

---

## 概要

毎日のAI予想を自動生成し、記事・動画・SNS投稿を生成する基盤です。

### 自動化フロー

```
毎日 14:00 JST (GitHub Actions実行)
    ↓
① AI予想生成（注目3レース）
    ↓
② Markdown記事自動生成
    ↓
③ 予想動画生成（MoviePy）
    ↓
④ YouTube自動投稿
    ↓
⑤ X（Twitter）自動投稿（RSS連携 via dlvr.it）
```

## ファイル構成

```
src/automation/
├── daily_prediction.py    # AI予想・記事生成
├── video_generator.py     # 動画自動生成
├── youtube_uploader.py    # YouTube API投稿
└── run_daily.py           # 統合実行スクリプト

.github/workflows/
└── daily-prediction.yml   # GitHub Actions設定

requirements-automation.txt # 自動化用依存関係
```

## セットアップ

### 1. 依存関係インストール

```bash
pip install -r requirements-automation.txt
```

### 2. YouTube API設定

#### 2.1 Google Cloud Console設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
3. **YouTube Data API v3** を有効化
4. 認証情報 → OAuth 2.0 クライアントIDを作成
   - アプリケーションの種類: **デスクトップアプリ**
   - 名前: 任意（例: keiba-ai-youtube）
5. 認証情報JSONファイルをダウンロード

#### 2.2 認証情報配置

```bash
mkdir -p credentials
cp ~/Downloads/client_secret_*.json credentials/youtube_credentials.json
```

#### 2.3 初回認証

```bash
python src/automation/youtube_uploader.py
```

ブラウザが開き、Googleアカウント認証を求められます。
認証完了後、`credentials/youtube_token.json` が生成されます。

### 3. GitHub Secrets設定

GitHub リポジトリの Settings → Secrets and variables → Actions で以下を設定：

| Secret名 | 説明 | 必須 |
|---------|------|-----|
| `YOUTUBE_CREDENTIALS` | YouTube API認証情報（JSON全体） | Yes |
| `WEBHOOK_URL` | 通知用Webhook URL（Slack/Discord）| No |

**YOUTUBE_CREDENTIALS の設定方法:**

```bash
# ファイル内容をコピー
cat credentials/youtube_credentials.json | pbcopy

# GitHub Secrets に貼り付け
```

## ローカルテスト

### 記事生成テスト

```bash
python src/automation/daily_prediction.py
```

**出力:**
- `output/article_YYYY-MM-DD.md` - Markdown記事

### 動画生成テスト

```bash
python src/automation/video_generator.py
```

**出力:**
- `test_output.mp4` - サンプル動画

### YouTube投稿テスト

```bash
python src/automation/youtube_uploader.py
```

**出力:**
- 認証成功メッセージ
- チャンネル情報表示

### 統合テスト

```bash
python src/automation/run_daily.py
```

**出力:**
- `output/article_YYYY-MM-DD.md` - 記事
- `output/prediction_YYYY-MM-DD.mp4` - 動画
- YouTube投稿URL（認証済みの場合）

## GitHub Actions自動実行

### スケジュール

- **毎日 14:00 JST (05:00 UTC)** - 自動実行
- レース開始前に予想を公開

### 手動実行

1. GitHubリポジトリの **Actions** タブ
2. **Daily AI Prediction Automation** を選択
3. **Run workflow** をクリック

### 実行ログ確認

Actions タブ → 該当のワークフロー実行 → ログ確認

### 生成ファイルのダウンロード

実行完了後、Artifacts から以下がダウンロード可能：

- `article_*.md` - Markdown記事
- `prediction_*.mp4` - 動画ファイル

保存期間: 7日間

## カスタマイズ

### 注目レース数の変更

`src/automation/run_daily.py`:

```python
article = await prediction_system.generate_daily_article(top_n=3)  # 3 → 任意の数
```

### 実行時刻の変更

`.github/workflows/daily-prediction.yml`:

```yaml
schedule:
  - cron: '0 5 * * *'  # 05:00 UTC = 14:00 JST
```

[Cron式ジェネレーター](https://crontab.guru/) を参照

### 動画スタイルの変更

`src/automation/video_generator.py`:

```python
self.colors = {
    'primary': '#667eea',    # メインカラー
    'secondary': '#764ba2',  # サブカラー
    # ...
}
```

### YouTube動画設定

`src/automation/youtube_uploader.py`:

```python
category_id='17',  # 17=Sports, 22=People & Blogs
privacy_status='public'  # public/private/unlisted
```

## X（Twitter）自動投稿設定

### dlvr.it を使用したRSS連携

1. [dlvr.it](https://dlvr.it/) にサインアップ
2. **Add Source** → RSS Feed
3. RSS URL を入力（CMSのRSSフィード）
4. **Add Route** → X（Twitter）アカウント連携
5. 投稿フォーマット設定:

```
{title}

{summary}

詳しくはこちら → {link}

#競馬 #AI予想 #{カスタムタグ}
```

### 自動投稿の流れ

```
① 記事がCMSに公開
    ↓
② RSSフィードに追加
    ↓
③ dlvr.it が検知
    ↓
④ X（Twitter）に自動投稿
```

## トラブルシューティング

### Q1. YouTube投稿が失敗する

**原因:**
- 認証情報の有効期限切れ
- OAuth 2.0 トークンが無効

**解決策:**
```bash
# 再認証
rm credentials/youtube_token.json
python src/automation/youtube_uploader.py
```

### Q2. 動画生成時にフォントエラー

**原因:**
- 日本語フォントがインストールされていない

**解決策（Ubuntu）:**
```bash
sudo apt-get install fonts-noto-cjk
```

**解決策（macOS）:**
- ヒラギノフォントは標準インストール済み

### Q3. GitHub Actions で Secrets が読み込めない

**確認事項:**
- Secret名が正確か（大文字小文字区別）
- JSON形式が正しいか（整形なし、1行）

### Q4. レースデータが取得できない

**原因:**
- keiba-data-shared の更新遅延
- 当日のレースデータが未公開

**解決策:**
- 手動実行でスキップ
- ログ確認で原因特定

## 監視・通知

### Slack通知（オプション）

`.github/workflows/daily-prediction.yml`:

```yaml
- name: Notify to Slack
  if: ${{ secrets.SLACK_WEBHOOK_URL != '' }}
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"✅ 競馬AI予想: 本日の自動化完了"}'
```

GitHub Secrets に `SLACK_WEBHOOK_URL` を設定

### Discord通知

```yaml
- name: Notify to Discord
  if: ${{ secrets.DISCORD_WEBHOOK_URL != '' }}
  run: |
    curl -X POST ${{ secrets.DISCORD_WEBHOOK_URL }} \
      -H 'Content-Type: application/json' \
      -d '{"content":"✅ 競馬AI予想: 本日の自動化完了"}'
```

## パフォーマンス

### 実行時間（目安）

| タスク | 所要時間 |
|--------|---------|
| AI予想生成 | 10-20秒 |
| 記事生成 | 1-2秒 |
| 動画生成 | 30-60秒 |
| YouTube投稿 | 20-40秒 |
| **合計** | **約2分** |

### GitHub Actions制限

- **無料プラン**: 月2,000分まで
- **1日の実行**: 約2分 × 30日 = 60分/月
- 十分に余裕あり

## ベストプラクティス

### 1. 実行前のヘルスチェック

```python
# run_daily.py に追加
async def health_check():
    """API稼働確認"""
    response = await client.get(f"{API_BASE_URL}/health")
    assert response.status_code == 200
```

### 2. エラーハンドリング

```python
try:
    article = await prediction_system.generate_daily_article()
except Exception as e:
    # ログ記録 + 通知
    send_error_notification(e)
    raise
```

### 3. リトライロジック

```python
for attempt in range(3):
    try:
        youtube_url = uploader.upload_video(...)
        break
    except Exception as e:
        if attempt == 2:
            raise
        await asyncio.sleep(10)
```

## FAQ

**Q: 手動で動画をアップロードできますか？**

A: はい。`output/prediction_*.mp4` を手動でYouTubeにアップロード可能です。

**Q: 複数のYouTubeチャンネルに投稿できますか？**

A: YouTubeアカウントごとに認証情報を分けて管理すれば可能です。

**Q: CMSとの連携方法は？**

A: 生成された `output/article_*.md` をCMS APIに送信するコードを追加してください。

**Q: 動画の解像度は変更できますか？**

A: `video_generator.py` の `__init__` で `width`, `height` を変更できます。

## 関連リンク

- [GitHub Actions ドキュメント](https://docs.github.com/en/actions)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [MoviePy ドキュメント](https://zulko.github.io/moviepy/)
- [dlvr.it](https://dlvr.it/)

---

**作成日**: 2026-03-05
**最終更新**: 2026-03-05
