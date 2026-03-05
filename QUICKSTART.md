# クイックスタートガイド

競馬予想AIを1から構築して動かすまでの手順

## 📋 前提条件

- Python 3.11以上
- keiba-data-sharedリポジトリ（ローカルにクローン済み）
- 十分なディスク容量（データ+モデルで約500MB）

## 🚀 セットアップ手順

### 1. プロジェクトディレクトリに移動

```bash
cd /Users/apolon/Projects/keiba-ai-predictor
```

### 2. セットアップスクリプト実行

```bash
./setup.sh
```

これにより以下が実行されます:
- Python仮想環境作成（venv/）
- 依存関係インストール（requirements.txt）

### 3. 仮想環境アクティベート

```bash
source venv/bin/activate
```

## 📊 データパイプライン実行

### Step 1: データ収集

keiba-data-sharedから過去のレース結果を収集します。

```bash
python src/data/collector.py
```

**出力:**
- `data/raw/nankan_results.csv` - 南関競馬結果
- `data/raw/jra_results.csv` - 中央競馬結果
- `data/raw/all_results.csv` - 統合データ

**所要時間:** 約1-2分

### Step 2: データ前処理

生データをクリーニング・変換します。

```bash
python src/data/preprocessor.py --file all_results.csv
```

**出力:**
- `data/processed/all_results_processed.csv`

**所要時間:** 約1分

### Step 3: 特徴量生成

過去成績などの高度な特徴量を生成します。

```bash
python src/data/feature_engineer.py --file all_results_processed.csv
```

**出力:**
- `data/features/all_results_features.csv`

**所要時間:** 約5-10分（データ量に依存）

## 🤖 モデル学習

### ランダムフォレストモデル（推奨）

```bash
python src/training/train.py --model random_forest --data data/features/all_results_features.csv
```

**出力:**
- `models/random_forest_model.pkl` - 学習済みモデル
- `models/test_data.csv` - テストデータ

**所要時間:** 約3-5分

### その他のモデル

```bash
# ロジスティック回帰
python src/training/train.py --model logistic

# XGBoost
python src/training/train.py --model xgboost

# LightGBM
python src/training/train.py --model lightgbm
```

## 🌐 予想API起動

### ローカルサーバー起動

```bash
cd /Users/apolon/Projects/keiba-ai-predictor
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

**アクセス:**
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### APIテスト

```bash
curl -X POST "http://localhost:8000/api/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-03-05",
    "venue": "大井",
    "venue_code": "OI",
    "race_number": 1,
    "distance": 1200,
    "surface": "ダート",
    "weather": "晴",
    "track_condition": "良",
    "horses": [
      {"number": 1, "name": "テストホース1", "popularity": 1},
      {"number": 2, "name": "テストホース2", "popularity": 2},
      {"number": 3, "name": "テストホース3", "popularity": 3}
    ]
  }'
```

## 📈 モデル評価

学習時に表示される評価指標:

- **的中率（本命）**: 予測確率最高の馬が1着になる確率
- **的中率（TOP3）**: 上位3頭に1着が入る確率
- **平均予測確率（1着馬）**: 実際の1着馬に対する予測確率
- **平均予測確率（敗北馬）**: 1着以外の馬に対する予測確率

**目標値:**
- 的中率（本命）: 30%以上
- 的中率（TOP3）: 70%以上
- 確率分離度: 0.15以上

## 🔗 keiba-intelligence連携

### Netlify Functionとして実装

1. `keiba-intelligence/astro-site/netlify/functions/ml-predict.js` を作成:

```javascript
// Netlify Function経由でML APIを呼び出し
export async function handler(event, context) {
  const raceData = JSON.parse(event.body);

  // ML API（keiba-ai-predictor）を呼び出し
  const response = await fetch('http://localhost:8000/api/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(raceData)
  });

  const predictions = await response.json();

  return {
    statusCode: 200,
    body: JSON.stringify(predictions)
  };
}
```

2. 予想ページで呼び出し:

```javascript
// prediction.astro 内
const mlPredictions = await fetch('/.netlify/functions/ml-predict', {
  method: 'POST',
  body: JSON.stringify(raceData)
}).then(r => r.json());
```

## 🐛 トラブルシューティング

### 依存関係エラー

```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### モデル読み込みエラー

モデルファイルが存在するか確認:

```bash
ls -la models/
```

### メモリ不足エラー

特徴量生成時にメモリ不足の場合:

```bash
# データを分割して処理
python src/data/feature_engineer.py --file nankan_results_processed.csv
python src/data/feature_engineer.py --file jra_results_processed.csv
```

## 📚 次のステップ

1. **データ蓄積**: keiba-data-sharedに新しいデータを追加
2. **モデル再学習**: 定期的に再学習して精度向上
3. **特徴量追加**: オッズ・血統などの新特徴量を追加
4. **ディープラーニング**: LSTMやTransformerモデルを試す
5. **本番デプロイ**: Docker化してクラウドデプロイ

## 💡 ヒント

- **初回学習**: データが少ない場合、的中率は低くなります。データが増えるごとに精度向上します。
- **過学習対策**: `max_depth`, `min_samples_split` などのパラメータを調整
- **特徴量重要度**: 学習時に表示される重要度を見て、不要な特徴量を削除
- **定期再学習**: 週1回程度の再学習を推奨

---

**作成日**: 2026-03-05
**最終更新**: 2026-03-05
