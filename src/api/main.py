"""
競馬予想API
FastAPIによるREST API実装
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
from pathlib import Path

# src/ を import パスに追加
sys.path.append(str(Path(__file__).parent.parent))

from api.predictor import RacePredictor
from api.rate_limiter import RateLimiter

app = FastAPI(
    title="競馬予想API",
    description="機械学習による競馬予想システム",
    version="1.0.0"
)

# 静的ファイル配信
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS設定（全てのオリジンからのアクセスを許可 - 無料公開版）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 誰でも使える無料API
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 予測器のグローバルインスタンス
predictor = None

# レート制限（無料公開版として適切な制限）
rate_limiter = RateLimiter(
    requests_per_minute=10,    # 1分あたり10リクエスト
    requests_per_hour=100,     # 1時間あたり100リクエスト
    requests_per_day=1000      # 1日あたり1000リクエスト
)


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
    promotion: Optional[Dict] = None  # keiba-intelligenceへの導線


@app.get("/")
async def root():
    """ルートエンドポイント - HTMLページを返す"""
    return FileResponse('static/index.html')


@app.get("/api")
async def api_root():
    """APIルートエンドポイント"""
    return {
        "message": "競馬予想API - 機械学習による無料競馬予想",
        "version": "1.0.0",
        "status": "running",
        "description": "このAPIは無料で公開されています。AI予想をお試しください。",
        "endpoints": {
            "predict": "/api/predict",
            "model_info": "/api/model-info",
            "docs": "/docs"
        },
        "promotion": {
            "message": "より詳しい予想・分析は keiba-intelligence で",
            "url": "https://keiba-intelligence.netlify.app",
            "description": "プロ級の予想サービス"
        }
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "model_loaded": predictor is not None
    }


@app.post("/api/predict", response_model=PredictResponse)
async def predict_race(predict_request: PredictRequest, request: Request):
    """
    レース予想エンドポイント

    Args:
        predict_request: レース情報・出走馬情報
        request: FastAPI Request（レート制限用）

    Returns:
        予想結果（勝率・役割・買い目）
    """
    # レート制限チェック
    await rate_limiter.check_rate_limit(request)

    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="モデルが読み込まれていません"
        )

    try:
        # 予想実行
        result = predictor.predict(predict_request.dict())

        # keiba-intelligenceへの導線を追加
        result['promotion'] = {
            "message": "より詳しい予想・分析をご希望の方へ",
            "service_name": "keiba-intelligence",
            "url": "https://keiba-intelligence.netlify.app",
            "features": [
                "過去データ分析",
                "騎手・調教師の詳細統計",
                "オッズ分析",
                "的中率向上支援"
            ]
        }

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


@app.get("/api/rate-limit-status")
async def get_rate_limit_status(request: Request):
    """
    レート制限ステータス取得（デバッグ用）
    現在のIP アドレスの残りリクエスト数を確認
    """
    return rate_limiter.get_remaining_requests(request)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
