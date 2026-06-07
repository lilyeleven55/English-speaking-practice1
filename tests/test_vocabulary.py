import os
import sys
import json
import tempfile
import csv
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

TEST_DB = os.path.join(tempfile.gettempdir(), "test_vocab_api.db")
SAMPLE_WORDS = [
    {"word": "beautiful", "definition": "美丽的", "example": "A beautiful day.", "source": "练习"},
    {"word": "excited", "definition": "兴奋的", "example": "I'm so excited!", "source": "手动添加"},
    {"word": "schedule", "definition": "日程表", "example": "Check your schedule.", "source": "练习"},
    {"word": "restaurant", "definition": "餐厅", "example": "Let's go to a restaurant.", "source": "餐厅点餐"},
    {"word": "yesterday", "definition": "昨天", "example": "I went there yesterday.", "source": "日常购物"},
]

passed = 0
failed = 0
errors = []


def assert_eq(actual, expected, msg=""):
    global passed, failed, errors
    if actual == expected:
        passed += 1
    else:
        failed += 1
        detail = f"  FAIL: {msg}\n    expected: {expected!r}\n    actual:   {actual!r}"
        errors.append(detail)
        print(detail)


def assert_true(condition, msg=""):
    global passed, failed, errors
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(f"  FAIL: {msg}")
        print(f"  FAIL: {msg}")


def setup_test_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    import app as app_module
    app_module.DB_PATH = TEST_DB
    app_module.init_db()


print("=" * 60)
print("Vocabulary API Integration Tests")
print("=" * 60)

from app import app

app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
app.secret_key = "test-secret-key"

setup_test_db()

client = app.test_client()


def with_session(user_id="test_user_001"):
    def decorator(func):
        def wrapper(*args, **kw):
            with client.session_transaction() as sess:
                sess["user_id"] = user_id
                sess["sid"] = f"test-session-{user_id}"
            return func(*args, **kw)
        return wrapper
    return decorator


@with_session()
def test_add_single():
    global resp
    resp = client.post("/api/vocabulary",
                       json=SAMPLE_WORDS[0],
                       content_type="application/json")
    assert_eq(resp.status_code, 200, "POST add single word status")
    result = resp.get_json()
    assert_eq(result["word"], "beautiful", "returned word matches")
    assert_true("id" in result and isinstance(result["id"], int), "has integer id")


@with_session()
def test_add_multiple():
    for w in SAMPLE_WORDS[1:]:
        r = client.post("/api/vocabulary", json=w, content_type="application/json")
        assert_eq(r.status_code, 200, f"POST add {w['word']}")
    
    resp = client.get("/api/vocabulary")
    items = resp.get_json()
    assert_eq(len(items), len(SAMPLE_WORDS), f"GET returns {len(SAMPLE_WORDS)} items")
    words_set = {i["word"] for i in items}
    assert_eq(words_set, {w["word"] for w in SAMPLE_WORDS}, "all sample words present")


@with_session()
def test_duplicate_detection():
    dup_resp = client.post("/api/vocabulary",
                            json={"word": "beautiful", "definition": "dup"},
                            content_type="application/json")
    assert_eq(dup_resp.status_code, 409, "duplicate returns 409")
    dup_result = dup_resp.get_json()
    assert_true("already exists" in dup_result["error"].lower(), "error mentions duplicate")
    
    case_dup = client.post("/api/vocabulary",
                             json={"word": "BEAUTIFUL"},
                             content_type="application/json")
    assert_eq(case_dup.status_code, 409, "case-insensitive duplicate returns 409")


@with_session()
def test_validation():
    empty = client.post("/api/vocabulary", json={"word": ""}, content_type="application/json")
    assert_eq(empty.status_code, 400, "empty word -> 400")
    
    missing = client.post("/api/vocabulary", json={"definition": "x"}, content_type="application/json")
    assert_eq(missing.status_code, 400, "missing word -> 400")
    
    long_word = client.post("/api/vocabulary", json={"word": "a" * 101}, content_type="application/json")
    assert_eq(long_word.status_code, 400, "word >100 chars -> 400")
    
    optional_ok = client.post("/api/vocabulary", json={"word": "simple"}, content_type="application/json")
    assert_eq(optional_ok.status_code, 200, "optional fields can be empty")


@with_session()
def test_get_and_search():
    get_all = client.get("/api/vocabulary")
    all_items = get_all.get_json()
    assert_eq(get_all.status_code, 200, "GET all status 200")
    assert_true(len(all_items) >= 6, f"has >=6 items (got {len(all_items)})")
    for item in all_items[:3]:
        for field in ["id", "word", "definition", "example", "source", "created_at"]:
            assert_true(field in item, f"item has '{field}' field")
    
    search_resp = client.get("/api/vocabulary?search=beau")
    search_items = search_resp.get_json()
    assert_true(len(search_items) >= 1, f"search 'beau' finds results ({len(search_items)})")
    for item in search_items:
        assert_true("beau" in item["word"].lower(), f"search result contains 'beau'")
    
    no_match = client.get("/api/vocabulary?search=zzznotexist")
    assert_eq(no_match.get_json(), [], "search no match returns empty list")


@with_session()
def test_delete():
    get_resp = client.get("/api/vocabulary")
    target_id = get_resp.get_json()[0]["id"]
    
    del_resp = client.delete(f"/api/vocabulary/{target_id}")
    assert_eq(del_resp.status_code, 200, "DELETE existing -> 200")
    del_result = del_resp.get_json()
    assert_true(del_result.get("ok") is True, "delete response has ok=true")
    
    after_del = client.get("/api/vocabulary")
    remaining = after_del.get_json()
    assert_true(not any(i["id"] == target_id for i in remaining), "deleted item gone from list")
    
    not_found_del = client.delete("/api/vocabulary/99999")
    assert_eq(not_found_del.status_code, 404, "DELETE nonexistent -> 404")


