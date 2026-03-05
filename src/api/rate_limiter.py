"""
レート制限ミドルウェア
無料公開APIとして適切な制限を設ける
"""

from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio


class RateLimiter:
    """
    シンプルなメモリベースのレート制限
    """

    def __init__(
        self,
        requests_per_minute: int = 10,
        requests_per_hour: int = 100,
        requests_per_day: int = 1000
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day

        # IP別のリクエスト履歴
        self.minute_requests = defaultdict(list)
        self.hour_requests = defaultdict(list)
        self.day_requests = defaultdict(list)

        # クリーンアップタスク起動
        asyncio.create_task(self._cleanup_loop())

    def get_client_ip(self, request: Request) -> str:
        """
        クライアントIPアドレス取得
        プロキシ経由の場合はX-Forwarded-Forヘッダーを優先
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def check_rate_limit(self, request: Request) -> None:
        """
        レート制限チェック
        制限を超えている場合は HTTPException を発生
        """
        ip = self.get_client_ip(request)
        now = datetime.now()

        # 古いリクエストを削除
        self._cleanup_old_requests(ip, now)

        # 各時間枠でチェック
        minute_count = len(self.minute_requests[ip])
        hour_count = len(self.hour_requests[ip])
        day_count = len(self.day_requests[ip])

        # 1分あたりの制限チェック
        if minute_count >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "レート制限を超過しました",
                    "limit": f"{self.requests_per_minute}リクエスト/分",
                    "retry_after": 60,
                    "message": "1分後に再試行してください"
                }
            )

        # 1時間あたりの制限チェック
        if hour_count >= self.requests_per_hour:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "レート制限を超過しました",
                    "limit": f"{self.requests_per_hour}リクエスト/時間",
                    "retry_after": 3600,
                    "message": "1時間後に再試行してください"
                }
            )

        # 1日あたりの制限チェック
        if day_count >= self.requests_per_day:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "レート制限を超過しました",
                    "limit": f"{self.requests_per_day}リクエスト/日",
                    "retry_after": 86400,
                    "message": "明日再試行してください"
                }
            )

        # リクエストを記録
        self.minute_requests[ip].append(now)
        self.hour_requests[ip].append(now)
        self.day_requests[ip].append(now)

    def _cleanup_old_requests(self, ip: str, now: datetime) -> None:
        """
        古いリクエスト履歴を削除
        """
        # 1分以上前のリクエストを削除
        one_minute_ago = now - timedelta(minutes=1)
        self.minute_requests[ip] = [
            t for t in self.minute_requests[ip] if t > one_minute_ago
        ]

        # 1時間以上前のリクエストを削除
        one_hour_ago = now - timedelta(hours=1)
        self.hour_requests[ip] = [
            t for t in self.hour_requests[ip] if t > one_hour_ago
        ]

        # 1日以上前のリクエストを削除
        one_day_ago = now - timedelta(days=1)
        self.day_requests[ip] = [
            t for t in self.day_requests[ip] if t > one_day_ago
        ]

    async def _cleanup_loop(self) -> None:
        """
        定期的にメモリをクリーンアップ（1時間ごと）
        """
        while True:
            await asyncio.sleep(3600)  # 1時間待機

            now = datetime.now()
            one_day_ago = now - timedelta(days=1)

            # 1日以上アクセスのないIPを削除
            for storage in [self.minute_requests, self.hour_requests, self.day_requests]:
                ips_to_remove = []
                for ip, timestamps in storage.items():
                    if not timestamps or all(t < one_day_ago for t in timestamps):
                        ips_to_remove.append(ip)

                for ip in ips_to_remove:
                    del storage[ip]

    def get_remaining_requests(self, request: Request) -> dict:
        """
        残りリクエスト数を取得（デバッグ用）
        """
        ip = self.get_client_ip(request)
        now = datetime.now()

        self._cleanup_old_requests(ip, now)

        return {
            "per_minute": {
                "limit": self.requests_per_minute,
                "used": len(self.minute_requests[ip]),
                "remaining": self.requests_per_minute - len(self.minute_requests[ip])
            },
            "per_hour": {
                "limit": self.requests_per_hour,
                "used": len(self.hour_requests[ip]),
                "remaining": self.requests_per_hour - len(self.hour_requests[ip])
            },
            "per_day": {
                "limit": self.requests_per_day,
                "used": len(self.day_requests[ip]),
                "remaining": self.requests_per_day - len(self.day_requests[ip])
            }
        }
