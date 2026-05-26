# -*- coding: utf-8 -*-
"""
post_reels.py
USJ815 Instagram Reels 全自動投稿スクリプト
仕組み: 動画 → Supabase Storage（公開URL）→ Instagram Graph API（Reels投稿）
"""

import os, sys, time, requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ===== 認証情報（ここに入れる） =====
INSTAGRAM_ACCESS_TOKEN = "IGAAixjYBdY8lBZAGJQeWZA4RUdFcWxXWFIwWU10T2s1eWE2SHV3UDc5ZAmwtb1BDSThiczFXUnR2RXpJSjlvOWdUY0lLV3RaelE2VkRwZAk0takNHYUlwLU9Ha19BUE5qOVJFcWxzcWYtWkFGRURPLVpPcTNJMmNUYWFiLUZApTWkxUQZDZD"
INSTAGRAM_ACCOUNT_ID   = "26734946246124933"

# BearGoと同じSupabase（動画の公開URL発行用）
SUPABASE_URL         = "https://uhmautrjkdcyubafwvib.supabase.co"
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
BUCKET               = "instagram-posts"

REELS_DIR = Path(r"C:\Users\lsbre\Desktop\Antigravity\USJACLEAN HP\reels")

# ===== 9本の投稿定義（ファイル名 + キャプション） =====
POSTS = [
    {
        "file": "reel_01_parent.mp4",
        "caption": """実家の親に使ってほしくて調べたら、これだった。

足を乗せるだけ。
寝たまま使える。
15分でタイマーOFF。

理学療法士監修。高齢者にも安心設計。

▶ プロフィールリンクから

#親へのプレゼント #腰痛ケア #金魚運動 #バイタリティスイング #理学療法士監修""",
    },
    {
        "file": "reel_02_secret.mp4",
        "caption": """全米でNo.1を獲った健康器具、
日本ではまだほとんど知られていない。

★4.4 / 2,600件のレビュー
ウォルマート採用
理学療法士監修

腰・むくみ・疲労を、
寝ながら15分でリセットする器具。

知ってる人だけが使っている段階。

▶ プロフィールリンクから

#全米NO1 #金魚運動機 #バイタリティスイング #腰痛 #むくみ解消""",
    },
    {
        "file": "reel_03_solution.mp4",
        "caption": """腰が重くて眠れない夜、これだけやってみて。

STEP 1：横になる
STEP 2：足首を乗せる
STEP 3：スイッチを入れる

あとの15分は器具がやってくれます。
自動タイマーOFF。静音設計。

全米20万台が証明した金魚運動。

▶ プロフィールリンクから

#腰痛 #眠れない #金魚運動 #バイタリティスイング #寝ながら運動 #ズボラ健康""",
    },
    {
        "file": "reel_04_education.mp4",
        "caption": """腰が痛い本当の原因、知ってますか？

「筋肉が弱い」ではなく「足首が固まって血流が止まっている」ことが多いです。

足首を動かすと、全身の血流が変わります。
金魚運動はこの原理を使った器具。

理学療法士が整形外科10年以上の経験からこれを選んだ理由が、ここにあります。

▶ プロフィールリンクから

#腰痛の原因 #金魚運動 #血流改善 #理学療法士監修 #バイタリティスイング""",
    },
    {
        "file": "reel_05_empathy.mp4",
        "caption": """座り仕事のあと、腰がズーンと重くなる。

それ、放置してませんか？

帰宅後すぐ横になって、足首を乗せるだけ。
動かなくていい。器具が動いてくれます。

自動タイマーOFF。静音設計。
気づいたら眠ってた、が正解。

▶ プロフィールリンクから

#デスクワーク #腰痛持ち #帰宅後 #金魚運動 #バイタリティスイング #ズボラ健康""",
    },
    {
        "file": "reel_06_steps.mp4",
        "caption": """腰ケア、難しいと思ってませんか？

STEP 1：横になる
STEP 2：足首を乗せる
STEP 3：スイッチを押す

以上です。

あとの15分は器具がやってくれます。
自動タイマーOFF。寝落ちしてもOK。

全米20万台が選ばれた理由は「続けられる簡単さ」にあります。

▶ プロフィールリンクから

#腰痛ケア #ズボラ健康 #寝ながら運動 #金魚運動 #バイタリティスイング #3ステップ""",
    },
    {
        "file": "reel_07_gift.mp4",
        "caption": """実家の親へのプレゼント、何にするか迷っていませんか？

立てなくても大丈夫。
運動経験がゼロでも大丈夫。
足首を乗せるだけ。

理学療法士が「高齢者にも安心」と推薦した根拠がある器具です。

渡した後に「毎日使ってる」と言われる、そういうプレゼントです。

▶ プロフィールリンクから

#親へのプレゼント #高齢者 #金魚運動 #バイタリティスイング #理学療法士監修 #腰痛ケア""",
    },
    {
        "file": "reel_08_authority.mp4",
        "caption": """整形外科10年以上の理学療法士が、自宅で使う器具として選んだのがこれです。

金魚運動は足首の自然な揺れを再現した動き。
関節・筋肉への余計な負荷がゼロ。
だから高齢者にも、術後の方にも安心して使えます。

「腰・むくみ・疲労」に安全にアプローチできる、根拠のある器具です。

▶ プロフィールリンクから

#理学療法士 #整形外科 #金魚運動 #バイタリティスイング #腰痛 #むくみ解消""",
    },
    {
        "file": "reel_09_reviews.mp4",
        "caption": """★4.4 / 2,600件のレビュー。

「腰が軽くなった」
「むくみがとれた」
「毎晩使っています」

使い方はシンプルです。
足首を乗せて、スイッチを入れるだけ。
15分後に自動タイマーOFF。

2,600人が選んだ理由を、一度体験してみてください。

▶ プロフィールリンクから

#レビュー #口コミ #金魚運動 #バイタリティスイング #腰痛 #むくみ #全米NO1""",
    },
]


