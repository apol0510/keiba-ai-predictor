#!/bin/bash
# 競馬予想AI セットアップスクリプト

set -e

echo "=== 競馬予想AI セットアップ開始 ==="

# 作業ディレクトリ確認
cd "$(dirname "$0")"
echo "作業ディレクトリ: $(pwd)"

# Python仮想環境作成
if [ ! -d "venv" ]; then
    echo "Python仮想環境を作成中..."
    python3 -m venv venv
    echo "仮想環境作成完了"
else
    echo "仮想環境は既に存在します"
fi

# 仮想環境アクティベート
echo "仮想環境をアクティベート中..."
source venv/bin/activate

# 依存関係インストール
echo "依存関係をインストール中..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "  1. 仮想環境をアクティベート:"
echo "     source venv/bin/activate"
echo ""
echo "  2. データ収集:"
echo "     python src/data/collector.py"
echo ""
echo "  3. データ前処理:"
echo "     python src/data/preprocessor.py"
echo ""
echo "  4. 特徴量生成:"
echo "     python src/data/feature_engineer.py"
echo ""
echo "  5. モデル学習:"
echo "     python src/training/train.py --model random_forest"
echo ""
