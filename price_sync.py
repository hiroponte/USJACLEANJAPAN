"""
USJ815 価格自動同期スクリプト
毎日1回実行: Amazon価格取得 → Shopify価格更新 → HTML更新 → Git push → LINE通知
"""

import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import requests
from bs4 import BeautifulSoup
import re
import subprocess
from pathlib import Path

# GitHub Actions上で動いているかどうか
IS_GH_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

# ========== 設定 ==========
ASIN = "B000PEAL8C"
COUPON_DISCOUNT = 1500

SHOPIFY_STORE = "daiwa-felicity-3.myshopify.com"
SHOPIFY_TOKEN = os.getenv("SHOPIFY_TOKEN", "ここにShopifyAdminAPIトークンを貼る")
VARIANT_ID = "49066637230303"

LINE_TOKEN = "EFSlMC/VWVj/vtDTwRQmAPevi5qBhCZkxskAAi+XvZ+scWTfDTuFZEdja8olHmDmLUIeWGHgH7n5d03EkNT1wOBVpr2H4+oBfYOf16j0vltNZ3vxfHClLhzzgiKC12YHag6p77NV4KbfkWx3yhz6YAdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "C94a431821472322cc481e3b44a3033c6"

HTML_PATH = Path(__file__).parent / "index.html"
REPO_DIR  = str(Path(__file__).parent)


# ========== Amazon価格取得 ==========
def get_amazon_price():
    url = f"https://www.amazon.co.jp/dp/{ASIN}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja-JP,ja;q=0.9",
    }
    res = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")
    price_el = soup.select_one(".a-price .a-offscreen, #price_inside_buybox, #priceblock_ourprice")
    if price_el:
        raw = price_el.get_text(strip=True)
        # ¥（半角）と￥（全角）両方除去
        raw = raw.replace("¥", "").replace("￥", "").replace(",", "").strip()
        digits = re.sub(r"[^\d]", "", raw)
        if digits:
            return int(digits)
    return None


# ========== Shopify価格更新 ==========
def update_shopify_price(new_price):
    if "ここに" in SHOPIFY_TOKEN:
        print("[Shopify] トークン未設定のためスキップ")
        return False
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/variants/{VARIANT_ID}.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json",
    }
    data = {"variant": {"id": int(VARIANT_ID), "price": str(new_price)}}
    res = requests.put(url, headers=headers, json=data, timeout=15)
    return res.status_code == 200


# ========== HTML価格表示を更新 ==========
def update_html(amazon_price, our_price):
    content = HTML_PATH.read_text(encoding="utf-8")

    amazon_fmt = f"¥{amazon_price:,}"
    our_fmt    = f"¥{our_price:,}"

    replacements = [
        # 上段の価格比較ブロック
        (r'(<span class="lp-price-amazon-num">)¥[\d,]+(</span>)',  f'\\g<1>{amazon_fmt}\\g<2>'),
        (r'(<span class="lp-price-shopify-num">)¥[\d,]+(</span>)', f'\\g<1>{our_fmt}\\g<2>'),
        # 下段の限定価格ブロック
        (r'(<span class="lp-excl-price lp-excl-price-cross">)¥[\d,]+(</span>)',  f'\\g<1>{amazon_fmt}\\g<2>'),
        (r'(<span class="lp-excl-price lp-excl-price-main">)¥[\d,]+(</span>)',   f'\\g<1>{our_fmt}\\g<2>'),
        # フッターのノート
        (r'通常価格（¥[\d,]+）', f'通常価格（{amazon_fmt}）'),
    ]
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    HTML_PATH.write_text(content, encoding="utf-8")
    print(f"[HTML] 更新完了: Amazon {amazon_fmt} / 公式 {our_fmt}")


# ========== Git push（ローカル実行時のみ。GitHub Actionsではワークフロー側でやる）==========
def git_push(amazon_price, our_price):
    if IS_GH_ACTIONS:
        print("[Git] GitHub Actions環境 → git操作はワークフロー側に委譲")
        return True
    msg = f"価格自動更新: Amazon¥{amazon_price:,} → 公式¥{our_price:,}"
    subprocess.run(["git", "add", "index.html"], cwd=REPO_DIR, check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO_DIR)
    if result.returncode == 0:
        print("[Git] 変更なし（価格が前回と同じ）")
        return False
    subprocess.run(["git", "commit", "-m", msg], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "push"], cwd=REPO_DIR, check=True)
    print(f"[Git] push完了: {msg}")
    return True


# ========== LINE通知 ==========
def send_line(message):
    try:
        requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers={"Authorization": f"Bearer {LINE_TOKEN}", "Content-Type": "application/json"},
            json={"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]},
            timeout=10,
        )
    except Exception as e:
        print(f"[LINE] 送信エラー: {e}")


# ========== メイン ==========
if __name__ == "__main__":
    print("=== USJ815 価格同期 開始 ===")

    amazon_price = get_amazon_price()
    if not amazon_price:
        send_line("[USJ815 価格同期] ⚠️ Amazon価格の取得に失敗しました。手動確認してください。")
        print("[エラー] Amazon価格取得失敗")
        exit(1)

    our_price = amazon_price - COUPON_DISCOUNT
    print(f"[Amazon] 現在価格: ¥{amazon_price:,}")
    print(f"[公式]   設定価格: ¥{our_price:,} (クーポン¥{COUPON_DISCOUNT:,}引き後)")

    # Shopify価格更新
    shopify_ok = update_shopify_price(amazon_price)

    # HTML更新 + Git push
    update_html(amazon_price, our_price)
    pushed = git_push(amazon_price, our_price)

    # LINE通知
    shopify_status = "✅ Shopify更新済" if shopify_ok else "⚠️ Shopify要手動更新"
    html_status    = "✅ サイト反映済" if pushed else "変更なし（前回と同額）"
    msg = (
        f"[USJ815 価格自動同期]\n"
        f"Amazon:  ¥{amazon_price:,}\n"
        f"公式(クーポン後): ¥{our_price:,}\n"
        f"Amazonより¥{COUPON_DISCOUNT:,}安い\n"
        f"{shopify_status}\n"
        f"{html_status}"
    )
    send_line(msg)
    print("=== 完了 ===")
    print(msg)
