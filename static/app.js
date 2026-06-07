/**
 * AI English Speaking Coach - Frontend logic
 * Features: Chat, scenarios, speech, streaks, easter eggs
 */

(function () {
    "use strict";

    const chatArea = document.getElementById("chat-area");
    const userInput = document.getElementById("user-input");
    const btnSend = document.getElementById("btn-send");
    const btnReset = document.getElementById("btn-reset");
    const scenarioBar = document.getElementById("scenario-bar");
    const welcomeCard = document.getElementById("welcome-card");

    let currentScenario = "restaurant";
    let conversationHistory = [];
    let isSending = false;
    let recognition = null;
    let isRecording = false;
    let consecutiveCorrect = 0;
    let consecutiveErrors = 0;
    let sessionStartTime = Date.now();
    let sessionWordCount = 0;
    let sessionErrorCount = 0;
    let isCustomScenario = false;
    let customScenarioData = null;

    // Easter egg keywords
    const EASTER_EGGS = {
        birthday: ["birthday", "happy birthday", "happy bday"],
        thankyou: ["thank you", "thanks", "thankyou"],
        goodbye: ["goodbye", "bye", "see you", "see ya"]
    };

    // Load streak data from localStorage
    function loadStreakData() {
        const today = new Date().toISOString().split('T')[0];
        const data = localStorage.getItem('speaking_streak');
        if (data) {
            return JSON.parse(data);
        }
        return {
            currentStreak: 0,
            longestStreak: 0,
            lastDate: null,
            records: {},
            wrongWords: [],
            badges: []
        };
    }

    function saveStreakData(data) {
        localStorage.setItem('speaking_streak', JSON.stringify(data));
    }

    function checkStreak() {
        const today = new Date().toISOString().split('T')[0];
        const streak = loadStreakData();
        
        if (!streak.lastDate) {
            streak.currentStreak = 1;
            streak.lastDate = today;
        } else if (streak.lastDate === today) {
            // Already checked in today
        } else {
            const lastDate = new Date(streak.lastDate);
            const todayDate = new Date(today);
            const diffDays = Math.floor((todayDate - lastDate) / (1000 * 60 * 60 * 24));
            
            if (diffDays === 1) {
                streak.currentStreak++;
                if (streak.currentStreak > streak.longestStreak) {
                    streak.longestStreak = streak.currentStreak;
                }
            } else {
                streak.currentStreak = 1;
            }
            streak.lastDate = today;
        }
        
        if (!streak.records[today]) {
            streak.records[today] = { messages: 0, errors: 0, duration: 0 };
        }
        
        saveStreakData(streak);
        updateStreakUI();
    }

    function updateStreakUI() {
        const streak = loadStreakData();
        const streakBadge = document.getElementById('streak-badge');
        const headerStreakBadge = document.getElementById('header-streak-badge');
        if (streakBadge) {
            streakBadge.innerHTML = `🔥 ${streak.currentStreak}天`;
            streakBadge.title = `最长连续打卡: ${streak.longestStreak}天`;
        }
        if (headerStreakBadge) {
            headerStreakBadge.innerHTML = `🔥 ${streak.currentStreak}天`;
            headerStreakBadge.title = `最长连续打卡: ${streak.longestStreak}天`;
        }
    }

    function addWrongWord(word) {
        const streak = loadStreakData();
        if (!streak.wrongWords.includes(word.toLowerCase())) {
            streak.wrongWords.push(word.toLowerCase());
            saveStreakData(streak);
        }
    }

    function triggerEasterEgg(type) {
        switch(type) {
            case 'birthday':
                createFallingEmojis(['🎂', '🎁', '🎈', '🎉', '🎊']);
                break;
            case 'thankyou':
                createFallingEmojis(['❤️', '💕', '💖', '💗', '💝']);
                break;
            case 'goodbye':
                createWaveAnimation();
                break;
        }
    }

    function createFallingEmojis(emojis) {
        const container = document.createElement('div');
        container.className = 'easter-egg-container';
        document.body.appendChild(container);

        for (let i = 0; i < 15; i++) {
            const emoji = document.createElement('span');
            emoji.className = 'falling-emoji';
            emoji.textContent = emojis[Math.floor(Math.random() * emojis.length)];
            emoji.style.left = Math.random() * 100 + '%';
            emoji.style.animationDelay = Math.random() * 2 + 's';
            emoji.style.fontSize = (16 + Math.random() * 12) + 'px';
            container.appendChild(emoji);
        }

        setTimeout(() => {
            container.remove();
        }, 5000);
    }

    function createWaveAnimation() {
        const wave = document.createElement('div');
        wave.className = 'wave-animation';
        wave.innerHTML = '👋 Bye! Have a great day!';
        document.body.appendChild(wave);

        setTimeout(() => {
            wave.remove();
        }, 3000);
    }

    function checkEasterEggs(text) {
        const lower = text.toLowerCase();
        for (const [type, keywords] of Object.entries(EASTER_EGGS)) {
            if (keywords.some(kw => lower.includes(kw))) {
                triggerEasterEgg(type);
                break;
            }
        }
    }

    function updateMouseCursor() {
        if (consecutiveCorrect >= 3) {
            document.body.style.cursor = 'url("data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'32\' height=\'32\' viewBox=\'0 0 32 32\'><text y=\'.9em\' font-size=\'24\'>📚</text></svg>"), auto';
        } else if (consecutiveErrors >= 5) {
            document.body.style.cursor = 'url("data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'32\' height=\'32\' viewBox=\'0 0 32 32\'><text y=\'.9em\' font-size=\'24\'>❓</text></svg>"), auto';
        } else {
            document.body.style.cursor = 'default';
        }
    }

    async function init() {
        await loadScenarios();
        await loadStats();
        bindEvents();
        initSpeechRecognition();
        checkStreak();
        initSidebar();
    }

    async function loadScenarios() {
        try {
            const res = await fetch("/api/scenarios");
            const data = await res.json();
            renderScenarioButtons(data.scenarios);
        } catch (err) {
            console.error("Failed to load scenarios:", err);
        }
    }

    async function loadStats() {
        try {
            const res = await fetch("/api/stats");
            const data = await res.json();
            renderStats(data);
        } catch (err) {
            console.error("Failed to load stats:", err);
        }
    }

    function renderStats(stats) {
        const statsEl = document.createElement("div");
        statsEl.className = "stats-bar";
        statsEl.innerHTML = `
            <div class="stat-item">
                <span class="stat-value">${stats.today.today_messages}</span>
                <span class="stat-label">今日练习</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
                <span class="stat-value">${stats.today.today_accuracy}%</span>
                <span class="stat-label">正确率</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
                <span class="stat-value">${stats.total.total_messages}</span>
                <span class="stat-label">累计练习</span>
            </div>
        `;
        
        const header = document.querySelector(".header");
        if (header) {
            const existingStats = header.querySelector(".stats-bar");
            if (existingStats) existingStats.remove();
            header.appendChild(statsEl);
        }
    }

    function renderScenarioButtons(scenarios) {
        scenarioBar.innerHTML = "";
        scenarios.forEach((s) => {
            const btn = document.createElement("button");
            btn.className = "scenario-btn" + (s.id === currentScenario ? " active" : "");
            btn.dataset.id = s.id;
            btn.innerHTML = s.name;
            btn.title = s.description;
            btn.addEventListener("click", () => switchScenario(s));
            scenarioBar.appendChild(btn);
        });
    }

    async function switchScenario(scenario) {
        if (scenario.id === currentScenario && !isCustomScenario) return;

        currentScenario = scenario.id;
        conversationHistory = [];
        isCustomScenario = false;
        customScenarioData = null;

        scenarioBar.querySelectorAll(".scenario-btn").forEach((btn) => {
            btn.classList.toggle("active", btn.dataset.id === currentScenario);
        });

        await fetch("/api/reset", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ scenario_id: currentScenario }),
        });

        clearChat();
        appendMessage("ai", scenario.opening);
        conversationHistory.push({ role: "assistant", content: scenario.opening });
    }

    async function sendMessage(text = null) {
        const userText = text || userInput.value.trim();
        if (!userText || isSending) return;

        isSending = true;
        btnSend.disabled = true;
        userInput.value = "";
        autoResize();

        if (welcomeCard) welcomeCard.style.display = "none";

        appendMessage("user", userText);
        conversationHistory.push({ role: "user", content: userText });

        checkEasterEggs(userText);

        const typingEl = showTyping();

        try {
            const requestBody = {
                message: userText,
                scenario_id: currentScenario,
                history: conversationHistory.slice(-10),
            };
            
            if (isCustomScenario && customScenarioData) {
                requestBody.custom_persona = customScenarioData.persona;
                requestBody.custom_scenario_name = customScenarioData.name;
            }
            
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestBody),
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || "Request failed");
            }

            removeTyping(typingEl);

            const hasErrors = data.grammar?.has_errors || false;
            if (hasErrors) {
                consecutiveCorrect = 0;
                consecutiveErrors++;
                sessionErrorCount++;
                
                data.grammar.issues?.forEach(issue => {
                    if (issue.original) addWrongWord(issue.original);
                });
            } else {
                consecutiveCorrect++;
                consecutiveErrors = 0;
            }
            
            sessionWordCount++;
            updateMouseCursor();

            appendMessage("ai", data.reply, {
                correction: data.correction,
                encouragement: data.encouragement,
                grammar: data.grammar,
            });
            conversationHistory.push({ role: "assistant", content: data.reply });

            speakText(data.reply);
            await loadStats();
            updateDailyRecord();
            updatePKScore(!hasErrors);

        } catch (err) {
            removeTyping(typingEl);
            appendMessage("ai", "Sorry, something went wrong. Please try again.");
            console.error(err);
        } finally {
            isSending = false;
            btnSend.disabled = false;
            userInput.focus();
        }
    }

    function updateDailyRecord() {
        const streak = loadStreakData();
        const today = new Date().toISOString().split('T')[0];
        
        if (!streak.records[today]) {
            streak.records[today] = { messages: 0, errors: 0, duration: 0 };
        }
        
        streak.records[today].messages++;
        streak.records[today].errors += sessionErrorCount;
        streak.records[today].duration = Math.floor((Date.now() - sessionStartTime) / 1000);
        
        saveStreakData(streak);
        checkBadges();
    }

    function checkBadges() {
        const streak = loadStreakData();
        const today = new Date().toISOString().split('T')[0];
        const todayRecord = streak.records[today];
        
        // Check for badges
        if (todayRecord && todayRecord.messages >= 10 && !streak.badges.includes('first_10')) {
            streak.badges.push('first_10');
            showBadgeNotification('🏅 首次完成10句练习！');
        }
        
        if (streak.currentStreak >= 7 && !streak.badges.includes('week_streak')) {
            streak.badges.push('week_streak');
            showBadgeNotification('🔥 连续打卡7天！');
        }
        
        if (streak.wrongWords.length >= 20 && !streak.badges.includes('vocab_master')) {
            streak.badges.push('vocab_master');
            showBadgeNotification('📖 收集20个生词！');
        }
        
        saveStreakData(streak);
    }

    function showBadgeNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'badge-notification';
        notification.innerHTML = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    function appendMessage(role, text, extras = {}) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${role}`;

        const bubble = document.createElement("div");
        bubble.className = "bubble";
        bubble.textContent = text;
        msgDiv.appendChild(bubble);

        const hasErrors = extras.grammar?.has_errors || false;
        
        if (hasErrors) {
            const grammarCard = document.createElement("div");
            grammarCard.className = "grammar-card";
            
            const errorCount = extras.grammar?.error_count || 0;
            const issues = extras.grammar?.issues || [];
            
            let issuesHtml = '';
            if (issues.length > 0) {
                issuesHtml = issues.map((issue) => {
                    const levelConfig = {
                        'format': { label: '🔤', bg: '#E6F2FF', color: '#1E90FF' },
                        'word': { label: '🟠', bg: '#FFF3E6', color: '#FF8C00' },
                        'grammar': { label: '📗', bg: '#E6FFEF', color: '#32CD32' }
                    };
                    const config = levelConfig[issue.level] || levelConfig['format'];
                    return `
                        <div class="grammar-issue">
                            <span class="issue-tag" style="background:${config.bg};color:${config.color};">${config.label}</span>
                            <span class="issue-desc">${issue.description}</span>
                            ${issue.suggestion && issue.suggestion !== issue.original ? `<span class="issue-arrow">→</span><span class="issue-suggest">${issue.suggestion}</span>` : ''}
                        </div>
                    `;
                }).join('');
            }
            
            const correctedText = extras.correction?.replace(/\*\*/g, '') || '';
            const encouragement = extras.encouragement || '';
            
            const originalText = extras.grammar?.original || '';
            let finalSentence = '';
            
            if (originalText) {
                finalSentence = originalText;
                
                issues.forEach(issue => {
                    if (issue.original && issue.suggestion && issue.suggestion !== issue.original) {
                        if (issue.original === '(句末)') {
                            if (!finalSentence.endsWith('.') && !finalSentence.endsWith('?') && !finalSentence.endsWith('!')) {
                                finalSentence += issue.suggestion;
                            }
                        } else {
                            const regex = new RegExp(issue.original, 'gi');
                            finalSentence = finalSentence.replace(regex, issue.suggestion);
                        }
                    }
                });
            }
            
            grammarCard.innerHTML = `
                <div class="grammar-header">
                    <span class="grammar-icon">✏️</span>
                    <span class="grammar-title">Grammar Feedback</span>
                    <span class="grammar-error-count">共${errorCount}处错误</span>
                    <button class="apply-correction-btn" onclick="applyCorrection('${finalSentence.replace(/'/g, "\\'")}')">📋 一键填入</button>
                    <span class="grammar-toggle" onclick="toggleGrammarCard(this.parentElement.parentElement)">▲</span>
                </div>
                <div class="grammar-content">
                    ${issuesHtml}
                    ${finalSentence && originalText ? `
                    <div class="grammar-suggestion">
                        <span class="suggestion-original">${originalText}</span>
                        <span class="suggestion-arrow">→</span>
                        <span class="suggestion-corrected">${finalSentence}</span>
                    </div>
                    ` : ''}
                    ${encouragement ? `
                    <div class="grammar-encouragement">💬 ${encouragement}</div>
                    ` : ''}
                </div>
            `;
            msgDiv.appendChild(grammarCard);
        } else if (extras.encouragement) {
            const card = document.createElement("div");
            card.className = "encourage-card";
            card.innerHTML = `<span class="encourage-icon">💪</span> ${extras.encouragement}`;
            msgDiv.appendChild(card);
        }

        chatArea.appendChild(msgDiv);
        scrollToBottom();
    }

    function showTyping() {
        const el = document.createElement("div");
        el.className = "message ai";
        el.innerHTML =
            '<div class="bubble typing-indicator"><span></span><span></span><span></span></div>';
        chatArea.appendChild(el);
        scrollToBottom();
        return el;
    }

    function removeTyping(el) {
        if (el && el.parentNode) el.parentNode.removeChild(el);
    }

    function clearChat() {
        chatArea.innerHTML = "";
        if (welcomeCard) {
            chatArea.appendChild(welcomeCard);
            welcomeCard.style.display = "none";
        }
        conversationHistory = [];
        sessionStartTime = Date.now();
        sessionWordCount = 0;
        sessionErrorCount = 0;
    }

    function scrollToBottom() {
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function initSpeechRecognition() {
        if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
            console.log("Speech recognition not supported");
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "en-US";

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript.trim();
            if (transcript) {
                userInput.value = transcript;
                sendMessage(transcript);
            }
            isRecording = false;
            updateMicButton();
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            isRecording = false;
            updateMicButton();
        };

        recognition.onend = () => {
            if (isRecording) {
                recognition.start();
            }
        };

        const micBtn = document.createElement("button");
        micBtn.id = "btn-mic";
        micBtn.className = "btn-mic";
        micBtn.innerHTML = "🎤";
        micBtn.title = "语音输入";
        micBtn.addEventListener("click", toggleRecording);
        
        const inputWrapper = document.querySelector(".input-wrapper");
        if (inputWrapper) {
            inputWrapper.insertBefore(micBtn, userInput);
        }
    }

    function toggleRecording() {
        if (isRecording) {
            try {
                recognition.stop();
            } catch (e) {
                console.warn("Error stopping recognition:", e);
            }
            isRecording = false;
        } else {
            try {
                recognition.start();
                isRecording = true;
            } catch (e) {
                console.error("Error starting recognition:", e);
                isRecording = false;
            }
        }
        updateMicButton();
    }

    function updateMicButton() {
        const micBtn = document.getElementById("btn-mic");
        if (micBtn) {
            micBtn.classList.toggle("recording", isRecording);
        }
    }

    function speakText(text) {
        if (!("speechSynthesis" in window)) {
            console.log("Text-to-speech not supported");
            return;
        }

        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = "en-US";
        utterance.rate = 0.9;
        utterance.pitch = 1;
        
        window.speechSynthesis.speak(utterance);
    }

    function initSidebar() {
        const sidebar = document.createElement('div');
        sidebar.className = 'sidebar';
        sidebar.id = 'sidebar';
        
        sidebar.innerHTML = `
            <div class="sidebar-header">
                <h3>📊 My Progress</h3>
                <button id="sidebar-toggle" class="sidebar-toggle">▶</button>
            </div>
            <div class="sidebar-content">
                <div class="pk-section">
                    <button id="btn-create-pk" class="pk-btn">🎮 创建PK房间</button>
                    <button id="btn-join-pk" class="pk-btn">🤝 加入PK</button>
                    <div id="pk-code-display" class="pk-code-display" style="display: none;"></div>
                    <div id="pk-scoreboard" class="pk-scoreboard" style="display: none;"></div>
                </div>
                <div class="quick-stats">
                    <div class="quick-stat">
                        <span class="quick-value">${loadStreakData().wrongWords.length}</span>
                        <span class="quick-label">生词本</span>
                    </div>
                    <div class="quick-stat">
                        <span class="quick-value">${loadStreakData().badges.length}</span>
                        <span class="quick-label">勋章</span>
                    </div>
                </div>
                <div class="calendar-section">
                    <h4>📅 打卡日历</h4>
                    <div id="calendar-grid" class="calendar-grid"></div>
                </div>
                <div class="badges-section">
                    <h4>🏆 我的勋章</h4>
                    <div id="badges-grid" class="badges-grid"></div>
                </div>
                <div class="wrong-words-section">
                    <h4>📖 生词本</h4>
                    <div id="wrong-words-list" class="wrong-words-list"></div>
                </div>
            </div>
        `;
        
        const app = document.querySelector('.app');
        const mainContent = document.querySelector('.main-content');
        app.insertBefore(sidebar, mainContent);
        
        document.getElementById('sidebar-toggle').addEventListener('click', toggleSidebar);
        document.getElementById('btn-create-pk').addEventListener('click', createPKRoom);
        document.getElementById('btn-join-pk').addEventListener('click', joinPKRoom);
        renderCalendar();
        renderBadges();
        renderWrongWords();
        initPKSession();
    }
    
    let pkSession = null;
    
    function initPKSession() {
        const saved = localStorage.getItem('pk_session');
        if (saved) {
            try {
                pkSession = JSON.parse(saved);
                if (pkSession && pkSession.code) {
                    showPKCode(pkSession.code);
                }
            } catch (e) {
                pkSession = null;
            }
        }
    }
    
    function generatePKCode() {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        let code = '';
        for (let i = 0; i < 6; i++) {
            code += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return code;
    }
    
    function createPKRoom() {
        const code = generatePKCode();
        pkSession = {
            code: code,
            isHost: true,
            player1: { name: '我', score: 0, errors: 0, messages: 0 },
            player2: null,
            startTime: Date.now()
        };
        localStorage.setItem('pk_session', JSON.stringify(pkSession));
        showPKCode(code);
        showPKScoreboard();
    }
    
    function joinPKRoom() {
        const code = prompt('请输入PK口令：').toUpperCase();
        if (!code || code.length !== 6) {
            alert('请输入6位有效口令');
            return;
        }
        
        pkSession = {
            code: code,
            isHost: false,
            player1: null,
            player2: { name: '我', score: 0, errors: 0, messages: 0 },
            startTime: Date.now()
        };
        localStorage.setItem('pk_session', JSON.stringify(pkSession));
        showPKCode(code);
        showPKScoreboard();
        alert(`已加入PK房间 ${code}，等待对手开始练习！`);
    }
    
    function showPKCode(code) {
        const display = document.getElementById('pk-code-display');
        display.innerHTML = `
            <div class="pk-code-label">🎮 PK口令</div>
            <div class="pk-code">${code}</div>
            <button id="btn-copy-pk" class="copy-pk-btn">📋 复制口令</button>
            <button id="btn-leave-pk" class="leave-pk-btn">🚪 离开房间</button>
        `;
        display.style.display = 'block';
        
        document.getElementById('btn-copy-pk').addEventListener('click', () => {
            navigator.clipboard.writeText(code);
            alert('口令已复制到剪贴板！');
        });
        
        document.getElementById('btn-leave-pk').addEventListener('click', () => {
            leavePKRoom();
        });
    }
    
    function showPKScoreboard() {
        const scoreboard = document.getElementById('pk-scoreboard');
        if (!pkSession) return;
        
        const p1 = pkSession.player1 || { name: '等待中...', score: 0, errors: 0, messages: 0 };
        const p2 = pkSession.player2 || { name: '等待中...', score: 0, errors: 0, messages: 0 };
        
        scoreboard.innerHTML = `
            <div class="pk-score-title">⚔️ PK对战</div>
            <div class="pk-player ${pkSession.isHost ? 'current' : ''}">
                <span class="pk-player-name">${p1.name}</span>
                <span class="pk-player-score">${p1.score}分</span>
                <span class="pk-player-detail">${p1.messages}句 · ${p1.errors}错误</span>
            </div>
            <div class="pk-vs">VS</div>
            <div class="pk-player ${!pkSession.isHost ? 'current' : ''}">
                <span class="pk-player-name">${p2.name}</span>
                <span class="pk-player-score">${p2.score}分</span>
                <span class="pk-player-detail">${p2.messages}句 · ${p2.errors}错误</span>
            </div>
        `;
        scoreboard.style.display = 'block';
    }
    
    function updatePKScore(isCorrect) {
        if (!pkSession) return;
        
        const player = pkSession.isHost ? pkSession.player1 : pkSession.player2;
        if (!player) return;
        
        player.messages++;
        if (isCorrect) {
            player.score += 10;
        } else {
            player.errors++;
            player.score = Math.max(0, player.score - 2);
        }
        
        localStorage.setItem('pk_session', JSON.stringify(pkSession));
        showPKScoreboard();
    }
    
    function leavePKRoom() {
        pkSession = null;
        localStorage.removeItem('pk_session');
        document.getElementById('pk-code-display').style.display = 'none';
        document.getElementById('pk-scoreboard').style.display = 'none';
    }

    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.getElementById('sidebar-toggle');
        sidebar.classList.toggle('collapsed');
        toggle.innerHTML = sidebar.classList.contains('collapsed') ? '▶' : '◀';
    }

    function renderCalendar() {
        const calendar = document.getElementById('calendar-grid');
        const streak = loadStreakData();
        const today = new Date();
        const currentMonth = today.getMonth();
        const currentYear = today.getFullYear();
        const firstDay = new Date(currentYear, currentMonth, 1);
        const lastDay = new Date(currentYear, currentMonth + 1, 0);
        
        let html = `<div class="calendar-month-header">${currentYear}年${currentMonth + 1}月</div>`;
        html += '<div class="calendar-header">';
        const days = ['日', '一', '二', '三', '四', '五', '六'];
        days.forEach(d => html += `<div class="calendar-day-name">${d}</div>`);
        html += '</div><div class="calendar-days">';
        
        for (let i = 0; i < firstDay.getDay(); i++) {
            html += '<div class="calendar-day empty"></div>';
        }
        
        let completedDays = 0;
        for (let i = 1; i <= lastDay.getDate(); i++) {
            const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
            const record = streak.records[dateStr];
            const isToday = i === today.getDate();
            
            let className = 'calendar-day';
            let tooltip = '';
            let emoji = '';
            
            if (isToday) className += ' today';
            if (record) {
                if (record.messages >= 5) {
                    className += ' completed';
                    emoji = '✅';
                    completedDays++;
                } else if (record.messages > 0) {
                    className += ' partial';
                    emoji = '⚡';
                }
                tooltip = `练习${record.messages}句，时长${record.duration}秒`;
            }
            
            html += `<div class="${className}" title="${tooltip}">${i}${emoji}</div>`;
        }
        
        html += '</div>';
        html += `<div class="calendar-summary">本月打卡 ${completedDays}/${lastDay.getDate()} 天</div>`;
        calendar.innerHTML = html;
    }

    function renderBadges() {
        const badgesGrid = document.getElementById('badges-grid');
        const streak = loadStreakData();
        
        const badgeDefinitions = {
            first_10: { icon: '🏅', name: '初露锋芒' },
            week_streak: { icon: '🔥', name: '一周坚持' },
            vocab_master: { icon: '📖', name: '词汇达人' },
            first_day: { icon: '🌱', name: '第一天' }
        };
        
        let html = '';
        Object.entries(badgeDefinitions).forEach(([key, badge]) => {
            const unlocked = streak.badges.includes(key);
            html += `<div class="badge-item ${unlocked ? '' : 'locked'}">
                <span class="badge-icon">${unlocked ? badge.icon : '🔒'}</span>
                <span class="badge-name">${unlocked ? badge.name : '???'}</span>
            </div>`;
        });
        
        badgesGrid.innerHTML = html;
    }

    function renderWrongWords() {
        const list = document.getElementById('wrong-words-list');
        const streak = loadStreakData();
        
        if (streak.wrongWords.length === 0) {
            list.innerHTML = '<p class="empty-message">暂无生词，继续练习！</p>';
            return;
        }
        
        let html = '';
        streak.wrongWords.slice(0, 10).forEach(word => {
            html += `<div class="wrong-word-item">${word}</div>`;
        });
        
        if (streak.wrongWords.length > 10) {
            html += `<p class="more-words">还有 ${streak.wrongWords.length - 10} 个生词...</p>`;
        }
        
        list.innerHTML = html;
    }

    function bindEvents() {
        btnSend.addEventListener("click", sendMessage);

        userInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        userInput.addEventListener("input", autoResize);

        btnReset.addEventListener("click", async () => {
            const confirmed = confirm('确定要重置当前对话吗？\n\n注意：这只会清空当前对话，您的学习记录（打卡、生词本等）将被保留。');
            if (!confirmed) return;
            
            clearChat();
            if (welcomeCard) welcomeCard.style.display = "block";

            await fetch("/api/reset", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ scenario_id: currentScenario }),
            });

            const activeBtn = scenarioBar.querySelector(".scenario-btn.active");
            if (activeBtn) {
                const scenarios = await (await fetch("/api/scenarios")).json();
                const s = scenarios.scenarios.find((sc) => sc.id === currentScenario);
                if (s) {
                    appendMessage("ai", s.opening);
                    conversationHistory.push({ role: "assistant", content: s.opening });
                }
            }
        });
    }

    function autoResize() {
        userInput.style.height = "auto";
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + "px";
    }

    function initCustomScenario() {
        const customBtn = document.getElementById('btn-custom-scenario');
        const modal = document.getElementById('custom-scenario-modal');
        const closeBtn = modal.querySelector('.close-modal');
        const cancelBtn = modal.querySelector('.btn-cancel');
        const confirmBtn = modal.querySelector('.btn-confirm');

        customBtn.addEventListener('click', () => {
            modal.style.display = 'flex';
        });

        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });

        cancelBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });

        confirmBtn.addEventListener('click', startCustomScenario);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }

    async function startCustomScenario() {
        const name = document.getElementById('scenario-name').value.trim();
        const persona = document.getElementById('scenario-persona').value.trim();
        const opening = document.getElementById('scenario-opening').value.trim();
        const description = document.getElementById('scenario-description').value.trim();

        if (!name || !persona || !opening) {
            alert('请填写场景名称、AI角色和开场白！');
            return;
        }

        isCustomScenario = true;
        currentScenario = 'custom';
        customScenarioData = {
            id: 'custom',
            name: name,
            name_en: name,
            persona: persona,
            opening: opening,
            description: description
        };

        document.getElementById('custom-scenario-modal').style.display = 'none';
        clearChat();

        await fetch("/api/reset", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ scenario_id: 'custom' }),
        });

        appendMessage("ai", opening);
        conversationHistory.push({ role: "assistant", content: opening });
    }

    init();
    initCustomScenario();
})();

function toggleGrammarCard(card) {
    const content = card.querySelector('.grammar-content');
    const toggle = card.querySelector('.grammar-toggle');
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        toggle.textContent = '▼';
    } else {
        content.style.display = 'none';
        toggle.textContent = '▶';
    }
}

function applyCorrection(text) {
    const userInput = document.getElementById('user-input');
    if (userInput && text) {
        userInput.value = text;
        userInput.focus();
    }
}
