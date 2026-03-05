// 競馬AI予想 - フロントエンドアプリケーション

document.addEventListener('DOMContentLoaded', () => {
    // DOM要素の取得
    const predictionForm = document.getElementById('prediction-form');
    const addHorseBtn = document.getElementById('add-horse-btn');
    const horsesList = document.getElementById('horses-list');
    const predictionResult = document.getElementById('prediction-result');
    const resultContent = document.getElementById('result-content');

    // 競馬場コードマッピング
    const venueCodeMap = {
        '大井': 'OI',
        '川崎': 'KW',
        '船橋': 'FN',
        '浦和': 'UR'
    };

    // 馬を追加
    addHorseBtn.addEventListener('click', () => {
        const horseRow = document.createElement('div');
        horseRow.className = 'horse-row';
        horseRow.innerHTML = `
            <input type="number" placeholder="馬番" min="1" required>
            <input type="number" placeholder="人気" min="1" required>
        `;
        horsesList.appendChild(horseRow);
    });

    // フォーム送信処理
    predictionForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // フォームデータの取得
        const venue = document.getElementById('venue').value;
        const distance = parseInt(document.getElementById('distance').value);
        const surface = document.getElementById('surface').value;

        // 出走馬情報の取得
        const horseRows = document.querySelectorAll('.horse-row');
        const horses = Array.from(horseRows).map((row, index) => {
            const inputs = row.querySelectorAll('input');
            return {
                number: parseInt(inputs[0].value),
                name: `${inputs[0].value}番馬`,  // 馬名は自動生成
                popularity: parseInt(inputs[1].value)
            };
        }).filter(horse => horse.number && horse.popularity);

        if (horses.length === 0) {
            alert('少なくとも1頭の馬情報を入力してください');
            return;
        }

        // APIリクエストデータ
        const requestData = {
            date: new Date().toISOString().split('T')[0],
            venue: venue,
            venue_code: venueCodeMap[venue] || 'OI',
            race_number: 1,
            distance: distance,
            surface: surface,
            horses: horses
        };

        try {
            // ローディング表示
            resultContent.innerHTML = '<p>AI予想を実行中...</p>';
            predictionResult.style.display = 'block';

            // API呼び出し
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error('予想の実行に失敗しました');
            }

            const data = await response.json();

            // 結果の表示
            displayPredictionResult(data);

        } catch (error) {
            console.error('Error:', error);
            resultContent.innerHTML = `
                <p style="color: red;">エラーが発生しました: ${error.message}</p>
                <p>もう一度お試しください。</p>
            `;
        }
    });

    // 予想結果の表示
    function displayPredictionResult(data) {
        const predictions = data.predictions;
        const bettingLines = data.betting_lines;

        let html = '<div class="predictions-list">';

        // 各馬の予想結果
        predictions.forEach((pred, index) => {
            const percentage = (pred.win_probability * 100).toFixed(1);
            html += `
                <div class="prediction-item">
                    <div class="horse-info">
                        <span class="horse-mark">${pred.mark}</span>
                        <div>
                            <div class="horse-name">${pred.number}番 ${pred.name}</div>
                            <div style="color: #666; font-size: 0.9rem;">${pred.role}</div>
                        </div>
                    </div>
                    <div class="win-prob">${percentage}%</div>
                </div>
            `;
        });

        html += '</div>';

        // 買い目提案
        if (bettingLines && bettingLines.umatan && bettingLines.umatan.length > 0) {
            html += `
                <div style="margin-top: 2rem; padding: 1rem; background: white; border-radius: 5px;">
                    <h4 style="margin-bottom: 0.5rem;">推奨買い目（馬単）</h4>
                    <p style="font-size: 1.1rem; color: #667eea; font-weight: 600;">
                        ${bettingLines.umatan.join(', ')}
                    </p>
                </div>
            `;
        }

        resultContent.innerHTML = html;

        // 結果までスクロール
        predictionResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // スムーススクロール
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});
