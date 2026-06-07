"""
Grammar checker module - detects common ESL errors and provides correction suggestions.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from .word_list import unknown, correction


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

    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    misspelled = unknown(words)
    for word in misspelled:
        if len(word) < 3:
            continue
        correction_word = correction(word)
        if correction_word:
            result.issues.append(
                GrammarIssue(
                    original=word,
                    suggestion=correction_word,
                    explanation=f"{word} 可能拼写错误，正确单词：{correction_word}",
                    severity="medium",
                    level="word",
                )
            )

    result.error_count = len(result.issues)
    result.has_errors = result.error_count > 0
    
    return result


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
