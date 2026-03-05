# 競馬予想API 使い方ガイド

> 🎯 **無料で使える機械学習競馬予想API**
> 誰でも自由に使えるオープンな競馬予想APIです。

## 📋 目次

1. [APIについて](#apiについて)
2. [クイックスタート](#クイックスタート)
3. [エンドポイント一覧](#エンドポイント一覧)
4. [予想APIの使い方](#予想apiの使い方)
5. [レスポンス例](#レスポンス例)
6. [プログラミング言語別サンプル](#プログラミング言語別サンプル)
7. [制限事項](#制限事項)
8. [よくある質問](#よくある質問)

---

## APIについて

### 🤖 何ができる？

- **レース予想**: 出走馬の勝率を機械学習で予測
- **買い目生成**: 馬単の推奨買い目を自動生成
- **役割判定**: 本命・対抗・単穴・連下を自動判定

### 📊 予想精度

- **本命的中率**: 33.01%
- **TOP3的中率**: 61.17%
- **学習データ**: 10,786レース（南関東競馬・JRA中央競馬）

### 💰 料金

**完全無料** - 登録不要、API Key不要

### 🔗 本番URL

```
https://keiba-ai-predictor.onrender.com
```

---

## クイックスタート

### 1. ヘルスチェック（APIが動いているか確認）

```bash
curl https://keiba-ai-predictor.onrender.com/health
```

**レスポンス:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### 2. API情報取得

```bash
curl https://keiba-ai-predictor.onrender.com/
```

### 3. 予想を実行してみる

```bash
curl -X POST https://keiba-ai-predictor.onrender.com/api/predict \
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
      {
        "number": 1,
        "name": "サンプルホース",
        "jockey": "サンプル騎手",
        "trainer": "サンプル調教師",
        "popularity": 1
      }
    ]
  }'
```

---

## エンドポイント一覧

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/` | GET | API情報取得 |
| `/health` | GET | ヘルスチェック |
| `/api/predict` | POST | レース予想実行 |
| `/api/model-info` | GET | モデル情報取得 |
| `/docs` | GET | Swagger UI（対話型ドキュメント） |

---

## 予想APIの使い方

### エンドポイント

```
POST /api/predict
```

### リクエスト形式

**必須フィールド:**

| フィールド | 型 | 説明 | 例 |
|-----------|-------|------|-----|
| `date` | string | 開催日（YYYY-MM-DD） | `"2026-03-05"` |
| `venue` | string | 競馬場名 | `"大井"`, `"東京"` |
| `venue_code` | string | 競馬場コード | `"OI"`, `"TK"` |
| `race_number` | integer | レース番号 | `1` |
| `distance` | integer | 距離（メートル） | `1200` |
| `surface` | string | 馬場種別 | `"ダート"`, `"芝"` |
| `horses` | array | 出走馬リスト | 下記参照 |

**オプションフィールド:**

| フィールド | 型 | デフォルト値 | 説明 |
|-----------|-------|------------|------|
| `weather` | string | `"晴"` | 天候 |
| `track_condition` | string | `"良"` | 馬場状態 |

**出走馬（horses）の形式:**

| フィールド | 型 | 必須 | 説明 |
|-----------|-------|------|------|
| `number` | integer | ✓ | 馬番 |
| `name` | string | ✓ | 馬名 |
| `jockey` | string | | 騎手名 |
| `trainer` | string | | 調教師名 |
| `popularity` | integer | | 人気順位 |

### リクエスト例（完全版）

```json
{
  "date": "2026-03-05",
  "venue": "大井",
  "venue_code": "OI",
  "race_number": 11,
  "distance": 1400,
  "surface": "ダート",
  "weather": "晴",
  "track_condition": "良",
  "horses": [
    {
      "number": 1,
      "name": "スピードスター",
      "jockey": "佐藤太郎",
      "trainer": "山田花子",
      "popularity": 1
    },
    {
      "number": 2,
      "name": "サンダーボルト",
      "jockey": "田中次郎",
      "trainer": "鈴木一郎",
      "popularity": 2
    },
    {
      "number": 3,
      "name": "ライトニング",
      "jockey": "高橋三郎",
      "trainer": "佐々木美咲",
      "popularity": 3
    }
  ]
}
```

---

## レスポンス例

### 成功レスポンス（200 OK）

```json
{
  "predictions": [
    {
      "number": 1,
      "name": "スピードスター",
      "win_probability": 0.352,
      "rank": 1,
      "role": "本命",
      "mark": "◎"
    },
    {
      "number": 2,
      "name": "サンダーボルト",
      "win_probability": 0.281,
      "rank": 2,
      "role": "対抗",
      "mark": "○"
    },
    {
      "number": 3,
      "name": "ライトニング",
      "win_probability": 0.198,
      "rank": 3,
      "role": "単穴",
      "mark": "▲"
    }
  ],
  "betting_lines": {
    "umatan": [
      "1-2.3.4",
      "2-1.3.4"
    ]
  },
  "promotion": {
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
}
```

### エラーレスポンス

#### 400 Bad Request（必須フィールド不足）

```json
{
  "detail": "リクエストボディの検証エラー"
}
```

#### 503 Service Unavailable（モデル未読み込み）

```json
{
  "detail": "モデルが読み込まれていません"
}
```

#### 500 Internal Server Error

```json
{
  "detail": "予想エラー: エラーメッセージ"
}
```

---

## プログラミング言語別サンプル

### JavaScript（ブラウザ）

```javascript
async function predictRace() {
  const raceData = {
    date: "2026-03-05",
    venue: "大井",
    venue_code: "OI",
    race_number: 1,
    distance: 1200,
    surface: "ダート",
    horses: [
      { number: 1, name: "テストホース", popularity: 1 }
    ]
  };

  try {
    const response = await fetch('https://keiba-ai-predictor.onrender.com/api/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(raceData)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log('予想結果:', result);

    // 予想を表示
    result.predictions.forEach(pred => {
      console.log(`${pred.rank}位: ${pred.mark} ${pred.number}番 ${pred.name} (勝率 ${(pred.win_probability * 100).toFixed(1)}%)`);
    });

    // 買い目を表示
    console.log('推奨買い目（馬単）:', result.betting_lines.umatan);

  } catch (error) {
    console.error('エラー:', error);
  }
}

predictRace();
```

### Python

```python
import requests
import json

def predict_race():
    url = 'https://keiba-ai-predictor.onrender.com/api/predict'

    race_data = {
        "date": "2026-03-05",
        "venue": "大井",
        "venue_code": "OI",
        "race_number": 1,
        "distance": 1200,
        "surface": "ダート",
        "horses": [
            {"number": 1, "name": "テストホース", "popularity": 1}
        ]
    }

    try:
        response = requests.post(url, json=race_data, timeout=30)
        response.raise_for_status()

        result = response.json()

        print("予想結果:")
        for pred in result['predictions']:
            print(f"{pred['rank']}位: {pred['mark']} {pred['number']}番 {pred['name']} "
                  f"(勝率 {pred['win_probability'] * 100:.1f}%)")

        print("\n推奨買い目（馬単）:")
        for line in result['betting_lines']['umatan']:
            print(f"  {line}")

    except requests.exceptions.RequestException as e:
        print(f"エラー: {e}")

if __name__ == '__main__':
    predict_race()
```

### Ruby

```ruby
require 'net/http'
require 'json'
require 'uri'

def predict_race
  uri = URI('https://keiba-ai-predictor.onrender.com/api/predict')

  race_data = {
    date: "2026-03-05",
    venue: "大井",
    venue_code: "OI",
    race_number: 1,
    distance: 1200,
    surface: "ダート",
    horses: [
      { number: 1, name: "テストホース", popularity: 1 }
    ]
  }

  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = true

  request = Net::HTTP::Post.new(uri.path, 'Content-Type' => 'application/json')
  request.body = race_data.to_json

  response = http.request(request)

  if response.is_a?(Net::HTTPSuccess)
    result = JSON.parse(response.body)

    puts "予想結果:"
    result['predictions'].each do |pred|
      puts "#{pred['rank']}位: #{pred['mark']} #{pred['number']}番 #{pred['name']} " \
           "(勝率 #{(pred['win_probability'] * 100).round(1)}%)"
    end

    puts "\n推奨買い目（馬単）:"
    result['betting_lines']['umatan'].each do |line|
      puts "  #{line}"
    end
  else
    puts "エラー: #{response.code} #{response.message}"
  end
end

predict_race
```

### PHP

```php
<?php
function predictRace() {
    $url = 'https://keiba-ai-predictor.onrender.com/api/predict';

    $raceData = [
        'date' => '2026-03-05',
        'venue' => '大井',
        'venue_code' => 'OI',
        'race_number' => 1,
        'distance' => 1200,
        'surface' => 'ダート',
        'horses' => [
            ['number' => 1, 'name' => 'テストホース', 'popularity' => 1]
        ]
    ];

    $options = [
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/json',
            'content' => json_encode($raceData),
            'timeout' => 30
        ]
    ];

    $context = stream_context_create($options);
    $response = file_get_contents($url, false, $context);

    if ($response === FALSE) {
        die('エラー: API呼び出しに失敗しました');
    }

    $result = json_decode($response, true);

    echo "予想結果:\n";
    foreach ($result['predictions'] as $pred) {
        printf("%d位: %s %d番 %s (勝率 %.1f%%)\n",
            $pred['rank'],
            $pred['mark'],
            $pred['number'],
            $pred['name'],
            $pred['win_probability'] * 100
        );
    }

    echo "\n推奨買い目（馬単）:\n";
    foreach ($result['betting_lines']['umatan'] as $line) {
        echo "  $line\n";
    }
}

predictRace();
?>
```

---

## 制限事項

### レート制限

現在のところ**レート制限はありません**が、以下のような使い方はご遠慮ください：

- 秒間10リクエスト以上の大量アクセス
- スクレイピング目的の自動リクエスト
- 商用目的での大規模利用

### タイムアウト

- **最大応答時間**: 30秒
- 初回アクセス時はCold Startで時間がかかる場合があります（最大60秒）

### データ制限

- 1リクエストあたり**最大18頭**まで

---

## よくある質問

### Q1: API Keyは必要ですか？

**A:** いいえ、不要です。誰でも自由に使えます。

### Q2: 商用利用は可能ですか？

**A:** 個人的な利用や小規模な利用は問題ありません。大規模な商用利用の場合は事前にご相談ください。

### Q3: 予想の精度はどのくらいですか？

**A:** 本命的中率33.01%です。これは競馬予想AIとしては標準的な精度です。より高精度な予想をお求めの方は [keiba-intelligence](https://keiba-intelligence.netlify.app) をご利用ください。

### Q4: どの競馬場に対応していますか？

**A:** 南関東競馬（大井、川崎、船橋、浦和）とJRA中央競馬（東京、中山など）に対応しています。

### Q5: リアルタイムのオッズデータは使えますか？

**A:** 現在は未対応です。将来のバージョンで追加予定です。

### Q6: エラーが発生します

**A:** 以下を確認してください：
- リクエストボディが正しいJSON形式か
- 必須フィールド（date, venue, venue_code, race_number, distance, surface, horses）が含まれているか
- horses配列が空でないか

### Q7: もっと詳しい分析がしたい

**A:** [keiba-intelligence](https://keiba-intelligence.netlify.app) では以下の機能を提供しています：
- 過去データの詳細分析
- 騎手・調教師の統計情報
- オッズ分析
- 的中率向上支援ツール

---

## サポート

### ドキュメント

- **API仕様書（Swagger UI）**: https://keiba-ai-predictor.onrender.com/docs
- **GitHub**: https://github.com/apol0510/keiba-ai-predictor

### 問い合わせ

バグ報告や機能要望は GitHubのIssuesまでお願いします。

---

## より詳しい予想をお求めの方へ

### keiba-intelligence

このAPIは試作版です。より詳しい予想・分析をお求めの方は、本格的な予想サービス **[keiba-intelligence](https://keiba-intelligence.netlify.app)** をご利用ください。

**主な機能:**
- 過去データの詳細分析
- 騎手・調教師の統計情報
- オッズ分析
- 的中率向上支援ツール
- リアルタイム予想更新

---

**作成日**: 2026-03-05
**最終更新**: 2026-03-05
**バージョン**: 1.0.0
