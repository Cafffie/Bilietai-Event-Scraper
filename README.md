# Bilietai Event Scraper

## Scraping structured event data from bilietai.lt using Selenium

---

## Introduction

This project is a Python-based web scraper designed to extract structured event data from **bilietai.lt**, one of the largest ticketing platforms in the Baltics. The script uses **Selenium with undetected-chromedriver** to handle dynamic, JavaScript-heavy pages and collects clean, analysis-ready data such as event details, venues, dates, pricing, and metadata across multiple categories (Concerts, Theatre, Museums, Exhibitions, etc.).

The scraper is built with reliability in mind: it handles cookie banners, lazy-loaded content, SPA quirks, and category-specific inconsistencies (notably Exhibitions).

---

## Visual Helper (High-Level Flow)

```
START
  |
  |--> Launch Chrome (undetected)
  |--> Accept cookies (if present)
  |--> Loop through categories
        |
        |--> Scroll page (lazy load)
        |--> Collect event links
        |--> Visit each event page
              |
              |--> Parse JSON-LD (Event schema)
              |--> Extract venue, dates, pricing
              |--> Save structured record
        |
  |--> Save all events to CSV
END
```

---

## User Instructions (How to Run)

### 1. Clone the repository

```bash
git clone https://github.com/Cafffie/webscrapping_
cd bilietai-scraper
```

### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # Linux / Mac
venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**

* undetected-chromedriver
* selenium
* webdriver-manager
* pandas
* beautifulsoup4
* lxml
* schedule
* openpyxl
* requests
* pymongo
* python-dotenv
* setuptools
* python-dateutil
* pg8000
* cloud-sql-python-connector


### 4. Run the scraper

```bash
python app.py
```

### 5. Output

* A CSV file will be generated: `bilietai_1.csv`
* Logs are written to: `log/scrape.log`

---

## Developer Instructions (How It Works)

### Browser Setup

* Uses `undetected_chromedriver` to reduce bot detection
* Headless mode enabled by default (`RUN_HEADLESS = True`)
* Custom user-agent to mimic a real browser

### Cookie Handling

* Automatically accepts Cookiebot consent dialogs
* Safe timeout handling if the banner does not appear

### Data Extraction Strategy

1. **Category pages**

   * Scrolls multiple times to trigger lazy loading (critical for Exhibitions)
   * Collects all `<a class="event_short">` links

2. **Event pages**

   * Parses `application/ld+json` Event schema
   * Extracts:

     * Title
     * Venue & address
     * City & country
     * Start / end dates
     * Booking dates
     * Currency
     * Basic pricing
     * Event time (when available)

3. **Output format**

   * One row per event
   * Timestamped scrape metadata

### Categories Covered

* Music
* Theatre
* Museums
* Sports
* Festivals
* Exhibitions
* Cinema
* Other
* Gift cards

---

## Contributor Expectations

If you want to contribute:

* Keep selectors **defensive** (expect HTML to change)
* Prefer JSON-LD over DOM scraping when available
* Do not hard-code sleep times unless unavoidable
* Add logs for anything that can fail silently
* Test changes specifically on **Exhibitions** and **Museums** categories

Pull requests should clearly state:

* What broke
* Why the fix works
* Which category/page type was tested

---

## Known Issues & Limitations

* Some events do not expose pricing or time information
* Seat capacity is not universally available (depends on ticket provider)
* Long-running scrapes may trigger throttling
* Page structure may change without notice
* Headless mode may fail occasionally — disable it for debugging

---

## Support the Project 💸

If this scraper saved you time, stress, or helped you ship something faster:

* ⭐ Star the repository
* ☕ Buy the maintainer a coffee
* 💰 Send a small donation (data scraping is pain)

Even small support helps keep this maintained and improved.

---

Happy scraping 🚀
