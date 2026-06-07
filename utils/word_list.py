import os
import urllib.request
import urllib.error
from pathlib import Path

_WORD_LIST_URL = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
_CACHE_DIR = Path(__file__).parent / ".cache"
_CACHE_FILE = _CACHE_DIR / "words_alpha.txt"

_known_words: set = None
_len_index: dict = None


def _ensure_word_list():
    global _known_words, _len_index
    if _known_words is not None:
        return

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if not _CACHE_FILE.exists():
        _download_word_list()

    if not _CACHE_FILE.exists():
        raise RuntimeError(
            "无法下载英文词表。请确保网络连接正常，首次运行会自动下载词表文件。"
        )

    with open(_CACHE_FILE, "r", encoding="utf-8") as f:
        _known_words = {line.strip().lower() for line in f if line.strip()}

    _len_index = {}
    for w in _known_words:
        _len_index.setdefault(len(w), []).append(w)


def _download_word_list():
    try:
        req = urllib.request.Request(
            _WORD_LIST_URL, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
        with open(_CACHE_FILE, "wb") as f:
            f.write(data)
        print(f"英文词表已下载并缓存至 {_CACHE_FILE}")
    except (urllib.error.URLError, OSError) as e:
        print(f"词表下载失败: {e}")
        print(f"请手动下载词表文件到 {_CACHE_FILE}")
        print(f"下载地址: {_WORD_LIST_URL}")


def unknown(words):
    _ensure_word_list()
    return {w for w in words if w.lower() not in _known_words}


def correction(word):
    _ensure_word_list()
    word_lower = word.lower()
    if word_lower in _known_words:
        return word_lower
    return _closest_word(word_lower)


def _closest_word(word, max_distance=2):
    if len(word) < 3:
        return word

    candidates = []
    for delta in range(-max_distance, max_distance + 1):
        target_len = len(word) + delta
        if target_len >= 3 and target_len in _len_index:
            candidates.extend(_len_index[target_len])

    best = None
    best_dist = max_distance + 1
    for known in candidates:
        dist = _levenshtein(word, known)
        if dist < best_dist:
            best_dist = dist
            best = known
            if dist == 1:
                break
    return best if best is not None else word


def _levenshtein(a, b):
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(
                prev[j + 1] + 1,
                curr[j] + 1,
                prev[j] + (0 if ca == cb else 1),
            ))
        prev = curr
    return prev[-1]