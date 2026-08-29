import os
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Main watch category URLs on HMT
HMT_URLS = [
    "https://www.hmtwatches.in/collections/mechanical",
    "https://www.hmtwatches.in/collections/automatic",
    "https://www.hmtwatches.in/collections/quartz",
]

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

def check_hmt_stock():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    restocked_watches = []

    for category_url in HMT_URLS:
        try:
            response = requests.get(category_url, headers=headers, timeout=20)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            
            # Locate product cards
            products = soup.select(".product-card, .product-item, .grid-product")

            for prod in products:
                text_content = prod.get_text().lower()
                
                # If marked out of stock or sold out, skip
                if "sold out" in text_content or "out of stock" in text_content:
                    continue

                # Extract title and link
                title_elem = prod.select_one("a.product-card__title, .product-title, h3, h2")
                link_elem = prod.select_one("a[href*='/products/']") or prod.select_one("a")

                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    raw_link = link_elem.get("href", "")
                    link = f"https://www.hmtwatches.in{raw_link}" if raw_link.startswith("/") else raw_link
                    
                    price_elem = prod.select_one(".price, .money, .price__regular")
                    price = price_elem.get_text(strip=True) if price_elem else "N/A"

                    restocked_watches.append((title, price, link))

        except Exception as e:
            print(f"Error scraping {category_url}: {e}")

    # Send alerts if in-stock watches are detected
    if restocked_watches:
        # Deduplicate results by URL
        unique_watches = {item[2]: item for item in restocked_watches}.values()
        
        for title, price, link in unique_watches:
            msg = (
                f"🚨 *HMT Watch In Stock Alert!*\n\n"
                f"*{title}*\n"
                f"💰 Price: {price}\n"
                f"🔗 {link}"
            )
            send_telegram(msg)

if __name__ == "__main__":
    check_hmt_stock()
