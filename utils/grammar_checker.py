"""
Grammar checker module - detects common ESL errors and provides correction suggestions.
"""

import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Dict, Tuple

from .word_list import unknown, correction


@dataclass
class GrammarIssue:
    """Single grammar issue record."""
    original: str
    suggestion: str
    explanation: str
    severity: str = "medium"  # low | medium | high
    level: str = "format"  # format | word | grammar
    category: str = "general"


@dataclass
class GrammarResult:
    """Grammar check result."""
    issues: List[GrammarIssue] = field(default_factory=list)
    error_count: int = 0
    has_errors: bool = False
    original_text: str = ""
    corrected_text: str = ""

    def to_dict(self) -> Dict:
        return {
            "has_errors": self.has_errors,
            "error_count": self.error_count,
            "original": self.original_text,
            "corrected_text": self.corrected_text,
            "issues": [
                {
                    "original": i.original,
                    "suggestion": i.suggestion,
                    "description": i.explanation,
                    "severity": i.severity,
                    "level": i.level,
                    "category": i.category,
                }
                for i in self.issues
            ],
        }


# ---------------------------------------------------------------------------
# a/an 例外词（字母与发音不一致）
# ---------------------------------------------------------------------------
_USE_A_BEFORE = frozenset(
    {"university", "european", "unicorn", "useful", "unit", "one", "once"}
)
_USE_AN_BEFORE = frozenset(
    {"hour", "honest", "honor", "honour", "heir", "hourly"}
)

# 第三人称单数：不规则动词
_THIRD_PERSON_FORMS = {
    "have": "has",
    "do": "does",
    "go": "goes",
}

# 可数名词常见单数形式（用于检测遗漏 -s）
_COUNTABLE_SINGULARS = frozenset(
    {
        "book", "apple", "child", "person", "mouse", "dog", "cat",
        "student", "teacher", "car", "friend", "egg", "sandwich",
    }
)

# 不可数名词（many + 不可数 为错误）
_UNCOUNTABLE_NOUNS = frozenset(
    {
        "information", "advice", "furniture", "equipment", "homework",
        "news", "bread", "money", "water", "traffic", "luggage",
        "progress", "research", "weather",
    }
)

