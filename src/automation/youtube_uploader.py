"""
YouTube自動投稿（CI対応版）
GitHub Actions等のCI環境で動作する設計
"""

import os
import json
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader:
    """YouTube API経由で動画投稿（CI対応）"""

    def __init__(
        self,
        credentials_file: str = "credentials/youtube_credentials.json",
        token_file: str = "credentials/youtube_token.json",
    ):
        """
        初期化

        Args:
            credentials_file: OAuth 2.0クライアント認証情報ファイル（使用しない）
            token_file: 保存されたトークンファイル（必須）

        Note:
            CI環境では token_file が必須。
            初回認証は init_youtube_auth.py をローカルで実行。
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.youtube = self._build_client()

    def _load_credentials(self) -> Credentials:
        """保存されたトークンファイルから認証情報を読み込む"""
        if not os.path.exists(self.token_file):
            raise FileNotFoundError(
                f"\n❌ Token file not found: {self.token_file}\n\n"
                "初回認証をローカルで実行してください:\n"
                "  python src/automation/init_youtube_auth.py\n\n"
                "CI環境の場合:\n"
                "  GitHub Secrets に YOUTUBE_TOKEN_JSON を登録してください\n"
            )

        with open(self.token_file, "r", encoding="utf-8") as f:
            token_info = json.load(f)

        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

        # トークン有効期限切れの場合は自動リフレッシュ
        if creds.expired and creds.refresh_token:
            print("🔄 トークンをリフレッシュ中...")
            creds.refresh(Request())

            # リフレッシュ後のトークンを保存
            Path(os.path.dirname(self.token_file)).mkdir(parents=True, exist_ok=True)
            with open(self.token_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            print("✅ トークンをリフレッシュしました")

        if not creds.valid:
            raise RuntimeError(
                "YouTube credentials are invalid.\n"
                "ローカルで再認証して youtube_token.json を更新してください:\n"
                "  python src/automation/init_youtube_auth.py"
            )

        return creds

    def _build_client(self):
        """YouTube APIクライアントを構築"""
        creds = self._load_credentials()
        return build("youtube", "v3", credentials=creds)

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list = None,
        category_id: str = "17",  # Sports
        privacy_status: str = "private",  # 本番前はprivate推奨
    ) -> Optional[str]:
        """
        動画をアップロード

        Args:
            video_path: 動画ファイルパス
            title: 動画タイトル（最大100文字）
            description: 動画説明文（最大5000文字）
            tags: タグリスト
            category_id: カテゴリID（17=Sports）
            privacy_status: 公開設定（public/private/unlisted）
                           本番前はprivateでテスト推奨

        Returns:
            アップロードされた動画のURL（失敗時はNone）
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        if tags is None:
            tags = ["競馬", "AI予想", "地方競馬", "南関東競馬", "機械学習"]

        body = {
            "snippet": {
                "title": title[:100],  # YouTube上限
                "description": (description + "\n\n🔗 詳しくはこちら\nhttps://keiba-ai-predictor.onrender.com")[:5000],
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(video_path, resumable=True)

        try:
            print(f"📤 YouTube へアップロード中: {title}")
            print(f"   公開設定: {privacy_status}")

            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"  進行状況: {int(status.progress() * 100)}%")

            video_id = response["id"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            print(f"✅ アップロード完了: {video_url}")
            return video_url

        except HttpError as e:
            print(f"❌ YouTubeアップロードエラー: {e}")
            return None

    def get_channel_info(self):
        """チャンネル情報を取得（デバッグ用）"""
        try:
            request = self.youtube.channels().list(
                part='snippet,statistics',
                mine=True
            )
            response = request.execute()

            if 'items' in response and len(response['items']) > 0:
                channel = response['items'][0]
                print(f"チャンネル名: {channel['snippet']['title']}")
                print(f"登録者数: {channel['statistics']['subscriberCount']}")
                print(f"総再生数: {channel['statistics']['viewCount']}")
                return channel
        except HttpError as e:
            print(f"❌ チャンネル情報取得エラー: {e}")

        return None


# テスト実行
if __name__ == "__main__":
    try:
        uploader = YouTubeUploader()
        uploader.get_channel_info()

        print("\n✅ YouTube API認証OK")
        print("動画アップロードの準備が完了しています")

    except FileNotFoundError as e:
        print(f"\n❌ トークンファイルが見つかりません")
        print(f"{e}")
