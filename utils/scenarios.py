"""
场景定义模块 —— 管理不同对话场景的上下文、开场白和回复模板。

新增功能：
  - 场景目标机制（任务驱动型对话）
  - 目标关键词映射
"""

SCENARIOS = {
    "restaurant": {
        "id": "restaurant",
        "name": "餐厅点餐",
        "name_en": "Restaurant Ordering",
        "icon": "🍽️",
        "description": "Practice ordering food and drinks at a restaurant.",
        "opening": (
            "Welcome to Sunny Café! I'm your waiter today. "
            "What would you like to order?"
        ),
        "persona": "friendly restaurant waiter",
        "goals": [
            "greeting",
            "order_food",
            "choose_drink",
            "confirm_order",
            "pay_bill"
        ],
        "goal_keywords": {
            "greeting": ["hello", "hi", "welcome", "good morning", "good afternoon", "good evening"],
            "order_food": ["order", "food", "main", "dish", "steak", "salad", "pasta", "burger", "rice"],
            "choose_drink": ["drink", "coffee", "tea", "water", "juice", "wine", "beer"],
            "confirm_order": ["yes", "that's all", "thank you", "okay", "confirm"],
            "pay_bill": ["bill", "check", "pay", "cost", "price"]
        },
        "keywords": [
            "order", "menu", "food", "drink", "bill", "check",
            "appetizer", "main course", "dessert", "coffee", "tea",
            "steak", "salad", "soup", "water", "wine",
        ],
        "responses": [
            "Great choice! Would you like anything else?",
            "Sure, I'll bring that right out. Anything to drink?",
            "Excellent! Our chef recommends the soup of the day.",
            "Of course! Would you like that for here or to go?",
            "Perfect! I'll have that ready in about 15 minutes.",
            "Good pick! That's one of our most popular dishes.",
        ],
        "hints": [
            "Try: 'I'd like to order...' or 'Could I have...'",
            "Remember to say 'please' and 'thank you'!",
            "You can ask: 'What do you recommend?'",
        ],
    },
    "greeting": {
        "id": "greeting",
        "name": "日常问候",
        "name_en": "Daily Greetings",
        "icon": "👋",
        "description": "Practice everyday greetings and small talk.",
        "opening": (
            "Hey there! Nice to meet you. "
            "How's your day going so far?"
        ),
        "persona": "friendly neighbor",
        "goals": [
            "greeting",
            "ask_about_day",
            "share_update",
            "make_plans"
        ],
        "goal_keywords": {
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "nice to meet"],
            "ask_about_day": ["how are you", "how's", "day going", "doing today", "feeling"],
            "share_update": ["good", "great", "fine", "busy", "tired", "happy"],
            "make_plans": ["weekend", "plans", "tonight", "tomorrow", "meet"]
        },
        "keywords": [
            "hello", "hi", "morning", "afternoon", "evening",
            "how are you", "fine", "good", "great", "weather",
            "weekend", "work", "study", "family", "friend",
        ],
        "responses": [
            "That's wonderful to hear! What have you been up to?",
            "Oh really? That sounds interesting!",
            "I'm doing great, thanks for asking!",
            "Ha ha, that's funny! Tell me more.",
            "Sounds like a busy day! Hope you get some rest later.",
            "Nice! I love chatting on days like this.",
        ],
        "hints": [
            "Try: 'How are you doing?' or 'Nice to meet you!'",
            "You can ask about the weather or weekend plans.",
            "A smile goes a long way — keep it friendly!",
        ],
    },
}

DEFAULT_SCENARIO = "restaurant"


def get_scenario(scenario_id: str) -> dict:
    """获取指定场景配置，不存在时返回默认场景。"""
    return SCENARIOS.get(scenario_id, SCENARIOS[DEFAULT_SCENARIO])


def list_scenarios() -> list[dict]:
    """返回所有场景的简要信息，供前端展示。"""
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "name_en": s["name_en"],
            "icon": s["icon"],
            "description": s["description"],
            "opening": s["opening"],
            "goals": s.get("goals", []),
        }
        for s in SCENARIOS.values()
    ]