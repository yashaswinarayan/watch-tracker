import json
import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STATE_FILE = "dwc_state.json"


def send_telegram(message):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f"Failed to send Telegram message: {e}")


def load_previous_state():
  if os.path.exists(STATE_FILE):
    try:
      with open(STATE_FILE, "r") as f:
        return json.load(f)
    except Exception as e:
      print(f"Error loading state: {e}")
  return {}


def save_current_state(state):
  try:
    with open(STATE_FILE, "w") as f:
      json.dump(state, f, indent=2)
  except Exception as e:
    print(f"Error saving state: {e}")


def check_dwc_restocks():
  headers = {"User-Agent": "Mozilla/5.0"}
  page = 1
  current_catalog = {}
  restocked_watches = []

  # 1. Fetch current catalog and variant availability
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
      product_title = product.get("title", "")
      handle = product.get("handle", "")

      for variant in product.get("variants", []):
        variant_id = str(variant.get("id"))
        is_available = bool(variant.get("available", False))
        price = variant.get("price", "0")
        variant_title = variant.get("title", "")

        display_name = (
            product_title
            if variant_title in ["Default Title", product_title]
            else f"{product_title} ({variant_title})"
        )

        current_catalog[variant_id] = {
            "title": display_name,
            "handle": handle,
            "price": price,
            "available": is_available,
        }

    page += 1

  if not current_catalog:
    print("No products fetched. Skipping update.")
    return

  # 2. Compare against previous state
  previous_state = load_previous_state()

  for variant_id, item in current_catalog.items():
    was_available = previous_state.get(variant_id, {}).get("available", False)
    is_now_available = item["available"]

    # Trigger alert only when previously Out of Stock (or new) and now In Stock
    if is_now_available and not was_available:
      restocked_watches.append(item)

  # 3. Save updated snapshot
  save_current_state(current_catalog)

  # 4. Dispatch Telegram alerts for newly restocked watches
  if restocked_watches:
    for item in restocked_watches:
      try:
        formatted_price = f"₹{float(item['price']):,.0f}"
      except (ValueError, TypeError):
        formatted_price = f"₹{item['price']}"

      msg = (
          f"🚨 *DWC RESTOCK ALERT!*\n\n"
          f"*{item['title']}* is now back in stock!\n"
          f"💰 Price: {formatted_price}\n"
          f"🔗 https://delhiwatchcompany.com/products/{item['handle']}"
      )
      send_telegram(msg)


if __name__ == "__main__":
  check_dwc_restocks()
