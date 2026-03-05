# 競馬予想AI (keiba-ai-predictor)

> 機械学習による競馬予想システム - 南関東競馬・中央競馬対応

## プロジェクト概要

### コンセプト
keiba-data-sharedに蓄積された過去データから学習し、レース結果を予測する独自AIモデルを構築します。

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

### プロジェクト目標

#### Phase 1: データ基盤構築
- [ ] keiba-data-sharedからデータ収集パイプライン構築
- [ ] 特徴量エンジニアリング（馬データ、騎手データ、コース条件）
- [ ] 学習用データセット作成（訓練/検証/テスト分割）

#### Phase 2: ベースラインモデル構築
- [ ] ロジスティック回帰（シンプルモデル）
- [ ] ランダムフォレスト（アンサンブル学習）
- [ ] 勾配ブースティング（XGBoost/LightGBM）
- [ ] モデル評価（的中率・回収率）

#### Phase 3: 高度なモデル開発
- [ ] ディープラーニングモデル（LSTM/Transformer）
- [ ] アンサンブル手法（複数モデル組み合わせ）
- [ ] ハイパーパラメータチューニング
- [ ] クロスバリデーション

#### Phase 4: 本番デプロイ
- [ ] 予想API開発（FastAPI）
- [ ] keiba-intelligence連携
- [ ] 自動予想生成パイプライン
- [ ] モデル再学習システム

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
│   │   └── predictor.py           # 予想ロジック
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

## 開発フロー

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

## ライセンス
Private Project

---

**作成日**: 2026-03-05
**作成者**: Claude Code（クロちゃん）
**協力者**: マコさん
