# Render.com デプロイ手順（完全ガイド）

競馬予想AIをRender.comにデプロイする詳細手順

## 📋 前提条件

- GitHubアカウント
- コードがGitHubにプッシュ済み: https://github.com/apol0510/keiba-ai-predictor
- Render.comアカウント（無料で作成可能）

## 🚀 デプロイ手順（所要時間: 5分）

### Step 1: Render.comアカウント作成

1. https://render.com にアクセス
2. "Get Started" をクリック
3. GitHubアカウントで登録（推奨）
4. 認証を許可

### Step 2: 新しいWebサービスを作成

1. ダッシュボードで **"New +"** ボタンをクリック
2. **"Web Service"** を選択
3. **"Connect a repository"** を選択

### Step 3: GitHubリポジトリを接続

1. **"Connect GitHub"** をクリック
2. リポジトリ検索で `keiba-ai-predictor` を検索
3. **"Connect"** をクリック

### Step 4: サービス設定

以下の設定を入力：

#### 基本設定

| 項目 | 設定値 |
|------|--------|
| **Name** | `keiba-ai-predictor` |
| **Region** | `Oregon (US West)` または `Singapore` |
| **Branch** | `master` |
| **Root Directory** | 空欄 |
| **Environment** | `Docker` |
| **Instance Type** | `Free` または `Starter ($7/月)` |

#### 詳細設定

**Docker設定:**
- Render.comは自動的に `Dockerfile` を検出します
- ビルドコマンド不要（Dockerfileに記載済み）

**環境変数（Environment Variables）:**

| Key | Value |
|-----|-------|
| `ENV` | `production` |
| `LOG_LEVEL` | `info` |
| `PORT` | `8000` |

#### ヘルスチェック設定

| 項目 | 設定値 |
|------|--------|
| **Health Check Path** | `/health` |

### Step 5: デプロイ開始

1. すべての設定を確認
2. **"Create Web Service"** をクリック
3. ビルドが自動的に開始されます

**ビルド時間:** 約5〜10分

### Step 6: デプロイ完了確認

ビルドログで以下を確認：

```
==> Building...
Step 1/8 : FROM python:3.11-slim
...
Step 8/8 : CMD ["uvicorn", "src.api.main:app", ...]
Successfully built xxxxxxxxxxxxx
==> Deploying...
==> Your service is live 🎉
```

**サービスURL:**
```
https://keiba-ai-predictor.onrender.com
```

### Step 7: 動作確認

デプロイ完了後、以下のコマンドでテスト：

```bash
# ヘルスチェック
curl https://keiba-ai-predictor.onrender.com/health

# API情報
curl https://keiba-ai-predictor.onrender.com/

# Swagger UI（ブラウザで開く）
https://keiba-ai-predictor.onrender.com/docs
```

## 🔧 トラブルシューティング

### ビルドエラー: "No such file or directory"

**原因:** モデルファイルがGitリポジトリに含まれていない

**解決策:**
1. モデルファイルをコミット
```bash
git add models/random_forest_model.pkl
git commit -m "Add trained model"
git push
```

2. Render.comで自動再デプロイされます

### メモリ不足エラー

**原因:** Freeプラン（512MB）でメモリ不足

**解決策:**
1. Starterプラン（$7/月）にアップグレード
2. または、requirements.txtから不要なパッケージを削除

### 起動が遅い

**原因:** Cold start（無料プランのスリープ機能）

**解決策:**
1. Starterプラン以上にアップグレード（常時起動）
2. または、定期的にヘルスチェックを実行

## 💰 料金プラン

### Free プラン
- **料金:** $0/月
- **制限:**
  - 750時間/月まで（約31日）
  - 15分間アクセスなしでスリープ
  - 512MB RAM
  - 共有CPU
- **推奨用途:** テスト・開発

### Starter プラン（推奨）
- **料金:** $7/月
- **特徴:**
  - 常時起動（スリープなし）
  - 512MB RAM
  - 0.5 CPU
  - 無制限稼働時間
- **推奨用途:** 本番環境

### Standard プラン
- **料金:** $25/月
- **特徴:**
  - 2GB RAM
  - 1 CPU
  - 高速応答
- **推奨用途:** 大規模トラフィック

## 🔄 自動デプロイ

GitHubにプッシュするだけで自動デプロイ！

```bash
# コード修正後
git add .
git commit -m "✨ 新機能追加"
git push

# Render.comが自動的に検出してデプロイ開始
```

**自動デプロイ設定:**
1. Render.com ダッシュボード
2. Settings → Build & Deploy
3. "Auto-Deploy" が `Yes` になっていることを確認

## 📊 モニタリング

### ログ確認

1. Render.com ダッシュボード
2. サービス選択
3. "Logs" タブ

リアルタイムでログが表示されます。

### メトリクス確認

1. "Metrics" タブ
2. 以下が表示されます：
   - CPU使用率
   - メモリ使用率
   - リクエスト数
   - レスポンスタイム

## 🌐 カスタムドメイン設定（オプション）

1. Render.com ダッシュボード
2. Settings → Custom Domains
3. "Add Custom Domain" をクリック
4. ドメイン名を入力（例: `api.your-domain.com`）
5. DNSレコードを設定（指示が表示されます）

**DNS設定例:**
```
Type: CNAME
Name: api
Value: keiba-ai-predictor.onrender.com
```

## 🔒 環境変数の更新

1. Render.com ダッシュボード
2. Environment → Environment Variables
3. 値を変更
4. "Save Changes" をクリック
5. 自動的に再デプロイされます

## ✅ デプロイ完了チェックリスト

- [ ] Render.comアカウント作成完了
- [ ] GitHubリポジトリ接続完了
- [ ] Webサービス作成完了
- [ ] 環境変数設定完了
- [ ] ビルド成功確認
- [ ] ヘルスチェック成功（`/health`）
- [ ] API動作確認（`/`）
- [ ] Swagger UI確認（`/docs`）
- [ ] 予想API動作確認（`/api/predict`）

## 🎉 完了！

デプロイURL:
```
https://keiba-ai-predictor.onrender.com
```

このURLをkeiba-intelligenceから呼び出せます！

---

**作成日**: 2026-03-05
**最終更新**: 2026-03-05