# 规则元组: (pattern, replacement, explanation, severity, category)
# replacement=None 表示需要特殊处理函数
_GRAMMAR_RULES: List[Tuple] = [
    # --- 主谓一致（原有）---
    (r"\bI\s+are\b", "I am", "主语 I 应搭配 am，不能用 are。", "high", "subject_verb"),
    (r"\bI\s+is\b", "I am", "主语 I 应搭配 am，不能用 is。", "high", "subject_verb"),
    (
        r"\b(he|she|it)\s+don't\b",
        r"\1 doesn't",
        "第三人称单数应使用 doesn't。",
        "high",
        "subject_verb",
    ),
    (
        r"\b(he|she|it)\s+are\b",
        r"\1 is",
        "第三人称单数应使用 is。",
        "high",
        "subject_verb",
    ),
    (
        r"\b(they|we|you)\s+is\b",
        r"\1 are",
        "复数主语应使用 are。",
        "high",
        "subject_verb",
    ),
    # --- 冠词 a/an（原有，配合例外词函数进一步校验）---
    (
        r"\ba\s+([aeiouAEIOU]\w+)\b",
        r"an \1",
        "元音发音开头的单词前应使用 an。",
        "medium",
        "article",
    ),
    (
        r"\ban\s+([^aeiouAEIOU\s]\w+)\b",
        r"a \1",
        "辅音发音开头的单词前应使用 a。",
        "medium",
        "article",
    ),
    (
        r"\bin\s+a\s+hour\b",
        "in an hour",
        "hour 发音以元音开头，应使用 an hour。",
        "medium",
        "article",
    ),
    (
        r"\ban\s+(university|european|unicorn|useful|unit|one)\b",
        r"a \1",
        "该词以辅音音素开头，应使用 a 而非 an。",
        "medium",
        "article",
    ),
    (
        r"\ba\s+(hour|honest|honor|honour|heir)\b",
        r"an \1",
        "该词以元音音素开头，应使用 an 而非 a。",
        "medium",
        "article",
    ),
    # --- 介词错误 ---
    (
        r"\bon\s+the\s+morning\b",
        "in the morning",
        "表示在早上应使用 in the morning，不用 on。",
        "medium",
        "preposition",
    ),
    (
        r"\bin\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
        r"on \1",
        "星期几前应使用 on，不用 in。",
        "medium",
        "preposition",
    ),
    (
        r"\bon\s+night\b",
        "at night",
        "表示在夜间应使用 at night，不用 on night。",
        "medium",
        "preposition",
    ),
    (
        r"\barrive\s+to\b",
        "arrive at",
        "arrive 后接地点通常用 at/in，不用 to。",
        "medium",
        "preposition",
    ),
    (
        r"\blisten\s+(music|radio|the\s+music|the\s+radio)\b",
        r"listen to \1",
        "listen 后需加 to，如 listen to music。",
        "medium",
        "preposition",
    ),
    (
        r"\bdepend\s+of\b",
        "depend on",
        "固定搭配是 depend on，不是 depend of。",
        "medium",
        "collocation",
    ),
    (
        r"\bwait\s+(me|him|her|us|them|you)\b",
        r"wait for \1",
        "wait 后需加 for，如 wait for me。",
        "medium",
        "preposition",
    ),
    (
        r"\binterested\s+for\b",
        "interested in",
        "固定搭配是 interested in，不是 interested for。",
        "medium",
        "collocation",
    ),
    (
        r"\baccording\s+to\s+of\b",
        "according to",
        "according to 本身已完整，不需要再加 of。",
        "low",
        "collocation",
    ),
    (
        r"\blook\s+forward\s+to\s+(see|go|meet|visit|watch|hear)\b",
        r"look forward to \1ing",
        "look forward to 后接动名词（-ing），不接动词原形。",
        "medium",
        "collocation",
    ),
    # --- 动词时态 / 形式 ---
    (
        r"\bi\s+(goes|does|has|wants|likes|needs|works|plays|studies)\b",
        None,
        "第一人称 I 后不应使用第三人称单数动词形式。",
        "high",
        "tense",
    ),
    (
        r"\b(have|has|had)\b(?:\s+(?:I|you|he|she|it|we|they|this|that|these|those|someone|something|anything|nothing|everything|anyone|everyone|noone|one))?\s+(?!to\b)(hear|see|go|do|make|take|give|get|write|speak|tell|think|know|come|become|feel|find|keep|leave|let|put|say|send|set|show|sing|sit|sleep|stand|understand|wear|win)\b",
        None,
        "现在完成时后应使用过去分词，不是动词原形。",
        "high",
        "tense",
    ),
    (
        r"\b(buyed|goed|writed|speaked|telled|thinked|knowed|comed|becomed|feeled|finded|keepped|leaved|letted|putted)s?\b",
        None,
        "不规则动词形式错误，请使用正确的过去式/过去分词。",
        "high",
        "tense",
    ),
    # --- 名词单复数 ---
    (
        r"\bmany\s+(information|advice|furniture|equipment|homework|news|bread|money|water|traffic|luggage|progress|research|weather)\b",
        None,
        "这些名词不可数，应使用 much 或 a piece of 等，不用 many。",
        "medium",
        "noun_number",
    ),
    (
        r"\bmuch\s+(books|apples|cars|students|children|dogs|friends|people|eggs|sandwiches|teachers)\b",
        None,
        "可数名词复数前应使用 many，不用 much。",
        "medium",
        "noun_number",
    ),
    (
        r"\b(two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(book|apple|child|person|mouse|dog|cat|student|friend|egg|sandwich)\b(?!\s*s\b)",
        None,
        "数量大于 1 时，可数名词通常需用复数形式。",
        "medium",
        "noun_number",
    ),
    # --- 词性混淆 ---
    (
        r"\b(run|runs|walk|walks|drive|drives|work|works|speak|speaks|study|studies|eat|eats|listen|listens)\s+(quick|slow|careful|easy|hard|quiet|loud|clear|safe)\b",
        None,
        "修饰动词应使用副词（如 quickly），不是形容词。",
        "medium",
        "word_form",
    ),
    (
        r"\b(do|did|does)\s+(good|bad)\b",
        None,
        "修饰动词应使用副词 well/badly，不是形容词 good/bad。",
        "medium",
        "word_form",
    ),
    (
        r"\b(real)\s+(good|nice|bad|big|small|fast|slow)\b",
        r"really \2",
        "修饰形容词应使用副词 really，不是 real。",
        "medium",
        "word_form",
    ),
    # --- 其他常见错误（原有）---
    (r"\bdon't\s+no\b", "don't know", "应避免双重否定。", "medium", "general"),
    (
        r"\bmore\s+better\b",
        "better",
        "better 本身是比较级，不需要 more。",
        "medium",
        "general",
    ),
    (
        r"\bmore\s+(better|worse|best|worst)\b",
        None,
        "比较级/最高级前不需要 more/most。",
        "medium",
        "general",
    ),
    (r"\bvery\s+unique\b", "unique", "unique 表示独一无二，通常不与 very 连用。", "low", "general"),
    (r"\bgo\s+to\s+home\b", "go home", "home 作副词时不需要 to。", "medium", "preposition"),
    (
        r"\bmake\s+a\s+photo\b",
        "take a photo",
        "拍照应说 take a photo，不是 make a photo。",
        "medium",
        "collocation",
    ),
    (
        r"\bexplain\s+me\b",
        "explain to me",
        "explain 后接人称代词需加 to。",
        "medium",
        "preposition",
    ),
    (r"\bdiscuss\s+about\b", "discuss", "discuss 本身已含 about 之意。", "low", "collocation"),
    (
        r"\bhow\s+much\s+persons\b",
        "how many people",
        "询问人数应使用 how many people。",
        "medium",
        "noun_number",
    ),
    (
        r"\b[a-zA-Z]{2,}[0-9][a-zA-Z]{0,3}\b",
        None,
        "包含数字的疑似拼写错误。",
        "high",
        "word",
    ),
]

