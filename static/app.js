/**
 * 前端交互逻辑 —— AJAX 聊天、场景切换、消息渲染、语音功能。
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

    async function init() {
        await loadScenarios();
        await loadStats();
        bindEvents();
        initSpeechRecognition();
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
                <span class="stat-label">语法正确率</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
                <span class="stat-value">${stats.total.total_messages}</span>
                <span class="stat-label">累计练习</span>
            </div>
        `;
        
        const header = document.querySelector(".header");
        if (header) {
            header.appendChild(statsEl);
        }
    }

    function renderScenarioButtons(scenarios) {
        scenarioBar.innerHTML = "";
        scenarios.forEach((s) => {
            const btn = document.createElement("button");
            btn.className = "scenario-btn" + (s.id === currentScenario ? " active" : "");
            btn.dataset.id = s.id;
            btn.innerHTML = `${s.icon} ${s.name}`;
            btn.title = s.description;
            btn.addEventListener("click", () => switchScenario(s));
            scenarioBar.appendChild(btn);
        });
    }

    async function switchScenario(scenario) {
        if (scenario.id === currentScenario) return;

        currentScenario = scenario.id;
        conversationHistory = [];

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

        const typingEl = showTyping();

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: userText,
                    scenario_id: currentScenario,
                    history: conversationHistory.slice(-10),
                }),
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || "Request failed");
            }

            removeTyping(typingEl);

            appendMessage("ai", data.reply, {
                correction: data.correction,
                encouragement: data.encouragement,
                grammar: data.grammar,
            });
            conversationHistory.push({ role: "assistant", content: data.reply });

            speakText(data.reply);
            await loadStats();

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

    function appendMessage(role, text, extras = {}) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${role}`;

        const bubble = document.createElement("div");
        bubble.className = "bubble";
        bubble.textContent = text;
        msgDiv.appendChild(bubble);

        if (extras.correction || extras.grammar) {
            const grammarCard = document.createElement("div");
            grammarCard.className = "grammar-card";
            
            const hasErrors = extras.grammar?.has_errors || false;
            const errorCount = extras.grammar?.error_count || 0;
            
            grammarCard.innerHTML = `
                <div class="grammar-header">
                    <span class="grammar-icon">📝</span>
                    <span class="grammar-title">Grammar Feedback</span>
                </div>
                <div class="grammar-content">
                    <p class="original-text">${extras.grammar?.original || text}</p>
                    <p class="${hasErrors ? 'error-text' : 'success-text'}">
                        ${hasErrors ? `❌ ${errorCount} error(s) found` : '✓ Correct sentence'}
                    </p>
                    ${extras.correction ? `<p class="correction-text">${extras.correction.replace(/\*\*/g, '')}</p>` : ''}
                </div>
            `;
            msgDiv.appendChild(grammarCard);
        }

        if (extras.encouragement) {
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
            recognition.stop();
            isRecording = false;
        } else {
            recognition.start();
            isRecording = true;
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
            conversationHistory = [];
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

    init();
})();