# -*- coding: utf-8 -*-
"""
post_x.py
USJ-815 バイタリティスイング X (Twitter) 自動投稿スクリプト
- テキストのみ投稿 + 画像付き投稿の両対応
- TWEETS は {"text": str, "image": str | None} の辞書リスト
"""

import os, sys, tweepy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ===== 認証情報（環境変数から取得） =====
X_API_KEY       = os.getenv("X_API_KEY", "")
X_API_SECRET    = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN  = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET", "")

PRODUCT_URL = "https://daiwafelicity.jp/"
IMAGES_DIR  = Path(__file__).parent / "assets"


def _v2_client():
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
        raise Exception(
            "X APIの認証情報が未設定です。\n"
            "環境変数 X_API_KEY / X_API_SECRET / X_ACCESS_TOKEN / X_ACCESS_SECRET を設定してください"
        )
    return tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_SECRET,
    )


def _upload_media(filename: str) -> str | None:
    """画像または動画をアップロードしてmedia_idを返す。失敗時はNone。"""
    path = IMAGES_DIR / filename
    if not path.exists():
        print(f"[WARN] ファイルが見つかりません: {path} → テキストのみで投稿")
        return None
    try:
        auth = tweepy.OAuth1UserHandler(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET)
        api  = tweepy.API(auth)
        ext  = path.suffix.lower()
        if ext in (".mp4", ".mov", ".avi"):
            media = api.media_upload(
                str(path),
                media_type="video/mp4",
                media_category="tweet_video",
                chunked=True,
                wait_for_async_finalize=True,
            )
        else:
            media = api.media_upload(str(path))
        return str(media.media_id)
    except Exception as e:
        print(f"[WARN] メディアアップロード失敗: {e} → テキストのみで投稿")
        return None


def post_tweet(tweet: dict) -> str:
    """1件ツイートして Tweet ID を返す。"""
    text  = tweet["text"]
    image = tweet.get("image")

    client   = _v2_client()
    media_id = _upload_media(image) if image else None

    if media_id:
        response = client.create_tweet(text=text, media_ids=[media_id])
    else:
        response = client.create_tweet(text=text)

    return response.data["id"]


# ===== 30本のツイート定義 =====
# image: assets/ 以下のファイル名。None はテキストのみ。
U = PRODUCT_URL