# 副词映射（形容词 -> 副词）
_ADJ_TO_ADV = {
    "quick": "quickly",
    "slow": "slowly",
    "careful": "carefully",
    "easy": "easily",
    "hard": "hardly",  # 注意：hardly=几乎不，但 ESL 常见错误是 hard
    "quiet": "quietly",
    "loud": "loudly",
    "clear": "clearly",
    "safe": "safely",
    "good": "well",
    "bad": "badly",
}

# 可数名词复数不规则变化
_PLURAL_FORMS = {
    "child": "children",
    "person": "people",
    "mouse": "mice",
}

# 常见不规则动词表
_IRREGULAR_VERBS = {
    "hear": "heard",
    "see": "seen",
    "go": "gone",
    "do": "done",
    "make": "made",
    "take": "taken",
    "give": "given",
    "get": "got",
    "write": "written",
    "speak": "spoken",
    "tell": "told",
    "think": "thought",
    "know": "known",
    "come": "come",
    "become": "become",
    "feel": "felt",
    "find": "found",
    "keep": "kept",
    "leave": "left",
    "let": "let",
    "put": "put",
    "say": "said",
    "send": "sent",
    "set": "set",
    "show": "shown",
    "sing": "sung",
    "sit": "sat",
    "sleep": "slept",
    "stand": "stood",
    "understand": "understood",
    "wear": "worn",
    "win": "won",
    "buy": "bought",
}

# 第三人称单数检测用的动词原形
_THIRD_PERSON_VERBS = frozenset(
    {
        "go", "do", "have", "want", "need", "like", "know", "think",
        "work", "play", "eat", "drink", "live", "study", "speak",
        "run", "walk", "read", "write", "see", "take", "make", "get",
    }
)

_PUNCTUATION_MAP = {
    "，": ",",
    "。": ".",
    "？": "?",
    "！": "!",
    "；": ";",
    "：": ":",
    """: '"',
    """: '"',
    "'": "'",
    "'": "'",
    "（": "(",
    "）": ")",
    "【": "[",
    "】": "]",
    "《": "<",
    "》": ">",
    "——": "--",
    "…": "...",
    "·": ".",
}


def _is_meta_issue(issue: GrammarIssue) -> bool:
    """判断是否为元信息类 issue（如句末标点），不能直接在原文中 replace。"""
    return issue.original.startswith("(") and issue.original.endswith(")")


def _apply_issue_to_text(text: str, issue: GrammarIssue) -> str:
    """将单条 issue 应用到文本，返回更新后的文本。"""
    if not issue.suggestion or issue.original == issue.suggestion:
        return text

    if _is_meta_issue(issue):
        if "句末" in issue.original or "句尾" in issue.original:
            stripped = text.rstrip().rstrip(",;:")
            if stripped and stripped[-1] not in ".!?":
                return stripped + issue.suggestion
        return text

    escaped = re.escape(issue.original)
    return re.sub(escaped, issue.suggestion, text, count=1, flags=re.IGNORECASE)


