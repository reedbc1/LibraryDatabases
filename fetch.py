import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import time


BASE_URL = "https://www.slcl.org"
START_URL = "https://www.slcl.org/research-learn/resources-a-to-z"


def parse_cards(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for card in soup.select("div.horizontal_card"):
        title_tag = card.select_one("h3 a")
        desc_tag = card.select_one(".field-summary")
        badge_divs = card.select(".badge")

        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = urljoin(BASE_URL, title_tag.get("href", ""))
        description = desc_tag.get_text(" ", strip=True) if desc_tag else ""

        badges = []
        for badge in badge_divs:
            text = badge.get_text(" ", strip=True)
            if text:
                badges.append(text)

        resource_type = next(
            (b for b in badges if b in {"Website", "Subscription Database"}),
            None,
        )

        results.append({
            "title": title,
            "description": description,
            "link": link,
            "type": resource_type,
        })

    return results


def fetch_page(session: requests.Session, page_num: int) -> str:
    if page_num == 0:
        url = START_URL
    else:
        url = f"{START_URL}?page={page_num}"

    response = session.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.slcl.org/research-learn",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def scrape_all_resources(max_pages: int = 100, delay: float = 0.5) -> list[dict]:
    all_results = []
    seen_links = set()

    with requests.Session() as session:
        for page_num in range(max_pages):
            print(f"Fetching page {page_num}...")

            html = fetch_page(session, page_num)
            page_results = parse_cards(html)

            if not page_results:
                print(f"No cards found on page {page_num}. Stopping.")
                break

            new_count = 0
            for item in page_results:
                if item["link"] not in seen_links:
                    seen_links.add(item["link"])
                    all_results.append(item)
                    new_count += 1

            print(f"Found {len(page_results)} cards, added {new_count} new items.")

            time.sleep(delay)

    return all_results


if __name__ == "__main__":
    resources = scrape_all_resources()

    print(f"\nTotal resources collected: {len(resources)}")
    print(json.dumps(resources[:5], indent=2, ensure_ascii=False))

    with open("slcl_resources.json", "w", encoding="utf-8") as f:
        json.dump(resources, f, indent=2, ensure_ascii=False)