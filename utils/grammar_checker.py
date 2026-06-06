"""
语法纠错辅助模块 —— 基于规则检测常见 ESL 错误并给出修正建议。

原创贡献：错误模式库、纠错提示文案生成逻辑。
"""

import re
from dataclasses import dataclass, field


@dataclass
class GrammarIssue:
    """单条语法问题记录。"""
    original: str
    suggestion: str
    explanation: str
    severity: str = "medium"  # low | medium | high


@dataclass
class GrammarResult:
    """语法检查结果。"""
    issues: list[GrammarIssue] = field(default_factory=list)
    error_count: int = 0
    has_errors: bool = False
    original_text: str = ""

    def to_dict(self) -> dict:
        return {
            "has_errors": self.has_errors,
            "error_count": self.error_count,
            "original": self.original_text,
            "issues": [
                {
                    "original": i.original,
                    "suggestion": i.suggestion,
                    "explanation": i.explanation,
                    "severity": i.severity,
                }
                for i in self.issues
            ],
        }


# (pattern, replacement, explanation, severity)
_GRAMMAR_RULES: list[tuple[str, str, str, str]] = [
    (
        r"\bI\s+are\b",
        "I am",
        "'I' 应搭配 'am'，不能用 'are'。",
        "high",
    ),
    (
        r"\bI\s+is\b",
        "I am",
        "'I' 应搭配 'am'，不能用 'is'。",
        "high",
    ),
    (
        r"\b(he|she|it)\s+don't\b",
        r"\1 doesn't",
        "第三人称单数应使用 'doesn't'。",
        "high",
    ),
    (
        r"\b(he|she|it)\s+are\b",
        r"\1 is",
        "第三人称单数应使用 'is'。",
        "high",
    ),
    (
        r"\b(they|we|you)\s+is\b",
        r"\1 are",
        "复数主语应使用 'are'。",
        "high",
    ),
    (
        r"\ba\s+([aeiouAEIOU]\w+)\b",
        r"an \1",
        "元音开头的单词前应使用 'an'。",
        "medium",
    ),
    (
        r"\ban\s+([^aeiouAEIOU\s]\w+)\b",
        r"a \1",
        "辅音开头的单词前应使用 'a'。",
        "medium",
    ),
    (
        r"\bdon't\s+no\b",
        "don't know",
        "双重否定在标准英语中应避免。",
        "medium",
    ),
    (
        r"\bmore\s+better\b",
        "better",
        "'better' 本身已是比较级，不需要 'more'。",
        "medium",
    ),
    (
        r"\bvery\s+unique\b",
        "unique",
        "'unique' 表示独一无二，通常不与 'very' 连用。",
        "low",
    ),
    (
        r"\bgo\s+to\s+home\b",
        "go home",
        "'home' 作副词时不需要 'to'。",
        "medium",
    ),
    (
        r"\bmake\s+a\s+photo\b",
        "take a photo",
        "拍照应说 'take a photo'，不是 'make a photo'。",
        "medium",
    ),
    (
        r"\bexplain\s+me\b",
        "explain to me",
        "'explain' 后需要加 'to' 再接人称代词。",
        "medium",
    ),
    (
        r"\bdiscuss\s+about\b",
        "discuss",
        "'discuss' 本身已含 'about' 之意，无需再加。",
        "low",
    ),
    (
        r"\bhow\s+much\s+persons\b",
        "how many people",
        "询问人数应使用 'how many people'。",
        "medium",
    ),
]


def check_grammar(text: str) -> GrammarResult:
    """
    检测文本中的常见语法错误。

    Args:
        text: 用户输入的英文句子。

    Returns:
        GrammarResult 包含发现的问题列表。
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

            result.issues.append(
                GrammarIssue(
                    original=original,
                    suggestion=suggested,
                    explanation=explanation,
                    severity=severity,
                )
            )

    # 句首未大写
    stripped = text.strip()
    if stripped and stripped[0].islower() and stripped[0].isalpha():
        result.issues.append(
            GrammarIssue(
                original=stripped[0],
                suggestion=stripped[0].upper(),
                explanation="英文句子开头应大写。",
                severity="low",
            )
        )

    # 缺少句末标点
    if stripped and stripped[-1] not in ".!?":
        result.issues.append(
            GrammarIssue(
                original="(句末)",
                suggestion=".",
                explanation="完整句子建议以句号、问号或感叹号结尾。",
                severity="low",
            )
        )

    result.error_count = len(result.issues)
    result.has_errors = result.error_count > 0
    return result


def build_correction_message(result: GrammarResult) -> str | None:
    """将语法检查结果格式化为用户可读的纠错提示。"""
    if not result.has_errors:
        return None

    lines = ["📝 **Grammar Tips:**"]
    for i, issue in enumerate(result.issues[:3], 1):
        lines.append(
            f"{i}. 「{issue.original}」→ 「{issue.suggestion}」"
            f" — {issue.explanation}"
        )
    if result.error_count > 3:
        lines.append(f"   ...还有 {result.error_count - 3} 处可改进的地方。")
    return "\n".join(lines)