def build_corrected_text(text: str, issues: List[GrammarIssue]) -> str:
    """
    根据所有 issue 生成完整修正句。
    先应用词汇/语法替换，最后统一处理句末标点。
    """
    if not text or not text.strip():
        return text

    corrected = text.strip()

    # 逗号后补空格
    corrected = re.sub(r",(\S)", r", \1", corrected)

    meta_issues = []
    replace_issues = []

    for issue in issues:
        if _is_meta_issue(issue) or (
            issue.level == "format"
            and issue.suggestion == "."
            and issue.original not in corrected
        ):
            meta_issues.append(issue)
        else:
            replace_issues.append(issue)

    for issue in replace_issues:
        corrected = _apply_issue_to_text(corrected, issue)

    # 句首大写（若 issue 中有）
    stripped = corrected.lstrip()
    if stripped and stripped[0].islower() and stripped[0].isalpha():
        corrected = stripped[0].upper() + stripped[1:]

    # 句末标点：移除尾部逗号/分号/冒号，再补句号
    corrected = corrected.rstrip()
    corrected = re.sub(r"[,;:]+$", "", corrected)
    if corrected and corrected[-1] not in ".!?":
        corrected += "."

    return corrected


def _check_missing_article(text: str) -> List[GrammarIssue]:
    """检测 want/need/like/buy/order 后遗漏冠词的情况。"""
    issues = []
    pattern = (
        r"\b(I|we|they|you)\s+(want|need|like|buy|order)\s+"
        r"(?!a\s|an\s|the\s|some\s|any\s|my\s|your\s|his\s|her\s|to\s|one\s)"
        r"([a-z]{3,})\b"
    )
    for match in re.finditer(pattern, text, re.IGNORECASE):
        noun = match.group(3).lower()
        if noun in _UNCOUNTABLE_NOUNS or noun.endswith("s"):
            continue
        article = "an" if noun[0] in "aeiou" and noun not in _USE_A_BEFORE else "a"
        if noun in _USE_AN_BEFORE:
            article = "an"
        original = match.group(0)
        suggestion = re.sub(
            rf"\b{re.escape(match.group(3))}\b",
            f"{article} {match.group(3)}",
            original,
            count=1,
            flags=re.IGNORECASE,
        )
        issues.append(
            GrammarIssue(
                original=original,
                suggestion=suggestion,
                explanation=f"可数名词 '{match.group(3)}' 前通常需要冠词 {article}。",
                severity="medium",
                level="grammar",
                category="article",
            )
        )
    return issues


def _check_third_person_s(text: str) -> List[GrammarIssue]:
    """检测第三人称单数遗漏 -s / has / does。"""
    issues = []
    pattern = (
        r"\b(he|she|it)\s+(" + "|".join(_THIRD_PERSON_VERBS) + r")\b"
        r"(?!s\b)(?!ing\b)"
    )
    for match in re.finditer(pattern, text, re.IGNORECASE):
        verb = match.group(2).lower()
        if verb.endswith("s"):
            continue
        corrected_verb = _THIRD_PERSON_FORMS.get(verb, verb + "s")
        original = match.group(0)
        suggestion = re.sub(
            rf"\b{re.escape(match.group(2))}\b",
            corrected_verb,
            original,
            count=1,
            flags=re.IGNORECASE,
        )
        issues.append(
            GrammarIssue(
                original=original,
                suggestion=suggestion,
                explanation=f"第三人称单数 '{match.group(1)}' 后的动词 '{verb}' 应变为 '{corrected_verb}'。",
                severity="high",
                level="grammar",
                category="tense",
            )
        )
    return issues


