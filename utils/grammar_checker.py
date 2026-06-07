"""
Grammar checker module - detects common ESL errors and provides correction suggestions.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class GrammarIssue:
    """Single grammar issue record."""
    original: str
    suggestion: str
    explanation: str
    severity: str = "medium"  # low | medium | high
    level: str = "format"  # format | word | grammar


@dataclass
class GrammarResult:
    """Grammar check result."""
    issues: List[GrammarIssue] = field(default_factory=list)
    error_count: int = 0
    has_errors: bool = False
    original_text: str = ""

    def to_dict(self) -> Dict:
        return {
            "has_errors": self.has_errors,
            "error_count": self.error_count,
            "original": self.original_text,
            "issues": [
                {
                    "original": i.original,
                    "suggestion": i.suggestion,
                    "description": i.explanation,
                    "severity": i.severity,
                    "level": i.level,
                }
                for i in self.issues
            ],
        }


_GRAMMAR_RULES = [
    (
        r"\bI\s+are\b",
        "I am",
        "I should use 'am', not 'are'.",
        "high",
    ),
    (
        r"\bI\s+is\b",
        "I am",
        "I should use 'am', not 'is'.",
        "high",
    ),
    (
        r"\b(he|she|it)\s+don't\b",
        r"\1 doesn't",
        "Third person singular should use 'doesn't'.",
        "high",
    ),
    (
        r"\b(he|she|it)\s+are\b",
        r"\1 is",
        "Third person singular should use 'is'.",
        "high",
    ),
    (
        r"\b(they|we|you)\s+is\b",
        r"\1 are",
        "Plural subjects should use 'are'.",
        "high",
    ),
    (
        r"\ba\s+([aeiouAEIOU]\w+)\b",
        r"an \1",
        "Use 'an' before vowel sounds.",
        "medium",
    ),
    (
        r"\ban\s+([^aeiouAEIOU\s]\w+)\b",
        r"a \1",
        "Use 'a' before consonant sounds.",
        "medium",
    ),
    (
        r"\bdon't\s+no\b",
        "don't know",
        "Double negatives should be avoided.",
        "medium",
    ),
    (
        r"\bmore\s+better\b",
        "better",
        "'better' is already comparative, no need for 'more'.",
        "medium",
    ),
    (
        r"\bvery\s+unique\b",
        "unique",
        "'unique' means one of a kind, not used with 'very'.",
        "low",
    ),
    (
        r"\bgo\s+to\s+home\b",
        "go home",
        "'home' as adverb doesn't need 'to'.",
        "medium",
    ),
    (
        r"\bmake\s+a\s+photo\b",
        "take a photo",
        "Use 'take a photo' instead of 'make a photo'.",
        "medium",
    ),
    (
        r"\bexplain\s+me\b",
        "explain to me",
        "'explain' needs 'to' before pronoun.",
        "medium",
    ),
    (
        r"\bdiscuss\s+about\b",
        "discuss",
        "'discuss' already includes 'about' meaning.",
        "low",
    ),
    (
        r"\bhow\s+much\s+persons\b",
        "how many people",
        "Use 'how many people' for counting people.",
        "medium",
    ),
]


COMMON_WORDS = {
    "fine", "good", "great", "happy", "sad", "tired", "hungry", "thirsty",
    "hello", "hi", "goodbye", "thanks", "please", "sorry",
    "yes", "no", "maybe", "perhaps",
    "eat", "drink", "sleep", "walk", "run", "talk", "think", "wait",
    "go", "come", "take", "give", "make", "do", "have", "be",
    "a", "an", "the", "this", "that", "these", "those",
    "i", "you", "he", "she", "it", "we", "they",
    "my", "your", "his", "her", "its", "our", "their",
    "is", "are", "was", "were", "am", "been", "being",
    "can", "could", "will", "would", "should", "may", "might", "must",
    "in", "on", "at", "by", "for", "of", "to", "from", "with", "without",
    "and", "but", "or", "so", "because", "if", "when", "while", "although",
    "what", "who", "which", "where", "when", "why", "how",
    "tomorrow", "yesterday", "today", "restaurant", "schedule"
}


def check_grammar(text: str) -> GrammarResult:
    """
    Detect common grammar errors in text.

    Args:
        text: User's English input.

    Returns:
        GrammarResult containing detected issues.
    """
    result = GrammarResult()
    result.original_text = text
    if not text or not text.strip():
        return result

    for pattern, replacement, explanation, severity in _GRAMMAR_RULES:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        for match in matches:
            original = match.group(0)
            if isinstance(replacement, str) and r"\1" in replacement:
                suggested = re.sub(pattern, replacement, original, flags=re.IGNORECASE)
            else:
                suggested = re.sub(
                    pattern, replacement, original, count=1, flags=re.IGNORECASE
                )

            level = "grammar" if severity == "high" else "word"
            result.issues.append(
                GrammarIssue(
                    original=original,
                    suggestion=suggested,
                    explanation=explanation,
                    severity=severity,
                    level=level,
                )
            )

    # 句首未大写
    stripped = text.strip()
    if stripped and stripped[0].islower() and stripped[0].isalpha():
        result.issues.append(
            GrammarIssue(
                original=stripped[0],
                suggestion=stripped[0].upper(),
                explanation=f"首字母 {stripped[0]} 需要大写 → {stripped[0].upper()}",
                severity="low",
                level="format",
            )
        )

    # 缺少句末标点
    if stripped and stripped[-1] not in ".!?":
        result.issues.append(
            GrammarIssue(
                original="(句末)",
                suggestion=".",
                explanation="句尾补充句号",
                severity="low",
                level="format",
            )
        )

    # 检测可能的拼写错误（基于常见单词列表）
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    for word in words:
        if len(word) >= 3 and word not in COMMON_WORDS:
            suggestions = _get_spelling_suggestions(word)
            if suggestions and suggestions[0] != word:
                result.issues.append(
                    GrammarIssue(
                        original=word,
                        suggestion=suggestions[0],
                        explanation=f"{word} 可能拼写错误，正确单词：{', '.join(suggestions)}",
                        severity="medium",
                        level="word",
                    )
                )

    result.error_count = len(result.issues)
    result.has_errors = result.error_count > 0
    
    return result


def _get_spelling_suggestions(word: str) -> list:
    """Get spelling suggestions for a word."""
    suggestions = []
    word_lower = word.lower()
    
    common_mistakes = {
        "fin": ["fine", "find", "finch"],
        "teh": ["the"],
        "wht": ["what"],
        "hw": ["how"],
        "u": ["you"],
        "r": ["are"],
        "ur": ["your", "you're"],
        "dont": ["don't"],
        "cant": ["can't"],
        "wont": ["won't"],
        "couldnt": ["couldn't"],
        "wouldnt": ["wouldn't"],
        "shouldnt": ["shouldn't"],
        "isnt": ["isn't"],
        "arent": ["aren't"],
        "wasnt": ["wasn't"],
        "werent": ["weren't"],
        "hasnt": ["hasn't"],
        "havent": ["haven't"],
        "hadnt": ["hadn't"],
        "didnt": ["didn't"],
        "doesnt": ["doesn't"],
        "neednt": ["needn't"],
        "dnt": ["don't"],
        "cnt": ["can't"],
        "wanna": ["want to"],
        "gonna": ["going to"],
        "gotta": ["got to"],
        "kinda": ["kind of"],
        "sorta": ["sort of"],
        "alot": ["a lot"],
        "neighbor": ["neighbour"],
        "color": ["colour"],
        "center": ["centre"],
        "traveler": ["traveller"],
        "favorite": ["favourite"],
        "honor": ["honour"],
        "labor": ["labour"],
        "theater": ["theatre"],
        "meter": ["metre"],
        "program": ["programme"],
        "catalog": ["catalogue"],
        "dialog": ["dialogue"],
        "cigarette": ["cigarette"],
        "accommodation": ["accommodation"],
        "calendar": ["calendar"],
        "committee": ["committee"],
        "definitely": ["definitely"],
        "environment": ["environment"],
        "friend": ["friend"],
        "government": ["government"],
        "immediately": ["immediately"],
        "magnificent": ["magnificent"],
        "necessary": ["necessary"],
        "occasion": ["occasion"],
        "separate": ["separate"],
        "successful": ["successful"],
        "temperature": ["temperature"],
        "vacuum": ["vacuum"],
        "weather": ["weather"],
        "whether": ["whether"],
        "yesterday": ["yesterday"],
        "tommorow": ["tomorrow"],
        "resturant": ["restaurant"],
        "schedule": ["schedule"],
        "receipt": ["receipt"],
        "achieve": ["achieve"],
        "believe": ["believe"],
        "conceive": ["conceive"],
        "deceive": ["deceive"],
        "perceive": ["perceive"],
        "piece": ["piece"],
        "peace": ["peace"],
        "advice": ["advice"],
        "advise": ["advise"],
        "affect": ["affect"],
        "effect": ["effect"],
        "complement": ["complement"],
        "compliment": ["compliment"],
        "principal": ["principal"],
        "principle": ["principle"],
        "stationary": ["stationary"],
        "stationery": ["stationery"],
        "ensure": ["ensure"],
        "insure": ["insure"],
        "assure": ["assure"],
        "accept": ["accept"],
        "except": ["except"],
        "access": ["access"],
        "excess": ["excess"],
        "adapt": ["adapt"],
        "adopt": ["adopt"],
        "adept": ["adept"],
        "bare": ["bare"],
        "bear": ["bear"],
        "brake": ["brake"],
        "break": ["break"],
        "buy": ["buy"],
        "by": ["by"],
        "cell": ["cell"],
        "sell": ["sell"],
        "cent": ["cent"],
        "sent": ["sent"],
        "scent": ["scent"],
        "chord": ["chord"],
        "cord": ["cord"],
        "cite": ["cite"],
        "site": ["site"],
        "sight": ["sight"],
        "clothes": ["clothes"],
        "cloths": ["cloths"],
        "compliment": ["compliment"],
        "complement": ["complement"],
        "council": ["council"],
        "counsel": ["counsel"],
        "desert": ["desert"],
        "dessert": ["dessert"],
        "device": ["device"],
        "devise": ["devise"],
        "die": ["die"],
        "dye": ["dye"],
        "emigrate": ["emigrate"],
        "immigrate": ["immigrate"],
        "fair": ["fair"],
        "fare": ["fare"],
        "hear": ["hear"],
        "here": ["here"],
        "hole": ["hole"],
        "whole": ["whole"],
        "lead": ["lead"],
        "led": ["led"],
        "loan": ["loan"],
        "lone": ["lone"],
        "lose": ["lose"],
        "loose": ["loose"],
        "passed": ["passed"],
        "past": ["past"],
        "peace": ["peace"],
        "piece": ["piece"],
        "plain": ["plain"],
        "plane": ["plane"],
        "practice": ["practice"],
        "practise": ["practise"],
        "presence": ["presence"],
        "presents": ["presents"],
        "quiet": ["quiet"],
        "quite": ["quite"],
        "right": ["right"],
        "write": ["write"],
        "rite": ["rite"],
        "road": ["road"],
        "rode": ["rode"],
        "rowed": ["rowed"],
        "scene": ["scene"],
        "seen": ["seen"],
        "seam": ["seam"],
        "seem": ["seem"],
        "shear": ["shear"],
        "sheer": ["sheer"],
        "soar": ["soar"],
        "sore": ["sore"],
        "stair": ["stair"],
        "stare": ["stare"],
        "steel": ["steel"],
        "steal": ["steal"],
        "tail": ["tail"],
        "tale": ["tale"],
        "there": ["there"],
        "their": ["their"],
        "they're": ["they're"],
        "through": ["through"],
        "threw": ["threw"],
        "thru": ["through"],
        "to": ["to"],
        "too": ["too"],
        "two": ["two"],
        "vain": ["vain"],
        "vein": ["vein"],
        "van": ["van"],
        "waist": ["waist"],
        "waste": ["waste"],
        "wait": ["wait"],
        "weight": ["weight"],
        "which": ["which"],
        "witch": ["witch"],
        "wood": ["wood"],
        "would": ["would"],
        "write": ["write"],
        "right": ["right"],
        "wrote": ["wrote"],
        "written": ["written"],
    }
    
    if word_lower in common_mistakes:
        suggestions = common_mistakes[word_lower]
    
    return suggestions


def build_correction_message(result: GrammarResult) -> Optional[str]:
    """Format grammar check result as user-readable message."""
    if not result.has_errors:
        return None

    lines = ["[Grammar Tips]"]
    for i, issue in enumerate(result.issues[:3], 1):
        lines.append(
            f"{i}. [{issue.original}] -> [{issue.suggestion}] - {issue.explanation}"
        )
    if result.error_count > 3:
        lines.append(f"Plus {result.error_count - 3} more suggestions.")
    return "\n".join(lines)
