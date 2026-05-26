# -*- coding: utf-8 -*-
"""
post_x_scheduled.py
GitHub Actions / Windows タスクスケジューラーから呼び出される自動投稿スクリプト。
毎日1本ずつ順番に投稿し、15本でループする。
"""
import json, sys, datetime, os
import urllib.request
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


def send_line(msg: str):
    token = os.getenv("LINE_TOKEN", "")
    user_id = os.getenv("LINE_USER_ID", "")
    if not token or not user_id:
        return
    try:
        body = json.dumps({"to": user_id, "messages": [{"type": "text", "text": msg}]}).encode("utf-8")
        req = urllib.request.Request(
            "https://api.line.me/v2/bot/message/push",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log(f"[LINE] 通知失敗: {e}")


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

        media_label = f"🖼 画像あり（{tweet_image}）" if tweet_image and not tweet_image.endswith(".mp4") else \
                      "🎬 動画あり" if tweet_image else "📝 テキストのみ"
        send_line(
            f"[USJ-815 X自動投稿]\n"
            f"✅ No.{idx+1} 投稿完了\n"
            f"{media_label}\n"
            f"本文: {tweet_text[:40].replace(chr(10), ' ')}…\n"
            f"🔗 https://x.com/i/web/status/{tweet_id}"
        )
    except Exception as e:
        log(f"[ERROR] 投稿失敗: {e}")
        send_line(f"[USJ-815 X自動投稿]\n❌ No.{idx+1} 投稿失敗\n{e}")
        sys.exit(1)

    log("===== X自動投稿 END =====")


if __name__ == "__main__":
    main()
