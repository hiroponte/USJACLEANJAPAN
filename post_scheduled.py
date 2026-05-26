# -*- coding: utf-8 -*-
"""
post_scheduled.py
Windows タスクスケジューラーから呼び出される自動投稿スクリプト。
月・水・金に1本ずつ順番に投稿し、9本でループする。
"""
import json, sys, datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "post_state.json"
LOG_FILE   = SCRIPT_DIR / "post_log.txt"

sys.path.insert(0, str(SCRIPT_DIR))
from post_reels import POSTS, post_one, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    # reel_01 は 5/13 に手動投稿済みなので次は index=1 から
    return {"next_index": 1}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    log("===== 自動投稿 START =====")

    if "ここに" in INSTAGRAM_ACCESS_TOKEN or "ここに" in INSTAGRAM_ACCOUNT_ID:
        log("[ERROR] 認証情報が未設定です")
        sys.exit(1)

    state = load_state()
    idx   = state["next_index"]
    post  = POSTS[idx]

    log(f"投稿対象: {post['file']} (index={idx})")

    try:
        post_id = post_one(post)
        log(f"✅ 投稿完了: Post ID={post_id}")
        state["next_index"]  = (idx + 1) % len(POSTS)
        state["last_posted"] = {
            "date":    datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "index":   idx,
            "file":    post["file"],
            "post_id": post_id,
        }
        save_state(state)
    except Exception as e:
        log(f"[ERROR] 投稿失敗: {e}")
        sys.exit(1)

    log("===== 自動投稿 END =====")


if __name__ == "__main__":
    main()
