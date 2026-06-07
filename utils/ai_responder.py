"""
AI 回复引擎 —— 接入智谱 GLM API，支持多轮上下文对话。

核心功能：
  - 真实 LLM API 调用
  - 会话记忆管理
  - 场景感知回复
  - 语法纠错与回复分离
"""

import json
import os
import random
import urllib.request
import urllib.error
from dataclasses import dataclass, field

from utils.grammar_checker import GrammarResult, build_correction_message, check_grammar
from utils.scenarios import get_scenario

ENCOURAGEMENT_MESSAGES = [
    "加油，已经很接近了！再试一次，你可以的！",
    "别灰心，学习语言就是这样一步步来的，继续保持！",
    "进步是需要时间的，你已经在正确的路上了！",
    "很棒的努力！每个错误都是学习的机会，再来一句吧！",
    "You're doing great! Mistakes help us learn faster. Keep going!",
]

POSITIVE_FEEDBACK = [
    "Well said! Your English sounds natural.",
    "Perfect! No grammar issues spotted.",
    "Great job! That was clear and correct.",
    "Excellent! You're getting the hang of this.",
]

ENCOURAGEMENT_THRESHOLD = 2


@dataclass
class SessionState:
    """会话状态，追踪用户连续错误次数和对话历史。"""
    consecutive_errors: int = 0
    total_messages: int = 0
    total_errors: int = 0
    scenario_id: str = "restaurant"
    history: list = field(default_factory=list)
    goal_progress: int = 0


@dataclass
class ChatResponse:
    """统一的聊天回复结构。"""
    reply: str
    correction: str | None = None
    encouragement: str | None = None
    grammar: dict = field(default_factory=dict)
    scenario_id: str = "restaurant"
    goal_progress: int = 0

    def to_dict(self) -> dict:
        return {
            "reply": self.reply,
            "correction": self.correction,
            "encouragement": self.encouragement,
            "grammar": self.grammar,
            "scenario_id": self.scenario_id,
            "goal_progress": self.goal_progress,
        }


def _build_system_prompt(scenario: dict, goals: list = None, goal_progress: int = 0) -> str:
    """构建发给大模型的 system prompt。"""
    goal_info = ""
    if goals and goal_progress < len(goals):
        current_goal = goals[goal_progress]
        goal_info = f"\n\nCurrent goal: {current_goal}"
    
    return (
        f"You are a {scenario['persona']} in an English speaking practice session.\n"
        f"Scenario: {scenario['name_en']}\n"
        f"Description: {scenario['description']}\n"
        f"{goal_info}\n\n"
        "Role: Act as a real person in this scenario.\n\n"
        "Requirements:\n"
        "1. Maintain conversation context naturally.\n"
        "2. Reply in 1-3 sentences only.\n"
        "3. Ask follow-up questions to keep conversation going.\n"
        "4. Encourage the learner with positive feedback.\n"
        "5. Keep language appropriate for ESL learners (B1-B2 level).\n"
        "6. Do NOT correct grammar in your reply - corrections are handled separately.\n"
        "7. Guide the conversation toward completing the scenario goals."
    )