def _resolve_special_suggestion(
    original: str, explanation: str, replacement
) -> Optional[str]:
    """处理 replacement=None 的特殊规则，生成建议文本。"""
    lower = original.lower()

    if "第一人称" in explanation:
        mapping = {
            "goes": "go", "does": "do", "has": "have", "wants": "want",
            "likes": "like", "needs": "need", "works": "work", "plays": "play",
            "studies": "study",
        }
        for wrong, right in mapping.items():
            if wrong in lower:
                return re.sub(rf"\b{wrong}\b", right, original, flags=re.IGNORECASE)

    if "过去分词" in explanation:
        words = re.findall(r"\b[a-zA-Z]+\b", original)
        aux = {"have", "has", "had", "be", "been", "being", "am", "is", "are",
               "was", "were", "do", "does", "did", "will", "would", "could",
               "should", "may", "might", "must", "can"}
        for w in words:
            wl = w.lower()
            if wl in aux:
                continue
            if wl in _IRREGULAR_VERBS:
                return original.replace(w, _IRREGULAR_VERBS[wl], 1)

    if "不规则动词" in explanation:
        wrong = re.search(r"\b([a-zA-Z]+ed)\b", original, re.IGNORECASE)
        if wrong:
            matched = wrong.group(1).lower()
            base = matched[:-2] if matched.endswith("ed") else matched.rstrip("ed")
            if base in _IRREGULAR_VERBS:
                return original.replace(wrong.group(0), _IRREGULAR_VERBS[base], 1)

    if "不可数" in explanation and "many" in lower:
        noun_match = re.search(
            r"\bmany\s+(\w+)\b", original, re.IGNORECASE
        )
        if noun_match:
            noun = noun_match.group(1)
            return re.sub(
                rf"\bmany\s+{re.escape(noun)}\b",
                f"much {noun}",
                original,
                flags=re.IGNORECASE,
            )

    if "many" in explanation and "much" in lower:
        noun_match = re.search(r"\bmuch\s+(\w+)\b", original, re.IGNORECASE)
        if noun_match:
            noun = noun_match.group(1)
            plural = _PLURAL_FORMS.get(noun.lower(), noun + "s")
            return re.sub(
                rf"\bmuch\s+{re.escape(noun)}\b",
                f"many {plural}",
                original,
                flags=re.IGNORECASE,
            )

    if "复数形式" in explanation:
        m = re.search(
            r"\b(two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(\w+)\b",
            original,
            re.IGNORECASE,
        )
        if m:
            noun = m.group(2)
            plural = _PLURAL_FORMS.get(noun.lower(), noun + "s")
            return re.sub(
                rf"\b{re.escape(noun)}\b",
                plural,
                original,
                count=1,
                flags=re.IGNORECASE,
            )

    if "副词" in explanation and "修饰动词" in explanation:
        m = re.search(
            r"\b(\w+)\s+(quick|slow|careful|easy|hard|quiet|loud|clear|safe|good|bad)\b",
            original,
            re.IGNORECASE,
        )
        if m:
            adj = m.group(2).lower()
            adv = _ADJ_TO_ADV.get(adj)
            if adv:
                if adj == "hard":
                    adv = "hard"  # ESL 常见：work hard 是正确的
                return re.sub(
                    rf"\b{re.escape(m.group(2))}\b",
                    adv,
                    original,
                    count=1,
                    flags=re.IGNORECASE,
                )

    if "look forward to" in lower and "ing" in explanation:
        m = re.search(r"\bto\s+(\w+)\b", original, re.IGNORECASE)
        if m:
            verb = m.group(1)
            if not verb.endswith("ing"):
                gerund = verb + "ing"
                if verb.endswith("e"):
                    gerund = verb[:-1] + "ing"
                return re.sub(
                    rf"\bto\s+{re.escape(verb)}\b",
                    f"to {gerund}",
                    original,
                    flags=re.IGNORECASE,
                )

    if "more/most" in explanation:
        m = re.search(r"\bmore\s+(\w+)\b", original, re.IGNORECASE)
        if m:
            return re.sub(r"\bmore\s+", "", original, count=1, flags=re.IGNORECASE)

    if "数字" in explanation and "疑似拼写" in explanation:
        return _suggest_digit_fix(original)

    return None


def _suggest_digit_fix(original: str) -> str:
    """数字代替字母的拼写修复。"""
    digit_map = {
        "0": ["o", "O"],
        "1": ["l", "i", "I"],
        "3": ["e", "E"],
        "4": ["a", "A"],
        "5": ["s", "S"],
        "7": ["t", "T"],
        "8": ["b", "B"],
    }
    word = original.strip()

    def generate(word_str: str, idx: int = 0) -> List[str]:
        if idx >= len(word_str):
            return [word_str]
        ch = word_str[idx]
        if ch in digit_map:
            results = []
            for rep in digit_map[ch]:
                results.extend(generate(word_str[:idx] + rep + word_str[idx + 1 :], idx + 1))
            results.extend(generate(word_str, idx + 1))
            return results
        return generate(word_str, idx + 1)

    try:
        for candidate in set(generate(word)):
            if len(candidate) > 2 and not unknown([candidate.lower()]):
                return candidate
        similar = correction(word.replace("0", "o").replace("1", "i").replace("3", "e"))
        if similar:
            return similar
    except Exception:
        pass
    return original


