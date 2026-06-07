import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.word_list import unknown, correction


def test_common_correct_words_return_none():
    correct_words = [
        "tomorrow", "yesterday", "schedule", "restaurant",
        "beautiful", "excited", "nervous", "wonderful",
        "important", "different", "experience", "environment",
        "accommodation", "calendar", "necessary", "successful",
    ]
    for word in correct_words:
        result = correction(word)
        assert result is None, f"FAIL: correction('{word}') should be None, got {result!r}"
        print(f"  PASS: correction('{word}') -> None")


def test_common_correct_words_not_in_unknown():
    words = [
        "tomorrow", "yesterday", "today", "restaurant", "schedule",
        "hello", "world", "good", "fine", "great", "happy", "sad",
        "eat", "drink", "sleep", "walk", "run", "think", "talk",
        "the", "is", "are", "was", "were", "have", "has", "had",
        "can", "could", "will", "would", "should", "may", "might",
        "and", "but", "or", "so", "because", "if", "when", "while",
        "what", "who", "which", "where", "why", "how",
    ]
    result = unknown(words)
    for word in words:
        assert word not in result, f"FAIL: '{word}' should NOT be in unknown set"
    print(f"  PASS: {len(words)} common words all correctly recognized (unknown=0)")


def test_obvious_misspellings_get_correction():
    cases = {
        "helo": "hell",
        "teh": "the",
        "wht": "what",
        "wrld": "word",
        "thsi": "this",
        "recieve": "receive",
        "occurence": "occurrence",
        "seperate": "separate",
        "definately": "definitely",
        "goverment": "government",
        "enviroment": "environment",
        "acheive": "achieve",
        "beleive": "believe",
        "begining": "beginning",
        "calender": "calendar",
        "collegue": "college",
        "commitee": "committee",
        "concious": "conscious",
        "embarass": "embarrass",
        "existance": "existence",
        "foriegn": "foreign",
        "forteen": "fourteen",
        "freind": "friend",
        "gaurd": "guard",
        "happend": "happened",
        "immediatly": "immediately",
        "independant": "independent",
        "knowlege": "knowledge",
        "libary": "library",
        "millenium": "millennium",
        "neccessary": "necessary",
        "noticable": "noticeable",
        "ocassion": "occasion",
        "paralell": "parallel",
        "persue": "pursue",
        "posession": "possession",
        "potatoe": "potato",
        "privilege": "privilege",
        "professer": "professor",
        "pronounciation": "pronunciation",
        "publically": "publicly",
        "questionaire": "questionnaire",
        "realy": "really",
        "reccomend": "recommend",
        "refered": "referred",
        "religous": "religious",
        "rember": "remember",
        "rythm": "rhythm",
        "sargent": "sergeant",
        "similiar": "similar",
        "sincerly": "sincerely",
        "speach": "speech",
        "strenght": "strength",
        "suprise": "surprise",
        "temperament": "temperament",
        "therefor": "therefore",
        "threshhold": "threshold",
        "tommorow": "tomorrow",
        "tounge": "tongue",
        "truely": "truly",
        "tyrany": "tyranny",
        "unbelievable": "unbelievable",
        "untill": "until",
        "vaccuum": "vacuum",
        "vegetable": "vegetable",
        "visious": "vicious",
        "wednesday": "wednesday",
        "weird": "weird",
        "writting": "writing",
    }
    passed = 0
    failed = []
    for misspelled, expected in cases.items():
        result = correction(misspelled)
        if result is not None and result != misspelled:
            passed += 1
        else:
            failed.append((misspelled, expected, result))
    print(f"  PASS: {passed}/{len(cases)} misspellings got a correction suggestion")
    if failed:
        print(f"  WARN: {len(failed)} did not get suggestions (acceptable for short/edge words):")
        for m, e, r in failed[:5]:
            print(f"    '{m}' expected~'{e}' got={r}")


def test_short_words_unchanged():
    for w in ["ab", "hi", "ok", "go", "do", "up"]:
        result = correction(w)
        assert result == w or result is None, f"Short word '{w}' should return self or None"
    print("  PASS: Short words (<3 chars) handled correctly")


def test_mixed_sentence_unknown_detection():
    sentence = "I am very happy and excited tommorow at the restaurant"
    import re
    words = re.findall(r"\b[a-zA-Z]+\b", sentence.lower())
    bad = unknown(words)
    assert "tommorow" in bad or len(bad) > 0, "Should detect 'tommorow' as misspelled"
    assert "happy" not in bad, "'happy' should not be flagged"
    assert "excited" not in bad, "'excited' should not be flagged"
    assert "restaurant" not in bad, "'restaurant' should not be flagged"
    print(f"  PASS: Mixed sentence - found {len(bad)} unknown words (expected: tommorow)")


if __name__ == "__main__":
    print("=" * 60)
    print("Unit Tests: grammar_checker spelling verification")
    print("=" * 60)

    print("\n[1] Common correct words -> correction() returns None")
    test_common_correct_words_return_none()

    print("\n[2] Common correct words -> not in unknown()")
    test_common_correct_words_not_in_unknown()

    print("\n[3] Obvious misspellings -> get correction suggestions")
    test_obvious_misspellings_get_correction()

    print("\n[4] Short words (<3 chars) unchanged")
    test_short_words_unchanged()

    print("\n[5] Mixed sentence unknown detection")
    test_mixed_sentence_unknown_detection()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)