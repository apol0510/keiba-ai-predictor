# 競馬予想AI (keiba-ai-predictor)

> 🎯 **無料で使える機械学習競馬予想API** - 南関東競馬・中央競馬対応

[![API Status](https://img.shields.io/badge/API-Live-success)](https://keiba-ai-predictor.onrender.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 📢 無料公開API

**誰でも自由に使える競馬予想API** を公開しています！

- 🆓 **完全無料** - 登録不要、API Key不要
- 🤖 **AI予想** - 機械学習による勝率予測
- 📊 **的中率33.01%** - 10,786レースで学習
- 🔓 **オープンソース** - コードも全て公開

**本番API:** https://keiba-ai-predictor.onrender.com

**使い方ガイド:** [API_USAGE.md](API_USAGE.md)

---

## プロジェクト概要

### コンセプト

keiba-data-sharedに蓄積された過去データから学習し、レース結果を予測する独自AIモデルを構築・公開しています。

**このプロジェクトは試作版です。** より詳しい予想・分析は **[keiba-intelligence](https://keiba-intelligence.netlify.app)** でご利用いただけます。

### 技術スタック

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| **言語** | Python 3.11+ | ML開発の標準 |
| **ML Framework** | scikit-learn | 機械学習モデル構築 |
| **深層学習** | TensorFlow / Keras | ニューラルネットワーク |
| **データ処理** | pandas, numpy | データ前処理・特徴量生成 |
| **可視化** | matplotlib, seaborn | データ分析・評価 |
| **API** | FastAPI | 予想API提供 |
| **デプロイ** | Docker | 本番環境構築 |

### 達成状況

#### Phase 1: データ基盤構築 ✅
- [x] keiba-data-sharedからデータ収集パイプライン構築
- [x] 特徴量エンジニアリング（馬データ、騎手データ、コース条件）
- [x] 学習用データセット作成（訓練/検証/テスト分割）

#### Phase 2: ベースラインモデル構築 ✅
- [x] ランダムフォレスト（アンサンブル学習）
- [x] モデル評価（的中率・回収率）

#### Phase 3: 高度なモデル開発 🚧
- [ ] ディープラーニングモデル（LSTM/Transformer）
- [ ] アンサンブル手法（複数モデル組み合わせ）
- [ ] ハイパーパラメータチューニング

#### Phase 4: 本番デプロイ ✅
- [x] 予想API開発（FastAPI）
- [x] Docker化・本番環境構築
- [x] 無料公開API
- [x] レート制限実装
- [x] 外部API連携（keiba-data-shared）
- [x] SEO最適化済みWebサイト公開

#### Phase 5: コンテンツ自動化 🚧
- [ ] 毎日の予想記事自動生成
- [ ] 予想動画自動生成（MoviePy）
- [ ] YouTube自動投稿
- [ ] X（Twitter）自動投稿（RSS連携）
- [ ] GitHub Actions定期実行

## ディレクトリ構造

```
keiba-ai-predictor/
├── README.md                      # このファイル
├── requirements.txt               # Python依存関係
├── .gitignore                     # Git除外設定
├── Dockerfile                     # Docker設定
├── docker-compose.yml             # Docker Compose設定
├── data/                          # データ管理
│   ├── raw/                       # 生データ（keiba-data-sharedから取得）
│   ├── processed/                 # 前処理済みデータ
│   └── features/                  # 特徴量データ
├── notebooks/                     # Jupyter Notebook（データ分析・実験）
│   ├── 01_data_exploration.ipynb  # データ探索
│   ├── 02_feature_engineering.ipynb # 特徴量生成
│   └── 03_model_experiments.ipynb # モデル実験
├── src/                           # ソースコード
│   ├── data/                      # データ収集・前処理
│   │   ├── collector.py           # データ収集
│   │   ├── preprocessor.py        # 前処理
│   │   └── feature_engineer.py    # 特徴量生成
│   ├── models/                    # モデル定義
│   │   ├── baseline.py            # ベースラインモデル
│   │   ├── ensemble.py            # アンサンブルモデル
│   │   └── deep_learning.py       # ディープラーニング
│   ├── training/                  # 学習スクリプト
│   │   ├── train.py               # 学習実行
│   │   └── evaluate.py            # 評価
│   ├── api/                       # 予想API
│   │   ├── main.py                # FastAPIアプリ
│   │   ├── predictor.py           # 予想ロジック
│   │   ├── race_data.py           # レースデータ取得
│   │   └── rate_limiter.py        # レート制限
│   ├── automation/                # コンテンツ自動化（NEW）
│   │   ├── daily_prediction.py    # 毎日の予想生成
│   │   ├── video_generator.py     # 動画自動生成
│   │   ├── youtube_uploader.py    # YouTube投稿
│   │   └── run_daily.py           # 統合実行スクリプト
│   └── utils/                     # ユーティリティ
│       ├── metrics.py             # 評価指標
│       └── visualization.py       # 可視化
├── models/                        # 学習済みモデル保存
│   └── .gitkeep
├── logs/                          # ログファイル
│   └── .gitkeep
└── tests/                         # テストコード
    └── .gitkeep
```

## 特徴量設計

### 1. 馬の特徴量
- 過去成績（勝率、連対率、複勝率）
- 距離適性（ベスト距離、距離別成績）
- 馬場適性（ダート/芝、馬場状態別成績）
- コース適性（競馬場別成績）
- 休養明け日数
- 前走着順、前走タイム
- 斤量
- 年齢、性別

### 2. 騎手・調教師の特徴量
- 騎手勝率、連対率
- 調教師勝率、連対率
- 馬×騎手の相性（過去成績）
- 馬×調教師の相性

### 3. レース条件の特徴量
- 距離、馬場種別（ダート/芝）
- 天候、馬場状態
- 出走頭数
- 枠番、馬番
- クラス（未勝利、1勝クラス等）

### 4. オッズ特徴量
- 単勝オッズ
- 人気順位
- オッズ変動

## モデル評価指標

### 1. 的中率
- Top-1的中率（本命の勝率）
- Top-3的中率（上位3頭に1着が入る率）
- 馬単的中率（1-2着順序的中）

### 2. 回収率
- 単勝回収率
- 馬単回収率
- 三連単回収率

### 3. ML標準指標
- AUC-ROC（分類性能）
- Log Loss（確率予測精度）
- Precision/Recall/F1

## 🚀 クイックスタート（API利用者向け）

### 1. ヘルスチェック

```bash
curl https://keiba-ai-predictor.onrender.com/health
```

### 2. 予想を実行

```bash
curl -X POST https://keiba-ai-predictor.onrender.com/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-03-05",
    "venue": "大井",
    "venue_code": "OI",
    "race_number": 1,
    "distance": 1200,
    "surface": "ダート",
    "horses": [
      {"number": 1, "name": "サンプルホース", "popularity": 1}
    ]
  }'
```

### 3. 詳しい使い方

**[API使い方ガイド（API_USAGE.md）](API_USAGE.md)** をご覧ください。

プログラミング言語別のサンプルコード（JavaScript, Python, Ruby, PHP）も用意しています。

---

## 🛠️ 開発者向け情報

### セットアップ
```bash
# プロジェクトディレクトリ作成
mkdir -p /Users/apolon/Projects/keiba-ai-predictor
cd /Users/apolon/Projects/keiba-ai-predictor

# Python仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# Jupyter起動
jupyter lab
```

### データ収集
```bash
python src/data/collector.py --source keiba-data-shared --output data/raw/
```

### 前処理・特徴量生成
```bash
python src/data/preprocessor.py --input data/raw/ --output data/processed/
python src/data/feature_engineer.py --input data/processed/ --output data/features/
```

### モデル学習
```bash
python src/training/train.py --model baseline --data data/features/
python src/training/train.py --model ensemble --data data/features/
python src/training/train.py --model deep_learning --data data/features/
```

### 評価
```bash
python src/training/evaluate.py --model models/baseline.pkl --test-data data/features/test.csv
```

### API起動
```bash
uvicorn src.api.main:app --reload --port 8000
```

## keiba-intelligence連携

### 予想APIエンドポイント
```
POST /api/predict
{
  "date": "2026-03-05",
  "venue": "大井",
  "race_number": 1,
  "horses": [
    {"number": 1, "name": "馬A", ...},
    {"number": 2, "name": "馬B", ...}
  ]
}

Response:
{
  "predictions": [
    {"number": 1, "win_probability": 0.35, "rank": 1},
    {"number": 2, "win_probability": 0.25, "rank": 2}
  ],
  "betting_lines": {
    "umatan": ["1-2.3.5", "2-1.3.5"]
  }
}
```

### 統合フロー
```
keiba-intelligence（予想ページ）
  ↓
keiba-ai-predictor（予想API）
  ↓
機械学習モデル推論
  ↓
予想結果返却（JSON）
  ↓
keiba-intelligence表示
```

## 🐳 Docker化・本番デプロイ

### ローカルDockerテスト

```bash
# Dockerイメージビルド
docker build -t keiba-ai-predictor:latest .

# コンテナ起動
docker run -d -p 8000:8000 keiba-ai-predictor:latest

# Docker Compose起動（Nginx + API）
docker-compose up -d
```

### クラウドデプロイ

**Render.com への簡単デプロイ:**

詳細は **[RENDER_DEPLOY.md](RENDER_DEPLOY.md)** を参照してください。

1. GitHubにプッシュ
2. Render.comでリポジトリ接続
3. デプロイボタンをクリック
4. 完了！

**その他のプラットフォーム:**

`DEPLOYMENT.md` に詳細手順があります。

- **Google Cloud Run** - 自動スケーリング、無料枠あり
- **Railway** - 開発者フレンドリー
- **AWS ECS/Fargate** - エンタープライズ向け

## 📊 性能指標

**検証データでの評価結果:**
- 的中率（本命）: **33.01%**
- 的中率（TOP3）: **61.17%**
- 学習データ: 10,786レース×馬
- 特徴量: 19個

**重要な特徴量:**
1. 人気 (55.1%)
2. 騎手連対率 (11.4%)
3. 騎手勝率 (8.8%)

## 🔗 より詳しい予想をお求めの方へ

### keiba-intelligence

このAPIは試作版です。より詳しい予想・分析をお求めの方は、本格的な予想サービス **[keiba-intelligence](https://keiba-intelligence.netlify.app)** をご利用ください。

**主な機能:**
- 📊 過去データの詳細分析
- 👤 騎手・調教師の統計情報
- 💰 オッズ分析
- 🎯 的中率向上支援ツール
- ⚡ リアルタイム予想更新

---

## ⚖️ レート制限

無料公開APIとして、以下の制限を設けています：

| 期間 | 上限 |
|-----|-----|
| 1分 | 10リクエスト |
| 1時間 | 100リクエスト |
| 1日 | 1000リクエスト |

制限を超えた場合は `429 Too Many Requests` エラーが返されます。

**レート制限の確認:**
```bash
curl https://keiba-ai-predictor.onrender.com/api/rate-limit-status
```

## 🤖 コンテンツ自動化

毎日の予想を完全自動化し、記事・動画・SNS投稿を自動生成します。

### 自動化フロー

```
毎日15:00（レース開始前）GitHub Actions実行
    ↓
① AI予想生成（注目3レース）
    ↓
② 記事自動生成・公開（CMS連携）
    ↓
③ 予想動画生成（MoviePy）
    ↓
④ YouTube自動投稿
    ↓
⑤ X（Twitter）自動投稿（RSS連携）
```

### 詳細

詳しくは **[AUTOMATION.md](AUTOMATION.md)** を参照してください。

## 📄 ドキュメント

| ドキュメント | 説明 |
|------------|------|
| **[API_USAGE.md](API_USAGE.md)** | API使い方ガイド（一般ユーザー向け） |
| **[AUTOMATION.md](AUTOMATION.md)** | コンテンツ自動化の仕組み（NEW） |
| **[RENDER_DEPLOY.md](RENDER_DEPLOY.md)** | Render.comデプロイ手順 |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | 各種クラウドプラットフォームへのデプロイ手順 |
| **[QUICKSTART.md](QUICKSTART.md)** | 開発者向けクイックスタート |

## 🤝 コントリビューション

このプロジェクトはオープンソースです。バグ報告や機能要望は [Issues](https://github.com/apol0510/keiba-ai-predictor/issues) までお願いします。

## ⭐ Star をお願いします！

このプロジェクトが役に立った場合は、GitHub でスターをつけていただけると嬉しいです！

## ライセンス

MIT License

---

**作成日**: 2026-03-05
**作成者**: Claude Code（クロちゃん）
**協力者**: マコさん
**最終更新**: 2026-03-05

**本番API**: https://keiba-ai-predictor.onrender.com
**GitHub**: https://github.com/apol0510/keiba-ai-predictor
