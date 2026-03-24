// 競馬AI予想 - フロントエンドアプリケーション（新UI）

document.addEventListener('DOMContentLoaded', () => {
    // グローバル変数
    let selectedDate = null;
    let selectedRace = null;

    // DOM要素
    const raceDateSelect = document.getElementById('race-date');
    const btnNextRaceList = document.getElementById('btn-next-race-list');
    const stepDate = document.getElementById('step-date');
    const stepRace = document.getElementById('step-race');
    const stepHorses = document.getElementById('step-horses');
    const raceList = document.getElementById('race-list');
    const raceInfo = document.getElementById('race-info');
    const horsesTable = document.getElementById('horses-table');
    const btnPredict = document.getElementById('btn-predict');
    const predictionResult = document.getElementById('prediction-result');
    const resultContent = document.getElementById('result-content');

    // 初期化: 利用可能な日付を取得
    loadAvailableDates();

    async function loadAvailableDates() {
        try {
            const response = await fetch('/api/dates');
            const data = await response.json();

            if (data.dates.length === 0) {
                raceDateSelect.innerHTML = '<option value="">直近の開催データがありません</option>';
                return;
            }

            raceDateSelect.innerHTML = '<option value="">開催日を選択してください</option>';
            data.dates.forEach((date, index) => {
                const option = document.createElement('option');
                option.value = date;
                const label = formatDate(date);
                option.textContent = index === 0 ? `${label}（最新開催）` : label;
                raceDateSelect.appendChild(option);
            });

            // 最新日を自動選択
            raceDateSelect.value = data.dates[0];
            selectedDate = data.dates[0];
            btnNextRaceList.disabled = false;
        } catch (error) {
            console.error('Error loading dates:', error);
            raceDateSelect.innerHTML = '<option value="">読み込みエラー</option>';
        }
    }

    // 日付選択時
    raceDateSelect.addEventListener('change', () => {
        selectedDate = raceDateSelect.value;
        btnNextRaceList.disabled = !selectedDate;
    });

    // 次へボタン（レース一覧表示）
    btnNextRaceList.addEventListener('click', async () => {
        if (!selectedDate) return;

        try {
            const response = await fetch(`/api/races/${selectedDate}`);
            const data = await response.json();

            displayRaceList(data.races);
            stepRace.style.display = 'block';
            stepRace.scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            console.error('Error loading races:', error);
            raceList.innerHTML = '<p style="color: red;">レース一覧の読み込みに失敗しました</p>';
        }
    });

    // レース一覧表示
    function displayRaceList(races) {
        raceList.innerHTML = '';

        races.forEach(race => {
            const raceCard = document.createElement('div');
            raceCard.className = 'race-card';

            const raceNum = race.raceInfo.raceNumber;
            const raceName = race.raceInfo.raceName;
            const distance = race.raceInfo.distance;
            const surface = race.raceInfo.surface;
            const startTime = race.raceInfo.startTime;
            const horsesCount = race.horses.length;

            raceCard.innerHTML = `
                <div class="race-card-header">
                    <span class="race-number">${raceNum}</span>
                    <span class="race-time">${startTime}</span>
                </div>
                <div class="race-name">${raceName}</div>
                <div class="race-details">${distance}m ${surface} / ${horsesCount}頭立て</div>
            `;

            raceCard.addEventListener('click', () => selectRace(race));
            raceList.appendChild(raceCard);
        });
    }

    // レース選択
    function selectRace(race) {
        selectedRace = race;
        displayRaceDetail(race);
        stepHorses.style.display = 'block';
        stepHorses.scrollIntoView({ behavior: 'smooth' });
    }

    // レース詳細表示
    function displayRaceDetail(race) {
        const info = race.raceInfo;

        raceInfo.innerHTML = `
            <h4>${info.raceNumber} ${info.raceName}</h4>
            <p>${info.date} ${info.track} ${info.startTime}発走</p>
            <p>${info.distance}m ${info.surface}</p>
        `;

        // 出走馬テーブル
        let tableHTML = `
            <table>
                <thead>
                    <tr>
                        <th>馬番</th>
                        <th>馬名</th>
                        <th>騎手</th>
                        <th>斤量</th>
                    </tr>
                </thead>
                <tbody>
        `;

        race.horses.forEach(horse => {
            tableHTML += `
                <tr>
                    <td><strong>${horse.number}</strong></td>
                    <td>${horse.name}</td>
                    <td>${horse.kisyu}</td>
                    <td>${horse.kinryo}kg</td>
                </tr>
            `;
        });

        tableHTML += `
                </tbody>
            </table>
        `;

        horsesTable.innerHTML = tableHTML;
    }

    // AI予想実行
    btnPredict.addEventListener('click', async () => {
        if (!selectedRace) return;

        try {
            btnPredict.disabled = true;
            btnPredict.textContent = 'AI予想実行中...';

            resultContent.innerHTML = '<p>AI予想を実行中...</p>';
            predictionResult.style.display = 'block';

            const requestData = buildPredictionRequest(selectedRace);

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
            displayPredictionResult(data);

            predictionResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } catch (error) {
            console.error('Error:', error);
            resultContent.innerHTML = `
                <p style="color: red;">エラーが発生しました: ${error.message}</p>
            `;
        } finally {
            btnPredict.disabled = false;
            btnPredict.textContent = 'AI予想を実行';
        }
    });

    // 予想リクエストデータ構築
    function buildPredictionRequest(race) {
        const info = race.raceInfo;
        const venue = info.track;
        const venueCodeMap = {
            '大井': 'OI',
            '川崎': 'KW',
            '船橋': 'FN',
            '浦和': 'UR'
        };

        // 人気は仮で馬番順とする（データに人気情報がない場合）
        const horses = race.horses.map((horse, index) => ({
            number: horse.number,
            name: horse.name,
            popularity: index + 1  // 仮の人気
        }));

        return {
            date: selectedDate,
            venue: venue,
            venue_code: venueCodeMap[venue] || 'OI',
            race_number: parseInt(info.raceNumber.replace('R', '')),
            distance: parseInt(info.distance),
            surface: info.surface,
            horses: horses
        };
    }

    // 予想結果表示
    function displayPredictionResult(data) {
        const predictions = data.predictions;

        let html = '<div class="predictions-list">';

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
        if (data.betting_lines && data.betting_lines.umatan && data.betting_lines.umatan.length > 0) {
            html += `
                <div style="margin-top: 2rem; padding: 1rem; background: white; border-radius: 5px;">
                    <h4 style="margin-bottom: 0.5rem;">推奨買い目（馬単）</h4>
                    <p style="font-size: 1.1rem; color: #667eea; font-weight: 600;">
                        ${data.betting_lines.umatan.join(', ')}
                    </p>
                </div>
            `;
        }

        resultContent.innerHTML = html;
    }

    // 日付フォーマット
    function formatDate(dateStr) {
        const date = new Date(dateStr);
        const month = date.getMonth() + 1;
        const day = date.getDate();
        const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
        const weekday = weekdays[date.getDay()];
        return `${month}月${day}日（${weekday}）`;
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