TWEETS = [
    # ── テキストのみ（アルゴリズムリーチ重視） ──────────────────

    # 1: 帰宅後の共感
    {"text": f"""帰宅後、腰がズーンと重くなる。

そのまま放置してませんか？

横になって足首を乗せるだけ。器具が動いてくれます。15分後に自動OFF。

#デスクワーク #腰痛持ち #金魚運動
👆 プロフィールリンクから""", "image": None},

    # 2: 全米実績
    {"text": f"""全米20万台が選ばれた健康器具、日本ではまだほぼ知られていない。

★4.4 / 2,600件のレビュー
ウォルマート採用
理学療法士監修

知っている人だけが使っている段階。

#腰痛 #全米NO1 #金魚運動
👆 プロフィールリンクから""", "image": None},

    # 3: 使い方3ステップ（シンプル）
    {"text": f"""腰ケアのやり方

1. 横になる
2. 足首を乗せる
3. スイッチを入れる

以上です。あとの15分は器具がやってくれます。

#ズボラ健康 #寝ながら運動 #腰痛ケア
👆 プロフィールリンクから""", "image": None},

    # 4: 口コミ引用
    {"text": f"""「腰の重さが気づいたら消えていた」

2,600人が言ってることの意味が、使い始めてやっとわかった。

足首を乗せるだけで、ここまで変わる。

#口コミ #腰痛持ちと繋がりたい #金魚運動
👆 プロフィールリンクから""", "image": None},

    # 5: 腰痛の原因解説（教育系）
    {"text": f"""腰痛の本当の原因、知ってますか？

「足首が固まって血流が止まっている」ことが多い。

足首を動かすと全身の血流が変わる。金魚運動はこの原理を使った器具。

#腰痛の原因 #血流改善 #バイタリティスイング
👆 プロフィールリンクから""", "image": None},

    # 6: Before/After
    {"text": f"""使う前：帰宅後は腰が重くてソファから動けない
使った後：15分後にスッキリして眠れる

変えたのは1つだけ。足首を乗せるだけ。

#腰痛改善 #寝ながら運動 #むくみ解消
👆 プロフィールリンクから""", "image": None},

    # 7: 50代・60代向け
    {"text": f"""50代・60代の腰痛に。

激しい運動は必要ない。
立てなくても大丈夫。
足を乗せるだけでいい。

理学療法士監修の金魚運動機。

#50代健康 #シニア健康 #腰痛ケア
👆 プロフィールリンクから""", "image": None},

    # 8: 寝落ちOK
    {"text": f"""寝落ちしてもOKな器具がある。

横になって足首を乗せてスイッチON。
15分後に自動でOFF。

起きたら腰が軽くなってる、が理想。

#寝落ち #腰痛 #金魚運動
👆 プロフィールリンクから""", "image": None},

    # 9: 静音設計
    {"text": f"""寝室で使える健康器具の条件。

・静かなこと
・寝たまま使えること
・タイマーで自動OFFになること

全部クリアしてる器具、見つけました。

#静音設計 #腰痛 #寝ながら運動
👆 プロフィールリンクから""", "image": None},

    # 10: 在宅ワーカー向け
    {"text": f"""在宅ワーカーの腰痛対策、これが一番続いてる。

運動しなくていい。
ストレッチしなくていい。
横になって足首を乗せるだけ。

#在宅ワーク #デスクワーク腰痛 #腰痛対策
👆 プロフィールリンクから""", "image": None},

    # 11: 親へのプレゼント
    {"text": f"""腰が痛い親に、何もしなくていい器具を送りました。

足を乗せるだけ。15分で自動OFF。
「毎日使ってる」って言ってくれました。

#親へのプレゼント #腰痛ケア #バイタリティスイング
👆 プロフィールリンクから""", "image": None},

    # 12: 金魚運動の仕組み解説
    {"text": f"""「金魚運動」を知ってますか？

魚が泳ぐように背骨をS字に揺らす運動。
足首から始まる振動が全身に伝わる。

これを自動でやってくれる器具がバイタリティスイング。

#金魚運動 #バイタリティスイング #健康器具
👆 プロフィールリンクから""", "image": None},

    # 13: 権威性まとめ
    {"text": f"""全米ウォルマートが採用。
理学療法士が監修。
2,600件のレビュー★4.4。

この数字の重さ、日本で理解されるまでに時間がかかると思う。

先に知ってほしい。

#全米NO1 #腰痛 #バイタリティスイング
👆 プロフィールリンクから""", "image": None},

    # 14: 「運動できない人」向け
    {"text": f"""15分のウォーキングが難しい方へ。

横になったまま同等の血流効果がある器具があります。

足首を揺らすだけ。関節への負荷ゼロ。

#運動不足 #腰痛 #金魚運動
👆 プロフィールリンクから""", "image": None},

    # 15: 夜のルーティン
    {"text": f"""夜寝る前の15分ルーティンに入れてから、
朝の体の軽さが全然違う。

横になって足首を乗せてスイッチを入れるだけ。
あとは勝手に終わる。

#夜のルーティン #腰痛改善 #バイタリティスイング
👆 プロフィールリンクから""", "image": None},

    # 16: 「試してみてほしい」系
    {"text": f"""腰痛持ちの方、これ一度試してみてください。

寝ながら5分。本当に変わります。

Amazon 2,600件のレビューが証明してます。

#腰痛持ちと繋がりたい #健康器具 #金魚運動
👆 プロフィールリンクから""", "image": None},

    # 17: 高齢者の親向け
    {"text": f"""80代でも使えます。

激しくない。立てなくても使える。
タイマーで15分後に自動OFF。

高齢の親へのプレゼントに選ばれている理由がわかる。

#敬老の日 #親へのプレゼント #シニア健康
👆 プロフィールリンクから""", "image": None},

    # 18: 価格訴求
    {"text": f"""Amazon ¥32,800 → 公式サイトなら ¥31,300

同じ商品が¥1,500安く買えます。

クーポンコード：WELCOME1500

#腰痛 #バイタリティスイング #公式限定
👆 プロフィールリンクから""", "image": None},

    # 19: むくみ訴求
    {"text": f"""足のむくみ、夜に爆発してませんか？

足首を動かすだけでふくらはぎのポンプが動き出す。

横になって15分。金魚運動機がやってくれます。

#むくみ解消 #足のむくみ #バイタリティスイング
👆 プロフィールリンクから""", "image": None},

    # 20: 「知ってる人だけ使ってる」希少感
    {"text": f"""日本でまだほぼ広まっていない健康器具がある。

アメリカでは20万台売れてる。
理学療法士が推薦してる。
Amazonで2,600人がレビューしてる。

なのになぜ日本で知られてないのか、謎。

#健康器具 #腰痛 #金魚運動
👆 プロフィールリンクから""", "image": None},

    # ── 画像付き投稿 ──────────────────────────────────────

    # 21: メインビジュアル
    {"text": f"""寝ながら15分。それだけ。

全米20万台・理学療法士監修・★4.4

バイタリティスイングが日本にあります。

👉 公式サイトから

#腰痛 #金魚運動 #バイタリティスイング
👆 プロフィールリンクから""", "image": "vs_hero.jpg"},

    # 22: 理学療法士監修
    {"text": f"""整形外科10年の理学療法士が選んだ自宅器具。

「関節への負荷ゼロ。80代でも安心して使える」

これがバイタリティスイングを信頼できる理由。

#理学療法士監修 #腰痛ケア #健康器具
👆 プロフィールリンクから""", "image": "vs_credentials.jpg"},

    # 23: 効果説明
    {"text": f"""なぜ足首を揺らすだけで腰に効くのか？

足首 → ふくらはぎ → 腰 → 背骨まで振動が届く。

全身の血流が動き出す。それが金魚運動の原理。

#金魚運動の仕組み #腰痛 #血流改善
👆 プロフィールリンクから""", "image": "vs_benefits.jpg"},

    # 24: 使い方
    {"text": f"""使い方はシンプル。

① 横になる
② 足首をのせる
③ スイッチON

15分で自動OFF。寝落ちしてもOK。

#使い方 #腰痛ケア #バイタリティスイング
👆 プロフィールリンクから""", "image": "vs_usage.jpg"},

    # 25: ライフスタイル
    {"text": f"""テレビを見ながら。
スマホを触りながら。
そのまま寝落ちしても。

日常の中に自然に入る腰ケア。

#ライフスタイル #腰痛改善 #寝ながら運動
👆 プロフィールリンクから""", "image": "vs_lifestyle.jpg"},

    # 26: 金魚運動の波動
    {"text": f"""魚が泳ぐように、背骨がS字に揺れる。

これが金魚運動。
足首から始まった波動が全身に伝わる。

横になってるだけで、体の中が動いてる。

#金魚運動 #波動 #背骨ケア
👆 プロフィールリンクから""", "image": "vs_wave.jpg"},

    # 27: スペック訴求
    {"text": f"""タイマー：自動15分
サイズ：コンパクト
音：静音設計
重さ：持ち運べる軽さ

これだけ揃って、寝ながら使える。

#バイタリティスイング #仕様 #腰痛器具
👆 プロフィールリンクから""", "image": "vs_specs.jpg"},

    # 28: 商品ビジュアル+価格
    {"text": f"""USJ-815 バイタリティスイング

■ 全米累計20万台
■ 理学療法士監修
■ Amazon ★4.4 / 2,600件

公式サイト限定価格 ¥31,300（¥1,500お得）

#バイタリティスイング #腰痛 #健康器具
👆 プロフィールリンクから""", "image": "product_vitality_swing.jpg"},

    # 29: ギフト・箱入り
    {"text": f"""誕生日・敬老の日のプレゼントに迷っている方へ。

立てなくても使える。
運動経験ゼロでも使える。
15分後に自動OFF。

「毎日使ってる」と言ってもらえる器具。

#敬老の日プレゼント #親へのプレゼント #バイタリティスイング
👆 プロフィールリンクから""", "image": "product_vitality_swing_box.jpg"},

    # 30: 基本情報まとめ
    {"text": f"""知らなかった人のために。

バイタリティスイング、3つの数字

・全米20万台
・Amazon ★4.4
・2,600件のレビュー

足首を乗せるだけの金魚運動機です。

#バイタリティスイング #腰痛 #全米NO1
👆 プロフィールリンクから""", "image": "vs_basicinfo.jpg"},

    # ── 動画投稿 ──────────────────────────────────────────────

    # 31: 動画・実演メイン
    {"text": """これが金魚運動。

足首を乗せてスイッチを入れる。
体が自然に揺れ始める。

運動不要。15分後に自動OFF。

#金魚運動 #腰痛ケア #バイタリティスイング""", "image": "vitality_swing_official.mp4"},

    # 32: 動画・使いやすさ訴求
    {"text": """寝ながら使える、が本当の意味。

テレビ見ながらでも。
本を読みながらでも。
そのまま寝落ちしても。

全米20万台が選ばれた理由、動いて分かる。

#寝ながら運動 #腰痛 #健康器具""", "image": "vitality_swing_official.mp4"},

    # 33: 動画・「足首から全身へ」解説
    {"text": """なぜ足首を動かすと腰に効くのか。

足首 → ふくらはぎ → 腰 → 背骨。
波動が下から上へ伝わっていく。

理学療法士が10年かけてたどり着いた原理。

#金魚運動の仕組み #血流改善 #腰痛""", "image": "vitality_swing_official.mp4"},
]


def main():
    import sys
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if not (0 <= idx < len(TWEETS)):
        print(f"[ERROR] 番号は0〜{len(TWEETS)-1}で指定してください")
        sys.exit(1)

    tweet = TWEETS[idx]
    print(f"\n{'='*50}")
    print(f"ツイート No.{idx+1} | 画像: {tweet.get('image') or 'なし'}")
    print(f"{'='*50}")
    print(tweet["text"])
    print(f"{'='*50}")

    tweet_id = post_tweet(tweet)
    print(f"\n✅ 投稿完了！ Tweet ID: {tweet_id}")
    print(f"URL: https://twitter.com/i/web/status/{tweet_id}")


if __name__ == "__main__":
    main()
