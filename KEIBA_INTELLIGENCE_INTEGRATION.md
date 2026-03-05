# keiba-intelligence 連携ガイド

競馬予想AI（keiba-ai-predictor）をkeiba-intelligenceに統合する完全ガイド

## 📋 目次

1. [連携概要](#連携概要)
2. [Netlify Functions セットアップ](#netlify-functions-セットアップ)
3. [環境変数設定](#環境変数設定)
4. [API呼び出し実装](#api呼び出し実装)
5. [フロントエンド統合](#フロントエンド統合)
6. [エラーハンドリング](#エラーハンドリング)
7. [テスト方法](#テスト方法)

---

## 連携概要

### アーキテクチャ

```
keiba-intelligence (Netlify)
  ↓
Netlify Function (Serverless)
  ↓
keiba-ai-predictor API (Render.com)
  ↓
機械学習モデル推論
  ↓
予想結果返却
  ↓
keiba-intelligence 表示
```

### API エンドポイント

**本番URL（Render.com）:**
```
https://keiba-ai-predictor.onrender.com
```

**主要エンドポイント:**
- `GET /health` - ヘルスチェック
- `GET /` - API情報
- `POST /api/predict` - 予想実行
- `GET /api/model-info` - モデル情報取得

---

## Netlify Functions セットアップ

### 1. ディレクトリ構造

keiba-intelligenceプロジェクトに以下を追加:

```
keiba-intelligence/
├── netlify/
│   └── functions/
│       ├── predict-race.js      # 予想API呼び出し
│       └── model-info.js         # モデル情報取得
├── netlify.toml                  # Netlify設定
└── .env                          # 環境変数（ローカル開発用）
```

### 2. netlify.toml 設定

```toml
[build]
  command = "npm run build"
  publish = "dist"
  functions = "netlify/functions"

[functions]
  directory = "netlify/functions"
  node_bundler = "esbuild"

[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200

[dev]
  command = "npm run dev"
  port = 4321
  targetPort = 4321
  autoLaunch = true
```

---

## 環境変数設定

### Netlify ダッシュボード設定

1. Netlify ダッシュボード → Site settings → Environment variables
2. 以下の環境変数を追加:

| Key | Value | 説明 |
|-----|-------|------|
| `AI_API_URL` | `https://keiba-ai-predictor.onrender.com` | AI APIのベースURL |
| `AI_API_TIMEOUT` | `30000` | タイムアウト（ミリ秒） |
| `NODE_ENV` | `production` | 環境 |

### ローカル開発用（.env）

```bash
# .env（keiba-intelligenceルートに作成）
AI_API_URL=https://keiba-ai-predictor.onrender.com
AI_API_TIMEOUT=30000
NODE_ENV=development

# ローカルテスト用（オプション）
# AI_API_URL=http://localhost:8000
```

**重要:** `.env`を`.gitignore`に追加:
```
# .gitignore
.env
.env.local
```

---

## API呼び出し実装

### Netlify Function: predict-race.js

`netlify/functions/predict-race.js` を作成:

```javascript
/**
 * 競馬予想AI 予想実行API
 * POST /api/predict-race
 */

const fetch = require('node-fetch');

const AI_API_URL = process.env.AI_API_URL || 'https://keiba-ai-predictor.onrender.com';
const TIMEOUT = parseInt(process.env.AI_API_TIMEOUT || '30000', 10);

/**
 * タイムアウト付きfetch
 */
async function fetchWithTimeout(url, options, timeout) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

exports.handler = async (event, context) => {
  // CORS設定
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Content-Type': 'application/json'
  };

  // OPTIONS（プリフライト）リクエスト対応
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  // POSTのみ許可
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method Not Allowed' })
    };
  }

  try {
    // リクエストボディ検証
    if (!event.body) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({
          error: 'リクエストボディが空です',
          required_fields: ['date', 'venue', 'race_number', 'horses']
        })
      };
    }

    const requestData = JSON.parse(event.body);

    // 必須フィールド検証
    const requiredFields = ['date', 'venue', 'race_number', 'horses'];
    const missingFields = requiredFields.filter(field => !requestData[field]);

    if (missingFields.length > 0) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({
          error: `必須フィールドが不足しています: ${missingFields.join(', ')}`,
          required_fields: requiredFields
        })
      };
    }

    // AI API呼び出し
    console.log(`AI API呼び出し開始: ${requestData.venue} ${requestData.race_number}R`);

    const response = await fetchWithTimeout(
      `${AI_API_URL}/api/predict`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      },
      TIMEOUT
    );

    // レスポンス検証
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`AI APIエラー (${response.status}): ${errorText}`);

      return {
        statusCode: response.status,
        headers,
        body: JSON.stringify({
          error: 'AI APIからエラーが返されました',
          status: response.status,
          details: errorText
        })
      };
    }

    const predictionData = await response.json();

    console.log(`予想成功: ${predictionData.predictions.length}頭の予想を取得`);

    // 成功レスポンス
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        data: predictionData,
        metadata: {
          date: requestData.date,
          venue: requestData.venue,
          race_number: requestData.race_number,
          timestamp: new Date().toISOString()
        }
      })
    };

  } catch (error) {
    console.error('予想API実行エラー:', error);

    // タイムアウトエラー
    if (error.name === 'AbortError') {
      return {
        statusCode: 504,
        headers,
        body: JSON.stringify({
          error: 'AI APIへの接続がタイムアウトしました',
          details: `${TIMEOUT}ms以内に応答がありませんでした`
        })
      };
    }

    // その他のエラー
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        error: '予想APIの実行中にエラーが発生しました',
        details: error.message
      })
    };
  }
};
```

### Netlify Function: model-info.js

`netlify/functions/model-info.js` を作成:

```javascript
/**
 * 競馬予想AI モデル情報取得API
 * GET /api/model-info
 */

const fetch = require('node-fetch');

const AI_API_URL = process.env.AI_API_URL || 'https://keiba-ai-predictor.onrender.com';
const TIMEOUT = parseInt(process.env.AI_API_TIMEOUT || '10000', 10);

exports.handler = async (event, context) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Content-Type': 'application/json'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  if (event.httpMethod !== 'GET') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method Not Allowed' })
    };
  }

  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), TIMEOUT);

    const response = await fetch(`${AI_API_URL}/api/model-info`, {
      method: 'GET',
      signal: controller.signal
    });

    clearTimeout(id);

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const modelInfo = await response.json();

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify(modelInfo)
    };

  } catch (error) {
    console.error('モデル情報取得エラー:', error);

    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        error: 'モデル情報の取得に失敗しました',
        details: error.message
      })
    };
  }
};
```

---

## フロントエンド統合

### Astroコンポーネント例

`src/components/AIPrediction.astro` を作成:

```astro
---
// 競馬予想AI統合コンポーネント
interface Horse {
  number: number;
  name: string;
  jockey: string;
  trainer: string;
  weight: number;
  jockey_weight: number;
  popularity: number;
  // ... その他フィールド
}

interface Props {
  date: string;
  venue: string;
  raceNumber: number;
  horses: Horse[];
}

const { date, venue, raceNumber, horses } = Astro.props;
---

<div class="ai-prediction-container">
  <h2>🤖 AI予想</h2>

  <button id="predict-btn" class="predict-button">
    AI予想を実行
  </button>

  <div id="prediction-result" class="prediction-result hidden">
    <h3>予想結果</h3>
    <div id="prediction-content"></div>
  </div>

  <div id="prediction-error" class="error-message hidden"></div>
  <div id="prediction-loading" class="loading hidden">
    <span class="spinner"></span>
    予想中...（最大30秒）
  </div>
</div>

<script define:vars={{ date, venue, raceNumber, horses }}>
  const predictBtn = document.getElementById('predict-btn');
  const resultDiv = document.getElementById('prediction-result');
  const contentDiv = document.getElementById('prediction-content');
  const errorDiv = document.getElementById('prediction-error');
  const loadingDiv = document.getElementById('prediction-loading');

  predictBtn.addEventListener('click', async () => {
    // UI初期化
    resultDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');
    predictBtn.disabled = true;

    try {
      // Netlify Functionを呼び出し
      const response = await fetch('/api/predict-race', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          date: date,
          venue: venue,
          race_number: raceNumber,
          horses: horses
        })
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || '予想に失敗しました');
      }

      // 予想結果を表示
      displayPrediction(result.data);

    } catch (error) {
      console.error('予想エラー:', error);
      errorDiv.textContent = `エラー: ${error.message}`;
      errorDiv.classList.remove('hidden');
    } finally {
      loadingDiv.classList.add('hidden');
      predictBtn.disabled = false;
    }
  });

  function displayPrediction(data) {
    const { predictions, betting_lines, confidence } = data;

    // 予想順にソート
    const sortedPredictions = [...predictions].sort((a, b) => a.rank - b.rank);

    // HTML生成
    let html = '<div class="predictions-table">';
    html += '<table>';
    html += '<thead><tr><th>順位</th><th>馬番</th><th>馬名</th><th>役割</th><th>勝率</th></tr></thead>';
    html += '<tbody>';

    sortedPredictions.forEach(pred => {
      html += `
        <tr class="prediction-row">
          <td class="rank">${pred.rank}</td>
          <td class="number">${pred.number}</td>
          <td class="name">${pred.horse_name || '-'}</td>
          <td class="role ${pred.role}">${pred.role}</td>
          <td class="probability">${(pred.win_probability * 100).toFixed(1)}%</td>
        </tr>
      `;
    });

    html += '</tbody></table></div>';

    // 買い目
    if (betting_lines && betting_lines.umatan) {
      html += '<div class="betting-lines">';
      html += '<h4>推奨買い目（馬単）</h4>';
      html += '<ul>';
      betting_lines.umatan.forEach(line => {
        html += `<li>${line}</li>`;
      });
      html += '</ul>';
      html += '</div>';
    }

    // 信頼度
    html += `<div class="confidence">モデル信頼度: ${(confidence * 100).toFixed(1)}%</div>`;

    contentDiv.innerHTML = html;
    resultDiv.classList.remove('hidden');
  }
</script>

<style>
  .ai-prediction-container {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
  }

  .predict-button {
    background: #007bff;
    color: white;
    border: none;
    padding: 12px 24px;
    font-size: 16px;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.3s;
  }

  .predict-button:hover {
    background: #0056b3;
  }

  .predict-button:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }

  .prediction-result {
    margin-top: 20px;
  }

  .predictions-table table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
  }

  .predictions-table th,
  .predictions-table td {
    padding: 10px;
    text-align: left;
    border-bottom: 1px solid #ddd;
  }

  .predictions-table th {
    background: #343a40;
    color: white;
  }

  .role {
    font-weight: bold;
  }

  .role.本命 { color: #dc3545; }
  .role.対抗 { color: #fd7e14; }
  .role.単穴 { color: #ffc107; }
  .role.連下 { color: #6c757d; }

  .betting-lines {
    background: #fff3cd;
    padding: 15px;
    margin: 15px 0;
    border-radius: 4px;
    border-left: 4px solid #ffc107;
  }

  .betting-lines ul {
    list-style: none;
    padding: 0;
  }

  .betting-lines li {
    padding: 5px 0;
    font-weight: bold;
  }

  .confidence {
    text-align: right;
    margin-top: 10px;
    font-size: 14px;
    color: #6c757d;
  }

  .error-message {
    background: #f8d7da;
    color: #721c24;
    padding: 12px;
    border-radius: 4px;
    margin-top: 10px;
  }

  .loading {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 10px;
  }

  .spinner {
    border: 3px solid #f3f3f3;
    border-top: 3px solid #007bff;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .hidden {
    display: none;
  }
</style>
```

### 使用例

```astro
---
// src/pages/race/[venue]/[date]/[race].astro
import AIPrediction from '@/components/AIPrediction.astro';

// レースデータ取得
const { venue, date, race } = Astro.params;
const raceData = await fetchRaceData(venue, date, race);
---

<Layout title={`${venue} ${race}R`}>
  <h1>{venue} {race}R</h1>

  <!-- 既存の出馬表など -->

  <!-- AI予想コンポーネント -->
  <AIPrediction
    date={date}
    venue={venue}
    raceNumber={parseInt(race)}
    horses={raceData.horses}
  />
</Layout>
```

---

## エラーハンドリング

### よくあるエラーと対処法

#### 1. タイムアウトエラー（504）

**原因:** Render.comのCold Start（無料プランでスリープから復帰）

**対処法:**
```javascript
// リトライロジック追加
async function predictWithRetry(data, maxRetries = 2) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch('/api/predict-race', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        return await response.json();
      }

      // 504の場合はリトライ
      if (response.status === 504 && i < maxRetries - 1) {
        console.log(`タイムアウト、リトライ ${i + 1}/${maxRetries - 1}`);
        await sleep(3000); // 3秒待機
        continue;
      }

      throw new Error(`API error: ${response.status}`);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(3000);
    }
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

#### 2. CORS エラー

**原因:** 許可されていないオリジンからのアクセス

**対処法:** AI APIの`src/api/main.py`で許可オリジン追加:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-keiba-intelligence.netlify.app",
        "http://localhost:4321"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 3. 必須フィールド不足（400）

**対処法:** リクエスト前に検証:
```javascript
function validateRaceData(data) {
  const required = ['date', 'venue', 'race_number', 'horses'];
  const missing = required.filter(field => !data[field]);

  if (missing.length > 0) {
    throw new Error(`必須フィールドが不足: ${missing.join(', ')}`);
  }

  if (!Array.isArray(data.horses) || data.horses.length === 0) {
    throw new Error('horsesは1頭以上の配列である必要があります');
  }

  return true;
}
```

---

## テスト方法

### 1. ローカルテスト（Netlify CLI）

```bash
# Netlify CLIインストール
npm install -g netlify-cli

# keiba-intelligenceディレクトリで実行
cd /path/to/keiba-intelligence

# 環境変数設定
echo "AI_API_URL=https://keiba-ai-predictor.onrender.com" > .env

# ローカルサーバー起動
netlify dev

# ブラウザで開く
# http://localhost:8888
```

### 2. Netlify Function 単体テスト

```bash
# curlでテスト
curl -X POST http://localhost:8888/api/predict-race \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-03-05",
    "venue": "大井",
    "race_number": 1,
    "horses": [
      {
        "number": 1,
        "name": "テストホース",
        "jockey": "テスト騎手",
        "trainer": "テスト調教師",
        "weight": 480,
        "jockey_weight": 54,
        "popularity": 1,
        "odds": 2.5,
        "past_races": 10,
        "past_wins": 3,
        "past_places": 5,
        "avg_finish_position": 4.2,
        "jockey_win_rate": 0.15,
        "jockey_place_rate": 0.35,
        "trainer_win_rate": 0.12,
        "trainer_place_rate": 0.30
      }
    ]
  }'
```

### 3. 本番デプロイ後テスト

```bash
# 本番URLでテスト
curl -X POST https://your-site.netlify.app/api/predict-race \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

### 4. ブラウザコンソールテスト

```javascript
// ブラウザのDevToolsコンソールで実行
async function testAIPrediction() {
  const testData = {
    date: "2026-03-05",
    venue: "大井",
    race_number: 1,
    horses: [
      {
        number: 1,
        name: "テストホース",
        jockey: "テスト騎手",
        trainer: "テスト調教師",
        weight: 480,
        jockey_weight: 54,
        popularity: 1,
        odds: 2.5,
        past_races: 10,
        past_wins: 3,
        past_places: 5,
        avg_finish_position: 4.2,
        jockey_win_rate: 0.15,
        jockey_place_rate: 0.35,
        trainer_win_rate: 0.12,
        trainer_place_rate: 0.30
      }
    ]
  };

  const response = await fetch('/api/predict-race', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(testData)
  });

  const result = await response.json();
  console.log('予想結果:', result);
}

testAIPrediction();
```

---

## パフォーマンス最適化

### 1. キャッシング

```javascript
// netlify.toml
[[headers]]
  for = "/api/model-info"
  [headers.values]
    Cache-Control = "public, max-age=3600"  # 1時間キャッシュ

[[headers]]
  for = "/api/predict-race"
  [headers.values]
    Cache-Control = "no-cache"  # 予想結果はキャッシュしない
```

### 2. Cold Start対策

```javascript
// 定期的にヘルスチェックを実行（GitHub Actions等）
// .github/workflows/keep-warm.yml
name: Keep API Warm
on:
  schedule:
    - cron: '*/10 * * * *'  # 10分ごと
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: curl https://keiba-ai-predictor.onrender.com/health
```

### 3. プリフライト最適化

```javascript
// Netlify Functionでプリフライトキャッシュ
const headers = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Max-Age': '86400',  # 24時間
  'Content-Type': 'application/json'
};
```

---

## モニタリング

### ログ確認

```bash
# Netlify Function ログ
netlify functions:log predict-race

# Render.com API ログ
# Render.com ダッシュボード → Logs タブ
```

### エラー追跡

Netlify Functionに簡易ロギング追加:

```javascript
// ログヘルパー
function log(level, message, data = {}) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    level: level,
    message: message,
    ...data
  };
  console.log(JSON.stringify(logEntry));
}

// 使用例
log('info', '予想API呼び出し', { venue, race_number });
log('error', '予想失敗', { error: error.message, stack: error.stack });
```

---

## セキュリティ

### 1. API Key認証（オプション）

AI APIにAPI Key認証を追加する場合:

```javascript
// netlify/functions/predict-race.js
const AI_API_KEY = process.env.AI_API_KEY;

const response = await fetch(`${AI_API_URL}/api/predict`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': AI_API_KEY  // カスタムヘッダー
  },
  body: JSON.stringify(requestData)
});
```

### 2. レート制限

```javascript
// 簡易レート制限（メモリベース）
const requestCounts = new Map();

function checkRateLimit(ip, maxRequests = 10, windowMs = 60000) {
  const now = Date.now();
  const userRequests = requestCounts.get(ip) || [];

  // 古いリクエストを削除
  const recentRequests = userRequests.filter(time => now - time < windowMs);

  if (recentRequests.length >= maxRequests) {
    return false;
  }

  recentRequests.push(now);
  requestCounts.set(ip, recentRequests);
  return true;
}
```

---

## まとめ

### 統合チェックリスト

- [ ] Netlify Functions作成（predict-race.js, model-info.js）
- [ ] netlify.toml設定
- [ ] 環境変数設定（Netlify + .env）
- [ ] フロントエンドコンポーネント実装
- [ ] ローカルテスト（`netlify dev`）
- [ ] 本番デプロイ
- [ ] 本番環境テスト
- [ ] エラーハンドリング確認
- [ ] パフォーマンス最適化

### サポートが必要な場合

**AI API（keiba-ai-predictor）:**
- GitHub: https://github.com/apol0510/keiba-ai-predictor
- 本番URL: https://keiba-ai-predictor.onrender.com

**ドキュメント:**
- API仕様: https://keiba-ai-predictor.onrender.com/docs
- デプロイガイド: RENDER_DEPLOY.md

---

**作成日**: 2026-03-05
**最終更新**: 2026-03-05
