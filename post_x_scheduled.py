# -*- coding: utf-8 -*-
"""
post_x_scheduled.py
GitHub Actions / Windows タスクスケジューラーから呼び出される自動投稿スクリプト。
毎日1本ずつ順番に投稿し、15本でループする。
"""
import json, sys, datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "x_post_state.json"
LOG_FILE   = SCRIPT_DIR / "x_post_log.txt"

sys.path.insert(0, str(SCRIPT_DIR))
from post_x import TWEETS, post_tweet


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
    return {"next_index": 0}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    log("===== X自動投稿 START =====")

    state = load_state()
    idx   = state["next_index"]
    tweet = TWEETS[idx]

    tweet_text  = tweet["text"] if isinstance(tweet, dict) else tweet
    tweet_image = tweet.get("image") if isinstance(tweet, dict) else None
    log(f"投稿対象: No.{idx+1} (index={idx}) | 画像: {tweet_image or 'なし'}")
    log(f"本文（先頭50文字）: {tweet_text[:50].replace(chr(10), ' ')}")

    try:
        tweet_id = post_tweet(tweet)
        log(f"✅ 投稿完了: Tweet ID={tweet_id}")
        state["next_index"]  = (idx + 1) % len(TWEETS)
        state["last_posted"] = {
            "date":     datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "index":    idx,
            "tweet_id": tweet_id,
        }
        save_state(state)
    except Exception as e:
        log(f"[ERROR] 投稿失敗: {e}")
        sys.exit(1)

    log("===== X自動投稿 END =====")


if __name__ == "__main__":
    main()
