"""
ベースライン機械学習モデル
- ロジスティック回帰
- ランダムフォレスト
- 勾配ブースティング（XGBoost/LightGBM）
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb
import joblib
from pathlib import Path
from typing import Tuple, Dict, List


class BaselineModel:
    """ベースライン機械学習モデル"""

    def __init__(self, model_type: str = 'random_forest'):
        """
        Args:
            model_type: 'logistic', 'random_forest', 'xgboost', 'lightgbm'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_cols = None

    def _get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """学習に使用する特徴量カラムを取得"""
        # 除外するカラム
        exclude_cols = [
            'date', 'venue', 'venue_code', 'race_number', 'race_name',
            'rank', 'number', 'name', 'jockey', 'trainer',
            'time', 'margin', 'last_furlong',
            'bracket', 'tansho_payout', 'umatan_payout',
            'is_winner',  # 目的変数
            'time_seconds', 'last_furlong_seconds',  # タイム系は除外（未来情報）
            'track', 'weather', 'track_condition', 'surface'  # エンコード前のカラム
        ]

        # 数値型の特徴量のみ使用
        feature_cols = []
        for col in df.columns:
            if col not in exclude_cols and df[col].dtype in ['int64', 'float64']:
                feature_cols.append(col)

        return feature_cols

    def prepare_data(
        self,
        df: pd.DataFrame,
        target_col: str = 'is_winner'
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """データ準備"""
        # 特徴量カラムを取得
        if self.feature_cols is None:
            self.feature_cols = self._get_feature_columns(df)

        print(f"使用する特徴量: {len(self.feature_cols)}個")
        print(f"特徴量リスト: {self.feature_cols}")

        # 特徴量・目的変数を分離
        X = df[self.feature_cols].copy()
        y = df[target_col].copy()

        # 欠損値補完（0埋め）
        X = X.fillna(0)

        return X, y

    def build_model(self):
        """モデル構築"""
        if self.model_type == 'logistic':
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42
            )
        elif self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'xgboost':
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric='logloss'
            )
        elif self.model_type == 'lightgbm':
            self.model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbose=-1
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        print(f"モデル構築完了: {self.model_type}")

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        normalize: bool = True
    ):
        """モデル学習"""
        print(f"学習データ: {len(X_train)}行")
        print(f"正例（1着）: {y_train.sum()}件 ({y_train.mean()*100:.2f}%)")

        # 正規化
        if normalize:
            X_train_scaled = self.scaler.fit_transform(X_train)
        else:
            X_train_scaled = X_train.values

        # モデル未構築の場合は構築
        if self.model is None:
            self.build_model()

        # 学習
        print("学習開始...")
        self.model.fit(X_train_scaled, y_train)
        print("学習完了")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """予測（クラス）"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """予測（確率）"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)

    def get_feature_importance(self) -> pd.DataFrame:
        """特徴量重要度を取得"""
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            importance = np.abs(self.model.coef_[0])
        else:
            return None

        importance_df = pd.DataFrame({
            'feature': self.feature_cols,
            'importance': importance
        }).sort_values('importance', ascending=False)

        return importance_df

    def save(self, output_path: str):
        """モデル保存"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'model_type': self.model_type,
            'model': self.model,
            'scaler': self.scaler,
            'feature_cols': self.feature_cols
        }

        joblib.dump(model_data, output_path)
        print(f"モデル保存完了: {output_path}")

    @classmethod
    def load(cls, model_path: str):
        """モデル読み込み"""
        model_data = joblib.load(model_path)

        instance = cls(model_type=model_data['model_type'])
        instance.model = model_data['model']
        instance.scaler = model_data['scaler']
        instance.feature_cols = model_data['feature_cols']

        print(f"モデル読み込み完了: {model_path}")
        return instance


if __name__ == '__main__':
    # テスト用コード
    print("ベースラインモデルモジュール")
    print("使用方法:")
    print("  from src.models.baseline import BaselineModel")
    print("  model = BaselineModel(model_type='random_forest')")
    print("  model.train(X_train, y_train)")
    print("  predictions = model.predict_proba(X_test)")
