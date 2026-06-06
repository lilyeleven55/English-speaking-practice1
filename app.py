"""
AI 英语口语陪练 —— Flask 主应用入口。

核心功能：
  - 多轮上下文对话
  - 会话记忆管理
  - 学习数据统计
  - 场景目标追踪

运行方式：python app.py
访问地址：http://127.0.0.1:5000
"""

import os
import sqlite3
import uuid
from datetime import date
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

load_dotenv()

from utils.ai_responder import SessionState, generate_response
from utils.scenarios import DEFAULT_SCENARIO, list_scenarios

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-in-production")

DB_PATH = "practice.db"
_sessions: dict[str, SessionState] = {}


def init_db():
    """初始化数据库表。"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS practice_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            date DATE NOT NULL,
            message_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            scenario TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    conn.commit()
    conn.close()


def _get_user_id() -> str:
    """获取或创建当前用户 ID。"""
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (session["user_id"],))
        conn.commit()
        conn.close()
    
    return session["user_id"]


def _update_practice_record(user_id: str, scenario: str, has_errors: bool):
    """更新练习记录。"""
    today = date.today()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, message_count, error_count FROM practice_records 
        WHERE user_id = ? AND date = ? AND scenario = ?
    """, (user_id, today, scenario))
    
    record = cursor.fetchone()
    
    if record:
        cursor.execute("""
            UPDATE practice_records 
            SET message_count = ?, error_count = ?
            WHERE id = ?
        """, (record[1] + 1, record[2] + (1 if has_errors else 0), record[0]))
    else:
        cursor.execute("""
            INSERT INTO practice_records (user_id, date, message_count, error_count, scenario)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, today, 1, 1 if has_errors else 0, scenario))
    
    conn.commit()
    conn.close()


def _get_today_stats(user_id: str) -> dict:
    """获取今日练习统计。"""
    today = date.today()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT SUM(message_count), SUM(error_count) 
        FROM practice_records 
        WHERE user_id = ? AND date = ?
    """, (user_id, today))
    
    result = cursor.fetchone()
    conn.close()
    
    total_messages = result[0] or 0
    total_errors = result[1] or 0
    accuracy = 0 if total_messages == 0 else round((1 - total_errors / total_messages) * 100, 1)
    
    return {
        "today_messages": total_messages,
        "today_errors": total_errors,
        "today_accuracy": accuracy
    }


def _get_total_stats(user_id: str) -> dict:
    """获取累计练习统计。"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT SUM(message_count), SUM(error_count) 
        FROM practice_records 
        WHERE user_id = ?
    """, (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    total_messages = result[0] or 0
    total_errors = result[1] or 0
    accuracy = 0 if total_messages == 0 else round((1 - total_errors / total_messages) * 100, 1)
    
    return {
        "total_messages": total_messages,
        "total_errors": total_errors,
        "total_accuracy": accuracy
    }


def _get_session_state() -> SessionState:
    """获取或创建当前用户的会话状态。"""
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    sid = session["sid"]
    if sid not in _sessions:
        _sessions[sid] = SessionState()
    return _sessions[sid]


@app.route("/")
def index():
    """渲染聊天主页面。"""
    return render_template("index.html")


@app.route("/api/scenarios", methods=["GET"])
def api_scenarios():
    """返回所有可用场景列表。"""
    return jsonify({"scenarios": list_scenarios()})


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """
    处理用户聊天消息。
    
    请求体 JSON:
        message (str): 用户英文输入
        scenario_id (str): 场景 ID，默认 restaurant
        history (list): 对话历史 [{role, content}, ...]
        custom_persona (str, optional): 自定义场景AI角色
        custom_scenario_name (str, optional): 自定义场景名称
    
    响应 JSON:
        reply, correction, encouragement, grammar, scenario_id, goal_progress
    """
    try:
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()

        if not user_message:
            return jsonify({"error": "Message cannot be empty."}), 400

        scenario_id = data.get("scenario_id", DEFAULT_SCENARIO)
        history = data.get("history", [])
        custom_persona = data.get("custom_persona")
        custom_scenario_name = data.get("custom_scenario_name")

        state = _get_session_state()
        state.scenario_id = scenario_id

        response = generate_response(
            user_message=user_message,
            scenario_id=scenario_id,
            state=state,
            conversation_history=history,
            custom_persona=custom_persona,
            custom_scenario_name=custom_scenario_name,
        )

        has_errors = response.grammar.get("has_errors", False)
        try:
            _update_practice_record(_get_user_id(), scenario_id, has_errors)
        except Exception as db_error:
            print(f"⚠️ 数据库更新警告: {db_error}")

        return jsonify(response.to_dict())
    except Exception as e:
        print(f"❌ API 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Server error", "reply": "Sorry, something went wrong. Please try again!"}), 500


@app.route("/api/reset", methods=["POST"])
def api_reset():
    """重置当前会话（切换场景或清空对话时调用）。"""
    data = request.get_json(silent=True) or {}
    scenario_id = data.get("scenario_id", DEFAULT_SCENARIO)

    state = _get_session_state()
    state.consecutive_errors = 0
    state.goal_progress = 0
    state.scenario_id = scenario_id

    return jsonify({"ok": True, "scenario_id": scenario_id})


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """获取用户练习统计数据。"""
    try:
        user_id = _get_user_id()
        
        today_stats = _get_today_stats(user_id)
        total_stats = _get_total_stats(user_id)
        
        return jsonify({
            "today": today_stats,
            "total": total_stats
        })
    except Exception as e:
        print(f"⚠️ 统计数据错误: {e}")
        return jsonify({
            "today": {"today_messages": 0, "today_errors": 0, "today_accuracy": 0},
            "total": {"total_messages": 0, "total_errors": 0, "total_accuracy": 0}
        })


if __name__ == "__main__":
    # 确保数据库在启动时初始化
    try:
        init_db()
        print("[OK] 数据库初始化成功")
    except Exception as e:
        print(f"[WARN] 数据库初始化警告: {e}")
    
    app.run(debug=True, host="127.0.0.1", port=5000)
