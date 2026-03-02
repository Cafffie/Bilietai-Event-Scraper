import re
import os
import time
import json
import logging
import random
import pandas as pd
from datetime import datetime
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
RUN_HEADLESS = True

if not os.path.exists("log"):
    os.makedirs("log")

logging.basicConfig(
    filename="log/scrape.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ------------------------------------------------------------
# UTILITIES
# ------------------------------------------------------------
def log_and_print(message):
    print(message)
    logging.info(message)

def setup_browser():
    options = uc.ChromeOptions()
    if RUN_HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.188 Safari/537.36"
    )

    try:
        return uc.Chrome(options=options, version_main=145)
    except Exception as e:
        log_and_print(f"Driver error: {e}. Trying without explicit version...")
        return uc.Chrome(options=options)

def handle_cookies(driver):
    try:
        cookie_btn_selector = "button#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, cookie_btn_selector))
        )
        driver.find_element(By.CSS_SELECTOR, cookie_btn_selector).click()
        log_and_print("Cookies accepted.")
        time.sleep(1) 
    except TimeoutException:
        pass 


# ------------------------------------------------------------
# EXTRACTION LOGIC
# ------------------------------------------------------------
def extract_all_fields(driver, category):
    data_out = {
        "title": None, "venue_url": driver.current_url, "category": category,
        "venue": None, "address": None, "city": None, "country": None,
        "open_date": None, "close_date": None, "booking_start_date": None,
        "booking_end_date": None, "upcoming_performances": [], 
        "currency": None, "seat_pricing": {}, 
        "scrape_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        # 1. Parse JSON-LD for Core Metadata
        scripts = driver.find_elements(By.XPATH, "//script[@type='application/ld+json']")
        for script in scripts:
            try:
                raw_data = json.loads(script.get_attribute('innerHTML'))
                if isinstance(raw_data, dict) and raw_data.get('@type') == 'Event':
                    data_out["title"] = raw_data.get("name")
                    data_out["open_date"] = raw_data.get("startDate")
                    data_out["close_date"] = raw_data.get("endDate")
                    
                    loc = raw_data.get("location", {})
                    data_out["venue"] = loc.get("name")
                    
                    addr = loc.get("address", {})
                    data_out["address"] = addr.get("streetAddress")
                    data_out["city"] = addr.get("addressLocality")

                    # Handle country (can be string or dict)
                    country_data = addr.get("addressCountry")
                    if isinstance(country_data, dict):
                        data_out["country"] = country_data.get("name")
                    else:
                        data_out["country"] = country_data

                    offers = raw_data.get("offers", {})
                    if isinstance(offers, dict):
                        data_out["currency"] = offers.get("priceCurrency", "EUR")
                        data_out["booking_start_date"] = offers.get("validFrom")
                        data_out["booking_end_date"] = data_out["close_date"]

                    # Extract Time from Detail Page
                    try:
                        time_elements = driver.find_elements(By.CSS_SELECTOR, ".concert_details_date, .event_short_time")
                        event_time = None
                        for te in time_elements:
                            found_time = re.search(r'(\d{2}:\d{2})', te.text)
                            if found_time:
                                event_time = found_time.group(1)
                                break
            
                        data_out["upcoming_performances"].append({
                            'date': data_out["open_date"],
                            'time': event_time
                        })
                    except: 
                        pass
                    break
            except json.JSONDecodeError:
                continue

        # 2. Seat Pricing
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, ".concert_details_pricing_value")
            data_out["seat_pricing"] = {
                data_out['open_date']: [{"seat": "General", "ticket_price": price_element.text}]
            }
        except: 
            pass


    except Exception as e:
        log_and_print(f"Error extracting data: {e}")

    return data_out

# ------------------------------------------------------------
# MAIN EXECUTION LOOP
# ------------------------------------------------------------
def scrape_bilietai():
    driver = setup_browser()
    if not driver:
        return

    all_final_data = []
    TARGET_CATEGORIES = [
        ("https://www.bilietai.lt/eng/tickets/koncertai/", "Music"),
        ("https://www.bilietai.lt/eng/tickets/teatras/", "Theatre"),
        ("https://www.bilietai.lt/eng/tickets/muziejai/", "Museums"),
        ("https://www.bilietai.lt/eng/tickets/sportas/", "Sports"),
        ("https://www.bilietai.lt/eng/tickets/festivaliai/", "Festivals"),
        ("https://www.bilietai.lt/eng/tickets/parodos/", "Exhibitions"),
        ("https://www.bilietai.lt/eng/tickets/kinas/", "Cinema"),
        ("https://www.bilietai.lt/eng/tickets/kita/", "Other"),
        ("https://www.bilietai.lt/eng/tickets/dovanu-cekiai/", "gift card"),
    ]

    try:
        for url, category_name in TARGET_CATEGORIES:
            log_and_print(f"--- Accessing Category: {category_name} ---")
            driver.get(url)
            handle_cookies(driver)
            
            # --- Scroll to load lazy events (needed for Exhibitions) ---
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            while scroll_attempts < 5:  # max 5 scrolls
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_attempts += 1

            # Wait for any event_short elements to appear
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.event_short"))
                )
            except TimeoutException:
                log_and_print(f"No events found immediately for {category_name}. Retrying with refresh...")
                driver.refresh()
                time.sleep(5)

            # Collect all event links (including Exhibition class)
            links = [e.get_attribute("href") for e in driver.find_elements(By.CSS_SELECTOR, "a.event_short")]

            if not links:
                log_and_print(f"Skip: Still no events found for {category_name}")
                continue

            for index, link in enumerate(links[:5]):  # limit to first 5 for testing
                log_and_print(f"[{index+1}/{len(links)}] Scraping: {link}")
                driver.get(link)
                time.sleep(random.uniform(2, 3))
                
                event_details = extract_all_fields(driver, category_name)
                all_final_data.append(event_details)

        if all_final_data:
            df = pd.DataFrame(all_final_data)
            filename = f"bilietai_1.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            log_and_print(f"SUCCESS: Saved {len(all_final_data)} events to {filename}")

    finally:
        driver.quit()

# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------   
if __name__ == "__main__":
        scrape_bilietai()