def call_llm_api(
    user_message: str,
    scenario_id: str,
    conversation_history: list[dict] | None = None,
    goals: list | None = None,
    goal_progress: int = 0,
    custom_persona: str | None = None,
    custom_scenario_name: str | None = None,
) -> str | None:
    """
    调用智谱 GLM API 生成回复。
    
    需要在环境变量中配置 ZHIPU_API_KEY
    
    Returns:
        模型生成的回复文本；返回 None 表示未配置 API，走模板回退。
    """
    api_key = os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        print("[WARN] ZHIPU_API_KEY 未设置，使用模板模式")
        return None
    
    print(f"[OK] ZHIPU_API_KEY 已设置: {api_key[:10]}...")

    try:
        if scenario_id == 'custom' and custom_persona:
            scenario = {
                "id": "custom",
                "name": custom_scenario_name or "Custom",
                "name_en": custom_scenario_name or "Custom",
                "persona": custom_persona,
                "description": "Custom user-defined scenario",
                "goals": [],
                "goal_keywords": {},
                "keywords": [],
                "responses": [],
                "hints": [],
            }
        else:
            scenario = get_scenario(scenario_id)
        
        messages = []
        
        system_prompt = _build_system_prompt(scenario, goals, goal_progress)
        messages.append({"role": "system", "content": system_prompt})
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_message})

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        data = {
            "model": "glm-5.1",
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7,
        }
        
        json_data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=json_data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )
        
        print("[INFO] 请求发送中...")
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            print("[OK] API 响应成功")
            return result["choices"][0]["message"]["content"]
    
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP 错误 {e.code}: {e.reason}")
        try:
            error_body = e.read().decode("utf-8")
            print(f"错误详情: {error_body}")
        except:
            pass
        return None
    except Exception as e:
        print(f"[ERROR] LLM API 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def _pick_scenario_response(user_message: str, scenario: dict) -> str:
    """根据场景关键词和随机模板生成自然回复。"""
    lower = user_message.lower()
    keywords = scenario.get("keywords", [])
    responses = scenario.get("responses", [])

    matched = [kw for kw in keywords if kw in lower]
    if matched and responses:
        return random.choice(responses)

    if responses:
        return random.choice(responses)
    
    default_responses = [
        "That's interesting! Tell me more.",
        "Could you elaborate on that?",
        "I see. What do you think about this?",
        "That's a good point. Let's continue.",
        "I understand. Please go on.",
    ]
    return random.choice(default_responses)


def _check_goal_progress(user_message: str, scenario: dict, current_progress: int) -> int:
    """检查场景目标完成进度。"""
    goals = scenario.get("goals", [])
    if not goals or current_progress >= len(goals):
        return current_progress
    
    lower = user_message.lower()
    keywords_map = scenario.get("goal_keywords", {})
    
    next_goal = goals[current_progress]
    keywords = keywords_map.get(next_goal, [])
    
    if any(kw in lower for kw in keywords):
        return min(current_progress + 1, len(goals))
    
    return current_progress


def generate_response(
    user_message: str,
    scenario_id: str,
    state: SessionState,
    conversation_history: list[dict] | None = None,
    custom_persona: str | None = None,
    custom_scenario_name: str | None = None,
) -> ChatResponse:
    """
    生成完整的 AI 回复（自然回应 + 纠错 + 鼓励）。
    """
    if scenario_id == 'custom' and custom_persona:
        scenario = {
            "id": "custom",
            "name": custom_scenario_name or "Custom",
            "name_en": custom_scenario_name or "Custom",
            "persona": custom_persona,
            "goals": [],
            "goal_keywords": {},
            "keywords": [],
            "responses": [],
            "hints": [],
        }
    else:
        scenario = get_scenario(scenario_id)
    
    grammar_result: GrammarResult = check_grammar(user_message)
    state.total_messages += 1

    if grammar_result.has_errors:
        state.consecutive_errors += 1
        state.total_errors += grammar_result.error_count
    else:
        state.consecutive_errors = 0

    goals = scenario.get("goals", [])
    state.goal_progress = _check_goal_progress(user_message, scenario, state.goal_progress)

    api_reply = call_llm_api(
        user_message, 
        scenario_id, 
        conversation_history,
        goals,
        state.goal_progress,
        custom_persona,
        custom_scenario_name
    )
    
    if api_reply:
        natural_reply = api_reply
    else:
        natural_reply = _pick_scenario_response(user_message, scenario)

    correction = build_correction_message(grammar_result)

    encouragement = None
    if state.consecutive_errors >= ENCOURAGEMENT_THRESHOLD:
        encouragement = random.choice(ENCOURAGEMENT_MESSAGES)
        state.consecutive_errors = 0

    return ChatResponse(
        reply=natural_reply,
        correction=correction,
        encouragement=encouragement,
        grammar=grammar_result.to_dict(),
        scenario_id=scenario_id,
        goal_progress=state.goal_progress,
    )
