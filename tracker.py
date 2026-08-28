import os
import requests
from datetime import datetime

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DISCOUNT_THRESHOLD = 60  # Tracks deals >= 60% off

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def check_deals():
    headers = {"User-Agent": "Mozilla/5.0"}
    page = 1
    total_products_checked = 0
    deals = []

    while True:
        url = f"https://casiostore.bhawar.com/products.json?limit=250&page={page}"
        try:
            response = requests.get(url, headers=headers, timeout=15)
            products = response.json().get("products", [])
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

        if not products:
            break

        total_products_checked += len(products)

        for product in products:
            title = product.get("title")
            handle = product.get("handle")
            for variant in product.get("variants", []):
                try:
                    price = float(variant.get("price", 0))
                    compare_at = float(variant.get("compare_at_price") or price)
                except (ValueError, TypeError):
                    continue

                if compare_at > 0 and price < compare_at:
                    discount = ((compare_at - price) / compare_at) * 100
                    if discount >= DISCOUNT_THRESHOLD and variant.get("available"):
                        deals.append((title, price, compare_at, discount, handle))
        page += 1

    # Send deal alerts if found
    if deals:
        for title, price, compare_at, discount, handle in deals:
            msg = (
                f"🚨 *Casio Deal Alert ({discount:.0f}% OFF)!*\n\n"
                f"*{title}*\n"
                f"💰 Price: ₹{price:,.0f} (MRP: ₹{compare_at:,.0f})\n"
                f"🔗 https://casiostore.bhawar.com/products/{handle}"
            )
            send_telegram(msg)
    else:
        # Heartbeat notification when no deals are found
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        msg = (
            f"✅ *Casio Monitor Check Completed*\n\n"
            f"• Checked `{total_products_checked}` products\n"
            f"• No deals $\\ge$ {DISCOUNT_THRESHOLD}% currently active\n"
            f"• Time: `{timestamp}`"
        )
        send_telegram(msg)

if __name__ == "__main__":
    check_deals()
  
