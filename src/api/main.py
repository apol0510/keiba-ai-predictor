"""
競馬予想API
FastAPIによるREST API実装
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
from pathlib import Path

# src/ を import パスに追加
sys.path.append(str(Path(__file__).parent.parent))

from api.predictor import RacePredictor

app = FastAPI(
    title="競馬予想API",
    description="機械学習による競馬予想システム",
    version="1.0.0"
)

# CORS設定（keiba-intelligenceからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://keiba-intelligence.netlify.app",
        "http://localhost:4321",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 予測器のグローバルインスタンス
predictor = None


@app.on_event("startup")
async def startup_event():
    """起動時処理: モデル読み込み"""
    global predictor
    predictor = RacePredictor(
        model_path='models/random_forest_model.pkl'
    )
    print("モデル読み込み完了")


# リクエスト・レスポンスモデル
class Horse(BaseModel):
    number: int
    name: str
    jockey: Optional[str] = None
    trainer: Optional[str] = None
    popularity: Optional[int] = None


class PredictRequest(BaseModel):
    date: str  # YYYY-MM-DD
    venue: str
    venue_code: str
    race_number: int
    distance: int
    surface: str  # ダート or 芝
    weather: Optional[str] = '晴'
    track_condition: Optional[str] = '良'
    horses: List[Horse]


class HorsePrediction(BaseModel):
    number: int
    name: str
    win_probability: float
    rank: int
    role: str  # 本命, 対抗, 単穴, 連下
    mark: str  # ◎, ○, ▲, △


class PredictResponse(BaseModel):
    predictions: List[HorsePrediction]
    betting_lines: Dict[str, List[str]]


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "競馬予想API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "model_loaded": predictor is not None
    }


@app.post("/api/predict", response_model=PredictResponse)
async def predict_race(request: PredictRequest):
    """
    レース予想エンドポイント

    Args:
        request: レース情報・出走馬情報

    Returns:
        予想結果（勝率・役割・買い目）
    """
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="モデルが読み込まれていません"
        )

    try:
        # 予想実行
        result = predictor.predict(request.dict())

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"予想エラー: {str(e)}"
        )


@app.get("/api/model-info")
async def get_model_info():
    """モデル情報取得"""
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="モデルが読み込まれていません"
        )

    return {
        "model_type": predictor.model.model_type,
        "features_count": len(predictor.model.feature_cols) if predictor.model.feature_cols else 0,
        "feature_names": predictor.model.feature_cols
    }


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
