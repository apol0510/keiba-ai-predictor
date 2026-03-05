# 競馬予想AI デプロイガイド

本番環境へのデプロイ手順とクラウドプラットフォーム別の設定方法

## 📋 目次

1. [ローカルDockerテスト](#ローカルdockerテスト)
2. [クラウドプラットフォーム選択](#クラウドプラットフォーム選択)
3. [Google Cloud Run デプロイ](#google-cloud-run-デプロイ)
4. [AWS ECS/Fargate デプロイ](#aws-ecsfargate-デプロイ)
5. [Render.com デプロイ](#rendercom-デプロイ)
6. [Railway デプロイ](#railway-デプロイ)
7. [GitHub Actions 自動デプロイ](#github-actions-自動デプロイ)

---

## ローカルDockerテスト

### 1. Dockerイメージビルド

```bash
cd /Users/apolon/Projects/keiba-ai-predictor

# イメージビルド
docker build -t keiba-ai-predictor:latest .

# ビルド確認
docker images | grep keiba-ai-predictor
```

### 2. コンテナ起動

```bash
# 単体起動
docker run -d \
  --name keiba-ai \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models:ro \
  keiba-ai-predictor:latest

# ログ確認
docker logs -f keiba-ai

# 動作確認
curl http://localhost:8000/
curl http://localhost:8000/health
```

### 3. Docker Compose起動

```bash
# 起動（Nginx + API）
docker-compose up -d

# ログ確認
docker-compose logs -f

# 停止
docker-compose down
```

### 4. APIテスト

```bash
# ヘルスチェック
curl http://localhost/health

# 予想APIテスト
curl -X POST http://localhost/api/predict \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

---

## クラウドプラットフォーム選択

### 推奨プラットフォーム比較

| プラットフォーム | 月額コスト | 難易度 | スケーラビリティ | 推奨度 |
|----------------|-----------|--------|-----------------|--------|
| **Google Cloud Run** | $0〜$10 | 低 | 自動 | ★★★★★ |
| **Render.com** | $7〜$25 | 超低 | 自動 | ★★★★☆ |
| **Railway** | $5〜$20 | 低 | 自動 | ★★★★☆ |
| AWS ECS/Fargate | $20〜$50 | 中 | 手動 | ★★★☆☆ |
| Azure Container Instances | $15〜$40 | 中 | 手動 | ★★★☆☆ |

**推奨**: **Google Cloud Run** または **Render.com**
- 無料枠あり
- 自動スケーリング
- シンプルなデプロイ

---

## Google Cloud Run デプロイ

### 前提条件
- Google Cloudアカウント
- gcloud CLI インストール済み

### 手順

#### 1. gcloud初期設定

```bash
# gcloud認証
gcloud auth login

# プロジェクト作成
gcloud projects create keiba-ai-project --name="Keiba AI Predictor"

# プロジェクト設定
gcloud config set project keiba-ai-project

# APIを有効化
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### 2. Docker イメージをビルド・プッシュ

```bash
# Artifact Registry設定
gcloud services enable artifactregistry.googleapis.com

# リポジトリ作成
gcloud artifacts repositories create keiba-ai-repo \
  --repository-format=docker \
  --location=asia-northeast1 \
  --description="Keiba AI Docker images"

# 認証設定
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# イメージタグ付け
docker tag keiba-ai-predictor:latest \
  asia-northeast1-docker.pkg.dev/keiba-ai-project/keiba-ai-repo/keiba-ai:latest

# プッシュ
docker push asia-northeast1-docker.pkg.dev/keiba-ai-project/keiba-ai-repo/keiba-ai:latest
```

#### 3. Cloud Run デプロイ

```bash
gcloud run deploy keiba-ai-predictor \
  --image=asia-northeast1-docker.pkg.dev/keiba-ai-project/keiba-ai-repo/keiba-ai:latest \
  --platform=managed \
  --region=asia-northeast1 \
  --allow-unauthenticated \
  --port=8000 \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=60s

# デプロイ完了後、URLが表示されます
# 例: https://keiba-ai-predictor-xxxxx-an.a.run.app
```

#### 4. 動作確認

```bash
# ヘルスチェック
curl https://keiba-ai-predictor-xxxxx-an.a.run.app/health

# 予想APIテスト
curl -X POST https://keiba-ai-predictor-xxxxx-an.a.run.app/api/predict \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

#### 5. カスタムドメイン設定（オプション）

```bash
# ドメインマッピング
gcloud run domain-mappings create \
  --service=keiba-ai-predictor \
  --domain=api.your-domain.com \
  --region=asia-northeast1
```

### 料金見積もり

**無料枠:**
- 月間200万リクエスト無料
- 360,000 vCPU秒無料
- 180,000 GiB秒無料

**従量課金（無料枠超過後）:**
- リクエスト: $0.40 / 100万リクエスト
- CPU: $0.00002400 / vCPU秒
- メモリ: $0.00000250 / GiB秒

**想定月額:**
- 10,000リクエスト/月: **$0（無料枠内）**
- 100,000リクエスト/月: **$3〜$5**
- 1,000,000リクエスト/月: **$10〜$20**

---

## Render.com デプロイ

### 最もシンプルな方法！

#### 1. GitHubリポジトリ作成

```bash
cd /Users/apolon/Projects/keiba-ai-predictor

# GitHubリポジトリ作成（GitHub CLI使用）
gh repo create keiba-ai-predictor --public --source=. --remote=origin

# プッシュ
git add .
git commit -m "🚀 本番デプロイ準備完了"
git push -u origin master
```

#### 2. Render.comでデプロイ

1. https://render.com にアクセス
2. "New Web Service" をクリック
3. GitHubリポジトリを接続
4. 設定:
   - **Name**: keiba-ai-predictor
   - **Environment**: Docker
   - **Region**: Oregon (US West) または Singapore
   - **Instance Type**: Starter ($7/月) or Free
   - **Port**: 8000
5. "Create Web Service" をクリック

#### 3. 環境変数設定

Render.com ダッシュボードで設定:
- `ENV=production`
- `LOG_LEVEL=info`

#### 4. 自動デプロイ

GitHubにpushするだけで自動デプロイ！

```bash
git add .
git commit -m "✨ 新機能追加"
git push
```

### 料金

- **Free**: $0/月（スリープあり、月750時間）
- **Starter**: $7/月（常時起動、512MB RAM、0.5 CPU）
- **Standard**: $25/月（2GB RAM、1 CPU）

---

## Railway デプロイ

### 手順

#### 1. Railway CLIインストール

```bash
npm install -g @railway/cli

# ログイン
railway login
```

#### 2. プロジェクト初期化

```bash
cd /Users/apolon/Projects/keiba-ai-predictor

# プロジェクト作成
railway init

# デプロイ
railway up
```

#### 3. ドメイン設定

Railway ダッシュボードで:
1. Settings → Domains
2. "Generate Domain" をクリック

### 料金

- **Hobby**: $5/月（500時間実行、512MB RAM）
- **Pro**: $20/月（無制限実行、8GB RAM）

---

## GitHub Actions 自動デプロイ

### Google Cloud Run 自動デプロイ

`.github/workflows/deploy.yml` を作成:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup gcloud CLI
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}

      - name: Configure Docker
        run: |
          gcloud auth configure-docker asia-northeast1-docker.pkg.dev

      - name: Build Docker image
        run: |
          docker build -t asia-northeast1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/keiba-ai-repo/keiba-ai:${{ github.sha }} .
          docker tag asia-northeast1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/keiba-ai-repo/keiba-ai:${{ github.sha }} \
            asia-northeast1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/keiba-ai-repo/keiba-ai:latest

      - name: Push Docker image
        run: |
          docker push asia-northeast1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/keiba-ai-repo/keiba-ai:${{ github.sha }}
          docker push asia-northeast1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/keiba-ai-repo/keiba-ai:latest

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy keiba-ai-predictor \
            --image=asia-northeast1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/keiba-ai-repo/keiba-ai:${{ github.sha }} \
            --platform=managed \
            --region=asia-northeast1 \
            --allow-unauthenticated
```

### GitHub Secrets設定

1. GitHub リポジトリ → Settings → Secrets
2. 以下を追加:
   - `GCP_SA_KEY`: サービスアカウントのJSONキー
   - `GCP_PROJECT_ID`: プロジェクトID

---

## 監視・ログ

### Google Cloud Run

```bash
# ログ確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=keiba-ai-predictor" \
  --limit=50 \
  --format=json

# メトリクス確認
gcloud run services describe keiba-ai-predictor --region=asia-northeast1
```

### Render.com / Railway

ダッシュボードで自動的にログ・メトリクスが表示されます。

---

## トラブルシューティング

### メモリ不足

```yaml
# Dockerfile修正
FROM python:3.11-slim  # 軽量イメージ使用

# requirements.txt から不要なパッケージ削除
# matplotlib, seaborn, plotly など
```

### 起動が遅い

```bash
# ヘルスチェック猶予期間を延長
--timeout=120s
--start-period=60s
```

### モデルファイルが大きい

```bash
# モデル圧縮
import joblib
model = joblib.load('model.pkl')
joblib.dump(model, 'model_compressed.pkl', compress=9)
```

---

## 推奨デプロイ手順

**初心者向け: Render.com**
1. GitHubにプッシュ
2. Render.comでリポジトリ接続
3. デプロイボタンクリック
4. 完了！

**本格運用: Google Cloud Run**
1. gcloud CLIセットアップ
2. Dockerイメージビルド・プッシュ
3. Cloud Runデプロイ
4. GitHub Actions自動化

---

**作成日**: 2026-03-05
**最終更新**: 2026-03-05