def _fix_punctuation(text: str) -> Tuple[str, List[GrammarIssue]]:
    """Fix punctuation issues in text."""
    issues = []
    fixed = text
    has_chinese_punct = False

    for cn_punct, en_punct in _PUNCTUATION_MAP.items():
        if cn_punct in fixed:
            has_chinese_punct = True
            if cn_punct in "，。？！；：":
                fixed = fixed.replace(cn_punct, en_punct + " ")
                fixed = " ".join(fixed.split())
            else:
                fixed = fixed.replace(cn_punct, en_punct)
            if cn_punct in "，。？！；：":
                issues.append(
                    GrammarIssue(
                        original=cn_punct,
                        suggestion=en_punct,
                        explanation=f"中文标点 '{cn_punct}' 应替换为英文标点 '{en_punct}'",
                        severity="low",
                        level="format",
                        category="format",
                    )
                )

    # 逗号后补空格
    if re.search(r",(\S)", fixed):
        issues.append(
            GrammarIssue(
                original=re.search(r",(\S)", fixed).group(0),
                suggestion=re.sub(r",(\S)", r", \1", re.search(r",(\S)", fixed).group(0)),
                explanation="逗号后应加空格。",
                severity="low",
                level="format",
                category="format",
            )
        )
        fixed = re.sub(r",(\S)", r", \1", fixed)

    stripped = fixed.rstrip()
    if stripped:
        last_char = stripped[-1]
        if last_char in ",;:":
            issues.append(
                GrammarIssue(
                    original=last_char,
                    suggestion=".",
                    explanation=f"句尾不应使用 '{last_char}'，应使用句号。",
                    severity="low",
                    level="format",
                    category="format",
                )
            )
        elif last_char not in ".!?\")'":
            if not has_chinese_punct:
                issues.append(
                    GrammarIssue(
                        original="(句末)",
                        suggestion=".",
                        explanation="句尾补充英文句号。",
                        severity="low",
                        level="format",
                        category="format",
                    )
                )

    return fixed, issues


def check_grammar(text: str) -> GrammarResult:
    """
    Detect common grammar errors in text.

    Args:
        text: User's English input.

    Returns:
        GrammarResult containing detected issues and corrected_text.
    """
    result = GrammarResult()
    result.original_text = text
    if not text or not text.strip():
        result.corrected_text = text
        return result

    for pattern, replacement, explanation, severity, category in _GRAMMAR_RULES:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            original = match.group(0)
            suggested = None

            if isinstance(replacement, str) and r"\1" in replacement:
                suggested = re.sub(pattern, replacement, original, flags=re.IGNORECASE)
            elif replacement is not None:
                suggested = re.sub(
                    pattern, replacement, original, count=1, flags=re.IGNORECASE
                )
            else:
                suggested = _resolve_special_suggestion(original, explanation, replacement)

            level = "grammar" if severity == "high" else "word"
            if category in ("format",):
                level = "format"

            if suggested is not None and suggested != original:
                result.issues.append(
                    GrammarIssue(
                        original=original,
                        suggestion=suggested,
                        explanation=explanation,
                        severity=severity,
                        level=level,
                        category=category,
                    )
                )

    result.issues.extend(_check_missing_article(text))
    result.issues.extend(_check_third_person_s(text))

    stripped = text.strip()
    if stripped and stripped[0].islower() and stripped[0].isalpha():
        result.issues.append(
            GrammarIssue(
                original=stripped[0],
                suggestion=stripped[0].upper(),
                explanation=f"句首字母 {stripped[0]} 应大写为 {stripped[0].upper()}。",
                severity="low",
                level="format",
                category="format",
            )
        )

    _, punct_issues = _fix_punctuation(text)
    result.issues.extend(punct_issues)

    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    for word in unknown(words):
        if len(word) < 3:
            continue
        correction_word = correction(word)
        if correction_word:
            result.issues.append(
                GrammarIssue(
                    original=word,
                    suggestion=correction_word,
                    explanation=f"'{word}' 可能拼写错误，建议改为 '{correction_word}'。",
                    severity="medium",
                    level="word",
                    category="spelling",
                )
            )

    result.error_count = len(result.issues)
    result.has_errors = result.error_count > 0
    result.corrected_text = build_corrected_text(text, result.issues)
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


def get_corrected_text(text: str) -> str:
    """Get the corrected version of input text with all fixes applied."""
    if not text or not text.strip():
        return text
    result = check_grammar(text)
    return result.corrected_text
