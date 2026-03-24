"""
毎日の予想記事自動生成
keiba-data-sharedからレース情報を取得し、AI予想を実行して記事を生成
"""

import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

# フォールバック探索日数（当日含まず）
FALLBACK_MAX_DAYS = 7


class DailyPredictionAutomation:
    """毎日の予想を自動生成"""

    def __init__(
        self,
        api_base_url: str = "http://localhost:8000",
        data_api_url: str = "https://keiba-data-shared.netlify.app/nankan/predictions"
    ):
        self.api_base_url = api_base_url
        self.data_api_url = data_api_url

    def _build_race_url(self, date_str: str) -> str:
        """日付文字列からレースデータURLを構築"""
        year, month = date_str.split('-')[0], date_str.split('-')[1]
        return f"{self.data_api_url}/{year}/{month}/{date_str}.json"

    async def _fetch_races_for_date(self, date_str: str) -> Optional[Dict]:
        """指定日付のレースデータを取得（単一日付）"""
        url = self._build_race_url(date_str)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if data and 'races' in data:
                        return data
                    else:
                        print(f"  ⚠️  レスポンスにracesフィールドがありません: {date_str}")
                elif response.status_code == 404:
                    pass  # データなし（正常系）
                else:
                    print(f"  ⚠️  HTTPステータス {response.status_code}: {date_str}")
        except httpx.TimeoutException:
            print(f"  ⚠️  タイムアウト: {date_str}")
        except Exception as e:
            print(f"  ⚠️  レースデータ取得エラー ({date_str}): {e}")
        return None

    async def get_today_races(self) -> Optional[Dict]:
        """本日のレース一覧を取得（後方互換）"""
        today = datetime.now().strftime('%Y-%m-%d')
        return await self._fetch_races_for_date(today)

    async def get_races_with_fallback(self, fallback_days: int = FALLBACK_MAX_DAYS) -> Tuple[Optional[Dict], str, bool]:
        """
        レースデータをフォールバック付きで取得

        Returns:
            (races_data, adopted_date, is_fallback)
            - races_data: レースデータ or None
            - adopted_date: 採用した日付文字列
            - is_fallback: フォールバックデータを使用したか
        """
        today = datetime.now().strftime('%Y-%m-%d')

        # 当日データ取得
        today_url = self._build_race_url(today)
        print(f"  📡 当日データ取得URL: {today_url}")
        data = await self._fetch_races_for_date(today)
        if data:
            print(f"  ✅ 当日データ取得成功: {today}")
            return data, today, False

        # 当日データなし → フォールバック探索
        print(f"  ⚠️  当日 ({today}) のレースデータが見つかりません")
        print(f"  🔍 フォールバック探索開始: 過去{fallback_days}日分を検索します...")

        for days_back in range(1, fallback_days + 1):
            target_date = datetime.now() - timedelta(days=days_back)
            date_str = target_date.strftime('%Y-%m-%d')
            print(f"  🔍 探索中: {date_str} ({days_back}日前)")

            data = await self._fetch_races_for_date(date_str)
            if data:
                print(f"  ✅ フォールバックデータ採用: {date_str} ({days_back}日前)")
                return data, date_str, True

        # すべて失敗
        print(f"  ❌ 直近{fallback_days}日以内に利用可能なレースデータが見つかりません")
        return None, today, False

    async def predict_race(self, race: Dict) -> Optional[Dict]:
        """レースの予想を実行"""
        race_info = race['raceInfo']
        horses = race['horses']

        # 予想リクエスト構築
        venue_code_map = {
            '大井': 'OI',
            '川崎': 'KW',
            '船橋': 'FN',
            '浦和': 'UR'
        }

        request_data = {
            'date': race_info['date'],
            'venue': race_info['track'],
            'venue_code': venue_code_map.get(race_info['track'], 'OI'),
            'race_number': int(race_info['raceNumber'].replace('R', '')),
            'distance': int(race_info['distance']),
            'surface': race_info['surface'],
            'horses': [
                {
                    'number': h['number'],
                    'name': h['name'],
                    'popularity': idx + 1  # 仮の人気順
                }
                for idx, h in enumerate(horses)
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/predict",
                    json=request_data,
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"予想実行エラー: {e}")

        return None

    async def generate_article_content(self, top_n: int = 3) -> Dict:
        """
        記事コンテンツを生成（CMS公開は別処理）

        このメソッドは記事の内容を生成するだけです。
        実際のCMS公開やRSS反映は別の責務として分離されています。

        Returns:
            success=True: 記事生成成功
            success=False, skip=True: データなし（正常スキップ）
            success=False, skip=False: 異常エラー
        """
        # 1. レースデータ取得（フォールバック付き）
        races_data, adopted_date, is_fallback = await self.get_races_with_fallback()

        if not races_data:
            return {
                'success': False,
                'skip': True,
                'message': f'直近{FALLBACK_MAX_DAYS}日以内に利用可能なレースデータが見つかりません'
            }

        # 採用日付を日本語形式に変換
        date_obj = datetime.strptime(adopted_date, '%Y-%m-%d')
        date_str_jp = date_obj.strftime('%Y年%m月%d日')

        races = races_data['races'][:top_n]  # 注目レース（最初の3レース）
        track = races_data.get('track', '南関東')

        if is_fallback:
            print(f"  📌 フォールバックデータ使用: {adopted_date} ({track})")

        # 2. 各レースの予想実行
        predictions = []
        for race in races:
            pred = await self.predict_race(race)
            if pred:
                predictions.append({
                    'race': race,
                    'prediction': pred
                })

        # 3. 記事本文生成
        article_content = self.create_article_markdown(
            track, date_str_jp, predictions
        )

        return {
            'success': True,
            'skip': False,
            'date': adopted_date,
            'track': track,
            'title': f'{date_str_jp} {track}競馬 AI予想',
            'content': article_content,
            'predictions': predictions,
            'summary': f'{track}競馬の注目{len(predictions)}レースをAIが予想。的中率33%の機械学習モデルによる本命・対抗馬を公開。',
            'is_fallback': is_fallback,
            'adopted_date': adopted_date,
        }

    async def generate_daily_article(self, top_n: int = 3) -> Dict:
        """
        後方互換性のため残す（generate_article_content()を使用推奨）
        """
        return await self.generate_article_content(top_n)

    def create_article_markdown(
        self, track: str, date_str: str, predictions: List[Dict]
    ) -> str:
        """Markdown形式の記事を生成"""

        md = f"""# {date_str} {track}競馬 AI予想

機械学習モデル（的中率33.01%）による本日の予想です。

"""

        for idx, pred_data in enumerate(predictions, 1):
            race = pred_data['race']['raceInfo']
            prediction = pred_data['prediction']

            # 本命・対抗・単穴を抽出
            horses = sorted(
                prediction['predictions'],
                key=lambda x: x['win_probability'],
                reverse=True
            )[:3]

            honmei = horses[0] if len(horses) > 0 else None
            taikou = horses[1] if len(horses) > 1 else None
            tanana = horses[2] if len(horses) > 2 else None

            md += f"""## {race['raceNumber']} {race['raceName']}

**レース情報**
- 距離: {race['distance']}m
- 馬場: {race['surface']}
- 発走: {race['startTime']}

**AI予想**

"""

            if honmei:
                md += f"- ◎本命: {honmei['number']}番 {honmei['name']} (勝率 {honmei['win_probability']*100:.1f}%)\n"

            if taikou:
                md += f"- ○対抗: {taikou['number']}番 {taikou['name']} (勝率 {taikou['win_probability']*100:.1f}%)\n"

            if tanana:
                md += f"- ▲単穴: {tanana['number']}番 {tanana['name']} (勝率 {tanana['win_probability']*100:.1f}%)\n"

            # 買い目
            if 'betting_lines' in prediction and prediction['betting_lines'].get('umatan'):
                md += f"\n**推奨買い目（馬単）**\n"
                md += f"- {', '.join(prediction['betting_lines']['umatan'])}\n"

            md += "\n---\n\n"

        md += f"""
## AI予想を試す

詳しい予想は [keiba-ai-predictor](https://keiba-ai-predictor.onrender.com) で無料公開中！

より本格的な予想・分析は [keiba-intelligence](https://keiba-intelligence.netlify.app) へ。
"""

        return md


# テスト実行
if __name__ == '__main__':
    import asyncio

    async def test():
        automation = DailyPredictionAutomation()
        article = await automation.generate_daily_article()

        if article['success']:
            print("=" * 60)
            print(article['title'])
            print("=" * 60)
            print(article['content'])
            print("=" * 60)
            print(f"\n記事の要約: {article['summary']}")
        else:
            print(f"エラー: {article['message']}")

    asyncio.run(test())
