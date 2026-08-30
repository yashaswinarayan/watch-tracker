import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(message):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f"Failed to send Telegram message: {e}")


def check_dwc_stock():
  headers = {"User-Agent": "Mozilla/5.0"}
  page = 1
  in_stock_watches = []

  while True:
    url = f"https://delhiwatchcompany.com/products.json?limit=250&page={page}"
    try:
      response = requests.get(url, headers=headers, timeout=15)
      if response.status_code != 200:
        break
      products = response.json().get("products", [])
    except Exception as e:
      print(f"Error fetching DWC page {page}: {e}")
      break

    if not products:
      break

    for product in products:
      title = product.get("title", "")
      handle = product.get("handle", "")

      # Check if any variant is currently in stock
      for variant in product.get("variants", []):
        if variant.get("available"):
          price = variant.get("price", "0")
          variant_title = variant.get("title", "")

          display_title = (
              title
              if variant_title in ["Default Title", title]
              else f"{title} ({variant_title})"
          )
          in_stock_watches.append((display_title, price, handle))

    page += 1

  # Send alerts for in-stock watches
  if in_stock_watches:
    # Deduplicate in case variants share identical entries
    seen = set()
    for title, price, handle in in_stock_watches:
      if handle not in seen:
        seen.add(handle)
        try:
          formatted_price = f"₹{float(price):,.0f}"
        except (ValueError, TypeError):
          formatted_price = f"₹{price}"

        msg = (
            f"🚨 *DWC In-Stock Alert!*\n\n"
            f"*{title}*\n"
            f"💰 Price: {formatted_price}\n"
            f"🔗 https://delhiwatchcompany.com/products/{handle}"
        )
        send_telegram(msg)


if __name__ == "__main__":
  check_dwc_stock()