@with_session()
def test_edit():
    edit_target = client.get("/api/vocabulary").get_json()[0]
    edit_id = edit_target["id"]
    
    put_resp = client.put(f"/api/vocabulary/{edit_id}",
                          json={
                              "word": edit_target["word"],
                              "definition": "修改后的释义",
                              "example": "New example sentence.",
                              "source": "edited"
                          },
                          content_type="application/json")
    assert_eq(put_resp.status_code, 200, "PUT edit -> 200")
    put_result = put_resp.get_json()
    assert_eq(put_result["definition"], "修改后的释义", "definition updated in response")
    
    verify = client.get("/api/vocabulary").get_json()
    verified = [i for i in verify if i["id"] == edit_id][0]
    assert_eq(verified["definition"], "修改后的释义", "definition persisted in DB")
    assert_eq(verified["example"], "New example sentence.", "example persisted in DB")
    
    other_word = client.get("/api/vocabulary").get_json()[1]["word"]
    dup_edit = client.put(f"/api/vocabulary/{edit_id}",
                          json={"word": other_word},
                          content_type="application/json")
    assert_eq(dup_edit.status_code, 409, "PUT to duplicate word -> 409")
    
    bad_edit = client.put(f"/api/vocabulary/{edit_id}", json={"word": ""}, content_type="application/json")
    assert_eq(bad_edit.status_code, 400, "PUT empty word -> 400")
    
    not_found_put = client.put("/api/vocabulary/99999", json={"word": "ghost"}, content_type="application/json")
    assert_eq(not_found_put.status_code, 404, "PUT nonexistent -> 404")


@with_session()
def test_export():
    csv_resp = client.get("/api/vocabulary/export?format=csv")
    assert_eq(csv_resp.status_code, 200, "CSV export status 200")
    csv_content = csv_resp.data.decode("utf-8")
    reader = csv.reader(io.StringIO(csv_content))
    csv_rows = list(reader)
    assert_eq(csv_rows[0], ["单词", "释义", "例句", "来源"], "CSV header correct")
    assert_true(len(csv_rows) >= 5, f"CSV has data rows ({len(csv_rows)-1} rows)")
    
    txt_resp = client.get("/api/vocabulary/export?format=txt")
    assert_eq(txt_resp.status_code, 200, "TXT export status 200")
    txt_content = txt_resp.data.decode("utf-8")
    assert_true("修改后的释义" in txt_content, "TXT includes edited definition (or data)")
    
    bad_fmt = client.get("/api/vocabulary/export?format=pdf")
    assert_eq(bad_fmt.status_code, 400, "invalid format -> 400")
    
    cd_csv = csv_resp.headers.get("Content-Disposition", "")
    assert_true("vocabulary.csv" in cd_csv, "CSV Content-Disposition header")
    cd_txt = txt_resp.headers.get("Content-Disposition", "")
    assert_true("vocabulary.txt" in cd_txt, "TXT Content-Disposition header")


@with_session()
def test_data_integrity():
    long_data = {
        "word": "limitest",
        "definition": "d" * 600,
        "example": "e" * 1100,
        "source": "s" * 150,
    }
    lim_resp = client.post("/api/vocabulary", json=long_data, content_type="application/json")
    lim_result = lim_resp.get_json()
    assert_true(len(lim_result["definition"]) <= 500, f"definition truncated to <=500 (got {len(lim_result['definition'])})")
    assert_true(len(lim_result["example"]) <= 1000, f"example truncated to <=1000 (got {len(lim_result['example'])})")
    assert_true(len(lim_result["source"]) <= 100, f"source truncated to <=100 (got {len(lim_result['source'])})")
    
    special = {
        "word": "café",
        'definition': '咖啡店 (quotes " and \')',
        "example": "Let's go — it's <great> & awesome!",
        "source": "test & review"
    }
    spec_resp = client.post("/api/vocabulary", json=special, content_type="application/json")
    assert_eq(spec_resp.status_code, 200, "special chars accepted")

    conn = sqlite3.connect(TEST_DB)
    conn.execute("DELETE FROM vocabulary")
    conn.commit()
    conn.close()
    empty_export = client.get("/api/vocabulary/export?format=csv")
    assert_eq(empty_export.status_code, 200, "empty export still 200")
    assert_true(b"No vocabulary data" in empty_export.data, "empty export has message")


print("\n[1] Add Vocabulary - Basic")
test_add_single()

print("\n[2] Add Vocabulary - Multiple words")
test_add_multiple()

print("\n[3] Add Vocabulary - Duplicate detection")
test_duplicate_detection()

print("\n[4] Add Vocabulary - Validation")
test_validation()

print("\n[5] Get Vocabulary - List & Search")
test_get_and_search()

print("\n[6] Delete Vocabulary")
test_delete()

print("\n[7] Edit Vocabulary")
test_edit()

print("\n[8] Export Vocabulary")
test_export()

print("\n[9] Data Integrity & Edge Cases")
test_data_integrity()


print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed")
if errors:
    print("\nFailed tests:")
    for e in errors:
        print(e)
else:
    print("ALL TESTS PASSED")
print("=" * 60)

if failed > 0:
    sys.exit(1)
