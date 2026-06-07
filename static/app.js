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

    // ===== 语音管理模块 =====
    const SpeechManager = {
        currentUtterance: null,
        currentMsgElement: null,
        isPaused: false,

        speak(text, msgElement = null, rate = 0.9) {
            if (!("speechSynthesis" in window)) return;
            
            this.stop();
            
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = "en-US";
            utterance.rate = rate;
            utterance.pitch = 1;
            
            this.currentUtterance = utterance;
            if (msgElement) this.currentMsgElement = msgElement;
            this.isPaused = false;
            
            utterance.onend = () => {
                this.resetPlayButton(msgElement);
                this.currentUtterance = null;
                this.currentMsgElement = null;
                this.isPaused = false;
            };
            
            utterance.onerror = () => {
                this.resetPlayButton(msgElement);
                this.currentUtterance = null;
                this.currentMsgElement = null;
                this.isPaused = false;
            };
            
            window.speechSynthesis.speak(utterance);
        },

        togglePause(msgElement) {
            if (!this.currentUtterance || this.currentMsgElement !== msgElement) {
                const text = msgElement?.closest('.message')?.querySelector('.bubble')?.textContent || '';
                if (text) this.speak(text, msgElement, 0.9);
                return;
            }
            
            if (this.isPaused) {
                window.speechSynthesis.resume();
                this.isPaused = false;
                this.updatePlayButton(msgElement, true);
            } else {
                window.speechSynthesis.pause();
                this.isPaused = true;
                this.updatePlayButton(msgElement, false);
            }
        },

        speakSlow(text) {
            this.stop();
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = "en-US";
            utterance.rate = 0.7;
            utterance.pitch = 1;
            window.speechSynthesis.speak(utterance);
        },

        stop() {
            window.speechSynthesis.cancel();
            if (this.currentMsgElement) {
                this.resetPlayButton(this.currentMsgElement);
            }
            this.currentUtterance = null;
            this.currentMsgElement = null;
            this.isPaused = false;
        },

        updatePlayButton(element, isPlaying) {
            if (!element) return;
            const btn = element.querySelector('.btn-play');
            if (btn) btn.textContent = isPlaying ? '⏸️' : '▶️';
        },

        resetPlayButton(element) {
            if (!element) return;
            const btn = element.querySelector('.btn-play');
            if (btn) btn.textContent = '▶️';
        },

        speakWord(word) {
            this.stop();
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(word);
            utterance.lang = "en-US";
            utterance.rate = 0.85;
            utterance.pitch = 1;
            window.speechSynthesis.speak(utterance);
        }
    };

    // ===== 词典API缓存模块 =====
    const DictionaryCache = {
        cache: {},
        
        async lookup(word) {
            const cleanWord = word.toLowerCase().trim().replace(/[^a-zA-Z-]/g, '');
            if (!cleanWord || cleanWord.length < 2) return null;
            
            if (this.cache[cleanWord]) {
                return this.cache[cleanWord];
            }
            
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);
                
                const response = await fetch(
                    `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(cleanWord)}`,
                    { signal: controller.signal }
                );
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    this.cache[cleanWord] = { error: true };
                    return null;
                }
                
                const data = await response.json();
                if (data && data.length > 0) {
                    const entry = data[0];
                    const meanings = entry.meanings || [];
                    const definitions = [];
                    meanings.forEach(m => {
                        (m.definitions || []).slice(0, 2).forEach(d => {
                            if (d.definition) definitions.push(d.definition);
                        });
                    });
                    
                    const phonetic = entry.phonetic || 
                        (entry.phonetics && entry.phonetics.find(p => p.text)?.text) || '';
                    
                    const result = {
                        word: entry.word,
                        phonetic,
                        definitions: definitions.slice(0, 3),
                        error: false
                    };
                    
                    this.cache[cleanWord] = result;
                    return result;
                }
                
                this.cache[cleanWord] = { error: true };
                return null;
            } catch (e) {
                console.warn('Dictionary API error:', e.message);
                this.cache[cleanWord] = { error: true };
                return null;
            }
        }
    };

    // ===== 单词弹窗模块 =====
    let wordClickDebounce = null;
    
    function showWordModal(word, sentence) {
        if (wordClickDebounce) clearTimeout(wordClickDebounce);
        wordClickDebounce = setTimeout(async () => {
            _showWordModalInternal(word, sentence);
        }, 200);
    }

    async function _showWordModalInternal(word, sentence) {
        const existingModal = document.getElementById('word-modal');
        if (existingModal) existingModal.remove();

        const modal = document.createElement('div');
        modal.id = 'word-modal';
        modal.className = 'word-modal-overlay';
        modal.innerHTML = `
            <div class="word-modal-content">
                <button class="word-modal-close" onclick="document.getElementById('word-modal').remove()">✕</button>
                <div class="word-modal-header">
                    <span class="word-modal-word">${escapeHtml(word)}</span>
                    <button class="word-modal-speak-btn" title="发音">🔈</button>
                </div>
                <div class="word-modal-body">
                    <div class="word-modal-loading">正在查询释义...</div>
                </div>
                ${sentence ? `<div class="word-modal-example"><strong>例句：</strong>"${escapeHtml(sentence)}"</div>` : ''}
                <div class="word-modal-actions">
                    <button class="word-modal-add-btn" id="modal-add-vocab">📚 添加到生词本</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const speakBtn = modal.querySelector('.word-modal-speak-btn');
        speakBtn.addEventListener('click', () => SpeechManager.speakWord(word));

        const addBtn = document.getElementById('modal-add-vocab');
        addBtn.addEventListener('click', () => addToVocabularyFromModal(word, sentence, modal));

        const dictResult = await DictionaryCache.lookup(word);
        const bodyEl = modal.querySelector('.word-modal-body');

        if (dictResult && !dictResult.error && dictResult.definitions.length > 0) {
            bodyEl.innerHTML = `
                ${dictResult.phonetic ? `<div class="word-modal-phonetic">${escapeHtml(dictResult.phonetic)}</div>` : ''}
                <div class="word-modal-definitions">
                    ${dictResult.definitions.map(d => `<p>${escapeHtml(d)}</p>`).join('')}
                </div>
            `;
        } else {
            bodyEl.innerHTML = '<div class="word-modal-no-def">暂无释义</div>';
        }

        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }

    async function addToVocabularyFromModal(word, sentence, modal) {
        try {
            const res = await fetch('/api/vocabulary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    word,
                    definition: '',
                    example: sentence || '',
                    source: '对话学习'
                })
            });
            
            const result = await res.json();
            
            if (result.success === false && result.error?.includes('已存在')) {
                alert('该单词已在生词本中！');
            } else if (result.id || result.word) {
                const btn = document.getElementById('modal-add-vocab');
                if (btn) {
                    btn.textContent = '✅ 已添加';
                    btn.disabled = true;
                    btn.style.opacity = '0.6';
                }
                renderVocabulary();
            }
        } catch (e) {
            console.error('Add vocabulary error:', e);
            alert('添加失败，请重试');
        }
    }

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
                if (!streak.records[streak.lastDate] || (streak.records[streak.lastDate] && streak.records[streak.lastDate].messages === 0)) {
                    streak.records[streak.lastDate] = { messages: 1, errors: 0, duration: 0, checkedIn: true };
                }
            } else if (diffDays > 1) {
                streak.currentStreak = 1;
            } else {
                streak.currentStreak = 1;
            }
            streak.lastDate = today;
        }
        
        if (!streak.records[today]) {
            streak.records[today] = { messages: 0, errors: 0, duration: 0 };
        }
        
        _repairStreakConsistency(streak);
        saveStreakData(streak);
        updateStreakUI();
    }

    function _repairStreakConsistency(streak) {
        if (streak.currentStreak >= 2 && streak.lastDate) {
            const date = new Date(streak.lastDate);
            for (let i = 1; i < streak.currentStreak; i++) {
                date.setDate(date.getDate() - 1);
                const dateStr = date.toISOString().split('T')[0];
                if (!streak.records[dateStr] || (streak.records[dateStr] && streak.records[dateStr].messages === 0)) {
                    streak.records[dateStr] = { messages: 1, errors: 0, duration: 0, checkedIn: true };
                }
            }
        }
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
        const cleanWord = word.trim().toLowerCase();
        
        if (!cleanWord || cleanWord.length < 2) return;
        if (!/^[a-zA-Z]+$/.test(cleanWord)) return;
        if (['the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from',
            'up', 'about', 'into', 'over', 'after'].includes(cleanWord)) return;
        
        fetch('/api/vocabulary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: cleanWord, source: '练习' })
        }).then(() => renderVocabulary()).catch(() => {});
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
        initTodoPanel();
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
        const userText = (typeof text === 'string' ? text : null) || userInput.value.trim();
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
                    if (issue.original && issue.original !== issue.suggestion && 
                        issue.level !== 'format' && 
                        issue.original !== '(句末)' &&
                        !/^[^a-zA-Z]+$/.test(issue.original)) {
                        addWrongWord(issue.original);
                    }
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
        
        if (_vocabCache.length >= 20 && !streak.badges.includes('vocab_master')) {
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
        
        if (role === 'ai') {
            bubble.innerHTML = makeWordsClickable(text);
            bubble.addEventListener('click', handleWordClick);
        } else {
            bubble.textContent = text;
        }
        
        msgDiv.appendChild(bubble);

        if (role === 'ai') {
            const audioControls = document.createElement('div');
            audioControls.className = 'audio-controls';
            audioControls.innerHTML = `
                <button class="btn-play" title="播放/暂停">▶️</button>
                <button class="btn-slow" title="慢速播放 (0.7x)">🐢</button>
            `;
            
            const playBtn = audioControls.querySelector('.btn-play');
            const slowBtn = audioControls.querySelector('.btn-slow');
            
            playBtn.addEventListener('click', () => SpeechManager.togglePause(audioControls));
            slowBtn.addEventListener('click', () => SpeechManager.speakSlow(text));
            
            msgDiv.appendChild(audioControls);
        }

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
            let finalSentence = extras.grammar?.corrected_text || '';

            // 后端 corrected_text 优先；旧版 API 无该字段时回退到前端拼接
            if (!finalSentence && originalText) {
                finalSentence = originalText;
                const punctuationIssues = [];
                const otherIssues = [];

                issues.forEach(issue => {
                    if (issue.original && issue.suggestion && issue.suggestion !== issue.original) {
                        if (issue.original === '(句末)' || issue.original === '(句末无标点)' || issue.level === 'format') {
                            punctuationIssues.push(issue);
                        } else {
                            otherIssues.push(issue);
                        }
                    }
                });

                otherIssues.forEach(issue => {
                    const escaped = issue.original.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    const regex = new RegExp(escaped, 'i');
                    finalSentence = finalSentence.replace(regex, issue.suggestion);
                });

                punctuationIssues.forEach(issue => {
                    if (issue.original === '(句末)' || issue.original === '(句末无标点)') {
                        finalSentence = finalSentence.replace(/[,;:]+$/, '');
                        if (!finalSentence.endsWith('.') && !finalSentence.endsWith('?') && !finalSentence.endsWith('!')) {
                            finalSentence += issue.suggestion;
                        }
                    } else if (issue.level === 'format') {
                        const escaped = issue.original.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                        const regex = new RegExp(escaped, 'i');
                        finalSentence = finalSentence.replace(regex, issue.suggestion);
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
            SpeechManager.stop();
            window.speechSynthesis.cancel();
            
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

    function makeWordsClickable(text) {
        return text.replace(/\b([a-zA-Z]{2,})\b/g, '<span class="clickable-word" data-word="$1">$1</span>');
    }

    function handleWordClick(e) {
        const wordEl = e.target.closest('.clickable-word');
        if (!wordEl) return;
        
        e.stopPropagation();
        
        const word = wordEl.dataset.word;
        const bubble = wordEl.closest('.bubble');
        const sentence = bubble ? bubble.textContent : '';
        
        showWordModal(word, sentence);
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
                <button id="sidebar-toggle" class="sidebar-toggle">◀</button>
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
                        <span class="quick-value" id="vocab-count">0</span>
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
                    <div class="vocab-header">
                        <h4>📖 生词本</h4>
                        <div class="vocab-actions">
                            <button id="btn-add-vocab" class="vocab-btn" title="添加生词">➕</button>
                            <button id="btn-export-csv" class="vocab-btn" title="导出CSV">📥</button>
                            <button id="btn-export-txt" class="vocab-btn" title="导出TXT">📄</button>
                        </div>
                    </div>
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
        
        const btnAddVocab = document.getElementById('btn-add-vocab');
        if (btnAddVocab) btnAddVocab.addEventListener('click', () => showAddVocabModal());
        const btnExportCsv = document.getElementById('btn-export-csv');
        if (btnExportCsv) btnExportCsv.addEventListener('click', () => exportVocab('csv'));
        const btnExportTxt = document.getElementById('btn-export-txt');
        if (btnExportTxt) btnExportTxt.addEventListener('click', () => exportVocab('txt'));
        
        renderCalendar();
        renderBadges();
        renderVocabulary();
        initPKSession();
    }

    // ===== 待办清单模块 =====
    const TODO_STORAGE_KEY = 'todo_list';
    let todoItems = [];

    function initTodoPanel() {
        const rightPanel = document.createElement('div');
        rightPanel.className = 'right-panel';
        rightPanel.id = 'right-panel';
        
        rightPanel.innerHTML = `
            <div class="todo-header">
                <h3>📝 To Do List</h3>
                <button id="todo-toggle" class="todo-toggle">▶</button>
            </div>
            <div class="todo-content">
                <div class="todo-stats">
                    <span>共 <span class="todo-count" id="todo-total-count">0</span> 项</span>
                    <span>已完成 <span class="todo-count" id="todo-completed-count">0</span> 项</span>
                </div>
                <div class="todo-input-area">
                    <input type="text" class="todo-input" id="todo-input" placeholder="添加新待办..." maxlength="100">
                    <button class="todo-add-btn" id="todo-add-btn" title="添加">+</button>
                </div>
                <ul class="todo-list" id="todo-list"></ul>
            </div>
        `;
        
        const app = document.querySelector('.app');
        app.appendChild(rightPanel);
        
        document.getElementById('todo-add-btn').addEventListener('click', addTodo);
        document.getElementById('todo-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') addTodo();
        });
        
        document.getElementById('todo-toggle').addEventListener('click', toggleTodoPanel);
        
        document.getElementById('todo-list').addEventListener('click', handleTodoClick);
        document.getElementById('todo-list').addEventListener('change', handleTodoChange);
        
        loadTodos();
        renderTodos();
    }
    
    function loadTodos() {
        try {
            const saved = localStorage.getItem(TODO_STORAGE_KEY);
            if (saved) {
                todoItems = JSON.parse(saved);
            }
        } catch (e) {
            console.error('Failed to load todos:', e);
            todoItems = [];
        }
    }
    
    function saveTodos() {
        try {
            localStorage.setItem(TODO_STORAGE_KEY, JSON.stringify(todoItems));
        } catch (e) {
            console.error('Failed to save todos:', e);
        }
    }
    
    function addTodo() {
        const input = document.getElementById('todo-input');
        const text = input.value.trim();
        
        if (!text) return;
        
        const newTodo = {
            id: Date.now().toString(36) + Math.random().toString(36).substr(2),
            text: text,
            completed: false,
            createdAt: new Date().toISOString()
        };
        
        todoItems.unshift(newTodo);
        saveTodos();
        renderTodos();
        
        input.value = '';
        input.focus();
    }
    
    function deleteTodo(id) {
        todoItems = todoItems.filter(item => item.id !== id);
        saveTodos();
        renderTodos();
    }
    
    function toggleTodo(id) {
        const item = todoItems.find(t => t.id === id);
        if (item) {
            item.completed = !item.completed;
            saveTodos();
            renderTodos();
        }
    }
    
    function startEditTodo(id) {
        const li = document.querySelector(`.todo-item[data-id="${id}"]`);
        if (!li) return;
        
        const item = todoItems.find(t => t.id === id);
        if (!item) return;
        
        const textWrapper = li.querySelector('.todo-text-wrapper');
        const currentText = item.text;
        
        textWrapper.innerHTML = `<input type="text" class="todo-text-input" value="${escapeHtml(currentText)}">`;
        const input = textWrapper.querySelector('.todo-text-input');
        input.focus();
        input.select();
        
        const finishEdit = () => {
            const newText = input.value.trim();
            if (newText && newText !== currentText) {
                item.text = newText;
                saveTodos();
            }
            renderTodos();
        };
        
        input.addEventListener('blur', finishEdit);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                input.blur();
            }
        });
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                renderTodos();
            }
        });
    }
    
    function handleTodoClick(e) {
        const target = e.target;
        const li = target.closest('.todo-item');
        if (!li) return;
        
        const id = li.dataset.id;
        
        if (target.classList.contains('todo-delete-btn')) {
            deleteTodo(id);
        } else if (target.classList.contains('todo-edit-btn')) {
            startEditTodo(id);
        }
    }
    
    function handleTodoChange(e) {
        if (e.target.classList.contains('todo-checkbox')) {
            const li = e.target.closest('.todo-item');
            if (li) {
                toggleTodo(li.dataset.id);
            }
        }
    }
    
    function renderTodos() {
        const list = document.getElementById('todo-list');
        if (!list) return;
        
        const totalCount = todoItems.length;
        const completedCount = todoItems.filter(t => t.completed).length;
        
        const totalEl = document.getElementById('todo-total-count');
        const completedEl = document.getElementById('todo-completed-count');
        if (totalEl) totalEl.textContent = totalCount;
        if (completedEl) completedEl.textContent = completedCount;
        
        if (totalCount === 0) {
            list.innerHTML = `
                <li class="todo-empty">
                    <div class="todo-empty-icon">📋</div>
                    <div>暂无待办事项</div>
                    <div style="font-size: 11px; margin-top: 4px;">添加一个新任务开始吧！</div>
                </li>
            `;
            return;
        }
        
        list.innerHTML = todoItems.map(item => `
            <li class="todo-item ${item.completed ? 'completed' : ''}" data-id="${item.id}">
                <input type="checkbox" class="todo-checkbox" ${item.completed ? 'checked' : ''}>
                <div class="todo-text-wrapper">
                    <span class="todo-text">${escapeHtml(item.text)}</span>
                </div>
                <div class="todo-actions">
                    <button class="todo-edit-btn" title="编辑">✏️</button>
                    <button class="todo-delete-btn" title="删除">🗑️</button>
                </div>
            </li>
        `).join('');
    }
    
    function toggleTodoPanel() {
        const panel = document.getElementById('right-panel');
        const toggle = document.getElementById('todo-toggle');
        
        panel.classList.toggle('collapsed');
        toggle.textContent = panel.classList.contains('collapsed') ? '◀' : '▶';
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
        toggle.innerHTML = sidebar.classList.contains('collapsed') ? '◀' : '▶';
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
        let activeDays = 0;
        for (let i = 1; i <= lastDay.getDate(); i++) {
            const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
            const record = streak.records[dateStr];
            const isToday = i === today.getDate();
            
            let className = 'calendar-day';
            let tooltip = '';
            let emoji = '';
            
            if (isToday) className += ' today';
            if (record) {
                activeDays++;
                if (record.messages >= 5) {
                    className += ' completed';
                    emoji = '✅';
                    completedDays++;
                } else if (record.messages > 0 || record.checkedIn) {
                    className += ' partial';
                    emoji = '⚡';
                }
                tooltip = `练习${record.messages}句，时长${record.duration}秒`;
            }
            
            html += `<div class="${className}" title="${tooltip}">${i}${emoji}</div>`;
        }
        
        html += '</div>';
        html += `<div class="calendar-summary">本月活跃 ${activeDays} 天（完成 ${completedDays} 天）</div>`;
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

    let _vocabCache = [];

    async function renderVocabulary() {
        const list = document.getElementById('wrong-words-list');
        if (!list) return;

        try {
            const res = await fetch('/api/vocabulary');
            _vocabCache = await res.json();
        } catch (e) {
            console.error('Failed to load vocabulary:', e);
        }

        updateVocabCount();

        if (_vocabCache.length === 0) {
            list.innerHTML = '<p class="empty-message">暂无生词，继续练习或手动添加！</p>';
            return;
        }

        let html = '';
        _vocabCache.forEach(item => {
            html += `
                <div class="vocab-item" data-id="${item.id}">
                    <div class="vocab-word-row">
                        <span class="vocab-word">${escapeHtml(item.word)}</span>
                        <button class="vocab-speak-btn" onclick="speakVocabWord('${escapeHtml(item.word)}')" title="发音">🔊</button>
                    </div>
                    ${item.definition ? `<div class="vocab-def">${escapeHtml(item.definition)}</div>` : ''}
                    ${item.example ? `<div class="vocab-example">"${escapeHtml(item.example)}"</div>` : ''}
                    <div class="vocab-item-actions">
                        <button class="vocab-edit-btn" onclick="editVocabWord(${item.id})" title="编辑">✏️</button>
                        <button class="vocab-delete-btn" onclick="deleteVocabWord(${item.id})" title="删除">🗑️</button>
                    </div>
                </div>`;
        });

        list.innerHTML = html;
    }

    function updateVocabCount() {
        const countEl = document.getElementById('vocab-count');
        if (countEl) countEl.textContent = _vocabCache.length;
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function showAddVocabModal(word = '') {
        const modal = document.createElement('div');
        modal.className = 'vocab-modal-overlay';
        modal.innerHTML = `
            <div class="vocab-modal">
                <div class="vocab-modal-header">
                    <h3>添加生词</h3>
                    <button class="vocab-modal-close" onclick="this.closest('.vocab-modal-overlay').remove()">✕</button>
                </div>
                <form onsubmit="submitAddVocab(event, this)">
                    <label>单词 *</label>
                    <input type="text" name="word" value="${escapeHtml(word)}" required placeholder="如: beautiful">
                    <label>释义</label>
                    <input type="text" name="definition" placeholder="如: 美丽的">
                    <label>例句</label>
                    <textarea name="example" rows="2" placeholder="如: The view is beautiful."></textarea>
                    <label>来源</label>
                    <input type="text" name="source" placeholder="如: 练习/手动添加">
                    <div class="vocab-modal-actions">
                        <button type="submit" class="btn-primary">保存</button>
                        <button type="button" onclick="this.closest('.vocab-modal-overlay').remove()">取消</button>
                    </div>
                </form>
            </div>
        `;
        document.body.appendChild(modal);
        setTimeout(() => modal.querySelector('input[name="word"]').focus(), 100);
    }

    async function submitAddVocab(e, form) {
        e.preventDefault();
        const data = {
            word: form.word.value.trim(),
            definition: form.definition.value.trim(),
            example: form.example.value.trim(),
            source: form.source.value.trim()
        };
        try {
            const res = await fetch('/api/vocabulary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                form.closest('.vocab-modal-overlay').remove();
                renderVocabulary();
            }
        } catch (err) {
            alert('保存失败: ' + err.message);
        }
    }

    async function editVocabWord(id) {
        const item = _vocabCache.find(v => v.id === id);
        if (!item) return;

        const modal = document.createElement('div');
        modal.className = 'vocab-modal-overlay';
        modal.innerHTML = `
            <div class="vocab-modal">
                <div class="vocab-modal-header">
                    <h3>编辑生词</h3>
                    <button class="vocab-modal-close" onclick="this.closest('.vocab-modal-overlay').remove()">✕</button>
                </div>
                <form onsubmit="submitEditVocab(event, this, ${id})">
                    <label>单词 *</label>
                    <input type="text" name="word" value="${escapeHtml(item.word)}" required>
                    <label>释义</label>
                    <input type="text" name="definition" value="${escapeHtml(item.definition || '')}" placeholder="如: 美丽的">
                    <label>例句</label>
                    <textarea name="example" rows="2" placeholder="如: The view is beautiful.">${escapeHtml(item.example || '')}</textarea>
                    <label>来源</label>
                    <input type="text" name="source" value="${escapeHtml(item.source || '')}" placeholder="如: 练习/手动添加">
                    <div class="vocab-modal-actions">
                        <button type="submit" class="btn-primary">保存</button>
                        <button type="button" onclick="this.closest('.vocab-modal-overlay').remove()">取消</button>
                    </div>
                </form>
            </div>
        `;
        document.body.appendChild(modal);
    }

    async function submitEditVocab(e, form, id) {
        e.preventDefault();
        const data = {
            word: form.word.value.trim(),
            definition: form.definition.value,
            example: form.example.value,
            source: form.source.value
        };
        try {
            const res = await fetch(`/api/vocabulary/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                form.closest('.vocab-modal-overlay').remove();
                renderVocabulary();
            }
        } catch (err) {
            alert('更新失败: ' + err.message);
        }
    }

    async function deleteVocabWord(id) {
        if (!confirm('确定删除这个生词吗？')) return;
        try {
            const res = await fetch(`/api/vocabulary/${id}`, { method: 'DELETE' });
            if (res.ok) renderVocabulary();
        } catch (err) {
            alert('删除失败: ' + err.message);
        }
    }

    function exportVocab(format) {
        window.open(`/api/vocabulary/export?format=${format}`, '_blank');
    }

    function bindEvents() {
        btnSend.addEventListener("click", () => sendMessage());

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

    window.submitAddVocab = submitAddVocab;
    window.submitEditVocab = submitEditVocab;
    window.editVocabWord = editVocabWord;
    window.deleteVocabWord = deleteVocabWord;
    window.speakVocabWord = (word) => SpeechManager.speakWord(word);

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
