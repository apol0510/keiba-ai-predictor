# 競馬予想AI - Production Dockerfile

FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# システム依存関係インストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係をコピー（本番環境用）
COPY requirements-prod.txt .

# Python依存関係インストール（軽量版）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# アプリケーションコードをコピー
COPY src/ ./src/
COPY models/ ./models/
COPY static/ ./static/

# 非rootユーザー作成
RUN useradd -m -u 1000 keiba && \
    chown -R keiba:keiba /app

USER keiba

# ポート公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# アプリケーション起動（本番環境：軽量化のため1ワーカー）
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
