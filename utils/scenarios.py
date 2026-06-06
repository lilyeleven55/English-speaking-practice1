"""
Scenario definition module - manages conversation scenarios with context, openings and responses.
"""

from typing import Dict, List, Any


SCENARIOS: Dict[str, Dict[str, Any]] = {
    "restaurant": {
        "id": "restaurant",
        "name": "🍽️ 餐厅点餐",
        "name_en": "Restaurant Ordering",
        "icon": "🍽️",
        "description": "Practice ordering food and drinks at a restaurant.",
        "opening": (
            "Welcome to Sunny Cafe! I'm your waiter today. "
            "What would you like to order?"
        ),
        "persona": "friendly restaurant waiter",
        "goals": ["greeting", "order_food", "choose_drink", "confirm_order", "pay_bill"],
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
    "airport": {
        "id": "airport",
        "name": "✈️ 机场出行",
        "name_en": "Airport Travel",
        "icon": "✈️",
        "description": "Practice airport conversations: check-in, baggage, directions.",
        "opening": (
            "Good morning! Welcome to the airport. "
            "Do you need help with check-in or finding your gate?"
        ),
        "persona": "helpful airport staff",
        "goals": ["greeting", "check_in", "baggage", "security", "boarding"],
        "goal_keywords": {
            "greeting": ["hello", "hi", "good morning", "good afternoon"],
            "check_in": ["check in", "boarding pass", "ticket", "seat"],
            "baggage": ["baggage", "luggage", "suitcase", "carry on"],
            "security": ["security", "passport", "ID", "screening"],
            "boarding": ["gate", "board", "departure", "flight"]
        },
        "keywords": [
            "check-in", "boarding pass", "luggage", "security",
            "gate", "boarding", "departure", "passport",
            "ticket", "seat", "carry-on", "baggage claim",
        ],
        "responses": [
            "Certainly! May I see your passport and ticket, please?",
            "Your flight departs from gate 23 in 45 minutes.",
            "Your carry-on looks good - it meets size requirements.",
            "Security checkpoint is just ahead on your left.",
            "Boarding will begin in 15 minutes. Have a safe flight!",
        ],
        "hints": [
            "Try: 'Where is gate 23?' or 'How do I check in?'",
            "Ask about flight status: 'Is flight AB123 on time?'",
            "Ask about baggage: 'Where do I collect my luggage?'",
        ],
    },
    "shopping": {
        "id": "shopping",
        "name": "🛍️ 日常购物",
        "name_en": "Daily Shopping",
        "icon": "🛍️",
        "description": "Practice shopping conversations: asking prices, sizes, bargaining.",
        "opening": (
            "Welcome to our store! How can I help you today? "
            "Looking for anything specific?"
        ),
        "persona": "friendly shop assistant",
        "goals": ["greeting", "ask_item", "ask_price", "ask_size", "purchase"],
        "goal_keywords": {
            "greeting": ["hello", "hi", "welcome"],
            "ask_item": ["looking for", "want", "need", "find"],
            "ask_price": ["how much", "price", "cost", "expensive"],
            "ask_size": ["size", "fit", "small", "large"],
            "purchase": ["buy", "take", "checkout", "pay"]
        },
        "keywords": [
            "price", "size", "color", "discount", "sale",
            "try on", "fitting room", "checkout", "cash",
            "credit card", "receipt", "return", "exchange",
        ],
        "responses": [
            "This one is very popular! Would you like to try it on?",
            "That's $49.99 - we have a 20% discount today!",
            "We have sizes S, M, L - what size are you looking for?",
            "Sure! The fitting rooms are over there.",
            "Would you like to pay with cash or card?",
        ],
        "hints": [
            "Try: 'How much is this?' or 'Do you have this in blue?'",
            "Ask for discount: 'Is there any discount today?'",
            "Ask about returns: 'What's your return policy?'",
        ],
    },
    "interview": {
        "id": "interview",
        "name": "💼 职场面试",
        "name_en": "Job Interview",
        "icon": "💼",
        "description": "Practice English job interview conversations.",
        "opening": (
            "Good morning! Thank you for coming today. "
            "Let's start with your self-introduction."
        ),
        "persona": "professional interviewer",
        "goals": ["greeting", "introduction", "experience", "skills", "closing"],
        "goal_keywords": {
            "greeting": ["hello", "good morning", "thank you"],
            "introduction": ["my name is", "I am", "I graduated", "major"],
            "experience": ["experience", "worked", "project", "responsibility"],
            "skills": ["skill", "proficient", "knowledge", "ability"],
            "closing": ["thank you", "when will I hear", "questions"]
        },
        "keywords": [
            "resume", "experience", "skills", "project",
            "teamwork", "challenge", "strength", "weakness",
            "salary", "benefits", "start date", "references",
        ],
        "responses": [
            "Great introduction! Tell me about your previous work experience.",
            "What was your biggest achievement in your last role?",
            "Describe a time you faced a challenge at work.",
            "What are your strongest technical skills?",
            "Do you have any questions for me about the company?",
        ],
        "hints": [
            "Try: 'I graduated from X university with a degree in...'",
            "Talk about your experience: 'In my previous job, I...'",
            "Prepare answers for common questions about strengths/weaknesses.",
        ],
    },
    "school": {
        "id": "school",
        "name": "📚 校园选课",
        "name_en": "Course Registration",
        "icon": "📚",
        "description": "Practice conversations for course registration and academic advising.",
        "opening": (
            "Hello! Welcome to the registration office. "
            "Which courses are you interested in this semester?"
        ),
        "persona": "friendly academic advisor",
        "goals": ["greeting", "courses", "schedule", "requirements", "registration"],
        "goal_keywords": {
            "greeting": ["hello", "hi", "good morning"],
            "courses": ["course", "class", "subject", "major"],
            "schedule": ["schedule", "time", "when", "class time"],
            "requirements": ["requirement", "prerequisite", "credit", "grade"],
            "registration": ["register", "enroll", "sign up", "add"]
        },
        "keywords": [
            "course", "credit", "prerequisite", "schedule",
            "semester", "professor", "classroom", "exam",
            "major", "minor", "elective", "required",
        ],
        "responses": [
            "What's your major? I can recommend some great courses!",
            "CS101 has Professor Smith - he's excellent!",
            "That course requires CS100 as a prerequisite. Have you taken it?",
            "Classes are Monday, Wednesday, Friday from 9-10 AM.",
            "Would you like me to help you register for these courses?",
        ],
        "hints": [
            "Ask: 'What courses are recommended for freshmen?'",
            "Ask: 'Is CS101 available this semester?'",
            "Ask: 'How many credits do I need to graduate?'",
        ],
    },
    "directions": {
        "id": "directions",
        "name": "🗺️ 短途问路",
        "name_en": "Getting Directions",
        "icon": "🗺️",
        "description": "Practice asking for and giving directions in English.",
        "opening": (
            "Hi there! Looking for directions? "
            "Where are you trying to go?"
        ),
        "persona": "friendly local resident",
        "goals": ["greeting", "destination", "route", "landmarks", "confirmation"],
        "goal_keywords": {
            "greeting": ["hello", "hi", "excuse me"],
            "destination": ["where is", "how to get to", "nearest", "direction"],
            "route": ["walk", "bus", "metro", "turn"],
            "landmarks": ["next to", "opposite", "near", "landmark"],
            "confirmation": ["thank you", "is that right", "how long"]
        },
        "keywords": [
            "street", "avenue", "turn left", "turn right",
            "straight", "block", "station", "landmark",
            "walking time", "bus stop", "subway", "exit",
        ],
        "responses": [
            "Sure! Go straight ahead and turn left at the next corner.",
            "The subway station is just two blocks from here.",
            "Look for the big red building - it's right next to it.",
            "It takes about 10 minutes to walk there.",
            "You can take bus #5 and get off at the Main Street stop.",
        ],
        "hints": [
            "Try: 'Excuse me, where is the nearest subway station?'",
            "Ask: 'How do I get to the museum?'",
            "Ask: 'Is it far from here?'",
        ],
    },
}

DEFAULT_SCENARIO: str = "restaurant"


def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """Get scenario config, return default if not found."""
    return SCENARIOS.get(scenario_id, SCENARIOS[DEFAULT_SCENARIO])


def list_scenarios() -> List[Dict[str, Any]]:
    """Return list of scenarios for frontend display."""
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
