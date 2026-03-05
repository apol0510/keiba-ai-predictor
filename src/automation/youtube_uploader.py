"""
YouTube自動投稿
Google YouTube Data API v3を使用して動画をアップロード
"""

import os
import json
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


class YouTubeUploader:
    """YouTube API経由で自動投稿"""

    # OAuth 2.0スコープ
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    def __init__(self, credentials_file: str = 'credentials/youtube_credentials.json',
                 token_file: str = 'credentials/youtube_token.json'):
        """
        初期化

        Args:
            credentials_file: OAuth 2.0クライアント認証情報ファイル
            token_file: 保存されたトークンファイル
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.youtube = None

        self._authenticate()

    def _authenticate(self):
        """YouTube API認証"""
        creds = None

        # 保存されたトークンがあれば読み込む
        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as token:
                creds_info = json.load(token)
                creds = Credentials.from_authorized_user_info(creds_info, self.SCOPES)

        # 有効なクレデンシャルがなければ、新規認証
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"OAuth 2.0 credentials not found: {self.credentials_file}\n"
                        f"Please download from Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # トークンを保存
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())

        # YouTube APIクライアント構築
        self.youtube = build('youtube', 'v3', credentials=creds)
        print("✅ YouTube API認証成功")

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list = None,
        category_id: str = '17',  # Sports
        privacy_status: str = 'public'
    ) -> Optional[str]:
        """
        動画をアップロード

        Args:
            video_path: 動画ファイルパス
            title: 動画タイトル
            description: 動画説明文
            tags: タグリスト
            category_id: カテゴリID（17=Sports）
            privacy_status: 公開設定（public/private/unlisted）

        Returns:
            アップロードされた動画のURL（失敗時はNone）
        """
        if tags is None:
            tags = ['競馬', 'AI予想', '南関東競馬', '地方競馬', '機械学習']

        body = {
            'snippet': {
                'title': title,
                'description': description + '\n\n🔗 詳しくはこちら\nhttps://keiba-ai-predictor.onrender.com',
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }

        # 動画ファイルのアップロード準備
        media = MediaFileUpload(
            video_path,
            chunksize=-1,  # 一括アップロード
            resumable=True
        )

        try:
            print(f"📤 YouTube へアップロード中: {title}")

            # アップロード実行
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"  進行状況: {int(status.progress() * 100)}%")

            video_id = response['id']
            video_url = f"https://youtube.com/watch?v={video_id}"

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
if __name__ == '__main__':
    # 認証テスト
    try:
        uploader = YouTubeUploader()
        uploader.get_channel_info()

        print("\n✅ YouTube API認証OK")
        print("本番実行時は upload_video() を呼び出してください")

    except FileNotFoundError as e:
        print(f"\n❌ 認証情報が見つかりません")
        print(f"{e}")
        print("\n【セットアップ手順】")
        print("1. Google Cloud Console でプロジェクト作成")
        print("2. YouTube Data API v3 を有効化")
        print("3. OAuth 2.0 クライアントID作成（デスクトップアプリ）")
        print("4. credentials.json をダウンロード")
        print("5. credentials/youtube_credentials.json に配置")