# ===== Supabaseに動画をアップロード =====
def upload_video_to_supabase(video_path: Path) -> str:
    filename = f"usj815_reels/{video_path.name}"
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{filename}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "video/mp4",
        "x-upsert": "true",
    }
    print(f"  [1/3] Supabase アップロード中: {video_path.name} ...")
    with open(video_path, "rb") as f:
        res = requests.put(url, headers=headers, data=f)
    if res.status_code not in (200, 201):
        raise Exception(f"Supabase upload failed: {res.status_code} {res.text}")
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{filename}"
    print(f"  [OK] 公開URL: {public_url}")
    return public_url


# ===== Reelsコンテナ作成 =====
def create_reels_container(video_url: str, caption: str) -> str:
    print(f"  [2/3] Reelsコンテナ作成中...")
    url = f"https://graph.instagram.com/v21.0/{INSTAGRAM_ACCOUNT_ID}/media"
    res = requests.post(url, data={
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    })
    res.raise_for_status()
    container_id = res.json().get("id")
    print(f"  [OK] Container ID: {container_id}")
    return container_id


# ===== 動画処理待ち（最大10分） =====
def wait_for_processing(container_id: str, timeout=600):
    print(f"  [処理待ち] 動画エンコード中（最大{timeout//60}分）...")
    url = f"https://graph.instagram.com/v21.0/{container_id}"
    for i in range(timeout // 10):
        res = requests.get(url, params={
            "fields": "status_code,status",
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        })
        data = res.json()
        status = data.get("status_code", "")
        print(f"    {i*10}s: {status}")
        if status == "FINISHED":
            print(f"  [OK] エンコード完了")
            return True
        if status == "ERROR":
            raise Exception(f"動画処理エラー: {data}")
        time.sleep(10)
    raise Exception("タイムアウト: 動画処理が完了しませんでした")


# ===== Reels公開 =====
def publish_reel(container_id: str) -> str:
    print(f"  [3/3] 投稿公開中...")
    url = f"https://graph.instagram.com/v21.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    res = requests.post(url, data={
        "creation_id": container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    })
    res.raise_for_status()
    post_id = res.json().get("id")
    print(f"  [完了] Post ID: {post_id}")
    return post_id


# ===== 1本投稿 =====
def post_one(post: dict):
    video_path = REELS_DIR / post["file"]
    if not video_path.exists():
        raise FileNotFoundError(f"動画が見つかりません: {video_path}")

    video_url    = upload_video_to_supabase(video_path)
    container_id = create_reels_container(video_url, post["caption"])
    wait_for_processing(container_id)
    post_id      = publish_reel(container_id)
    return post_id


# ===== メイン =====
def main():
    if "ここに" in INSTAGRAM_ACCESS_TOKEN:
        print("[ERROR] INSTAGRAM_ACCESS_TOKEN を設定してください")
        sys.exit(1)
    if "ここに" in INSTAGRAM_ACCOUNT_ID:
        print("[ERROR] INSTAGRAM_ACCOUNT_ID を設定してください")
        sys.exit(1)

    # コマンドライン引数で投稿番号を指定（0-8）。なければ0番目を投稿
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if not (0 <= idx < len(POSTS)):
        print(f"[ERROR] 番号は0〜{len(POSTS)-1}で指定してください")
        sys.exit(1)

    post = POSTS[idx]
    print(f"\n{'='*50}")
    print(f"投稿 Day {idx+1}: {post['file']}")
    print(f"{'='*50}")

    post_id = post_one(post)
    print(f"\n✅ 投稿完了！ Post ID: {post_id}")


if __name__ == "__main__":
    main()
