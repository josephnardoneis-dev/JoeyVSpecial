#!/usr/bin/env python3
"""
Real Oddshopper Free Picks Scraper

Scrapes actual expert picks from https://www.oddsshopper.com/expert-picks/free
"""

import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import time
import pytz

class OddshopperScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.base_url = "https://www.oddsshopper.com"
        self.free_picks_url = "https://www.oddsshopper.com/expert-picks/free"

    def fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch the HTML content of a page"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_json_data(self, html_content: str) -> List[Dict]:
        """Extract JSON schema data from the page"""
        picks = []

        try:
            # Look for JSON-LD script tags that contain pick data
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find script tags containing JSON data
            script_tags = soup.find_all('script', type='application/ld+json')

            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'productSchemas' in data:
                        picks.extend(data['productSchemas'])
                    elif isinstance(data, list):
                        picks.extend(data)
                except json.JSONDecodeError:
                    continue

            # Also look for any other script tags with JSON data
            all_scripts = soup.find_all('script')
            for script in all_scripts:
                if script.string and 'expert' in script.string.lower() and 'pick' in script.string.lower():
                    # Try to extract JSON objects from the script
                    json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', script.string)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if self.looks_like_pick_data(data):
                                picks.append(data)
                        except json.JSONDecodeError:
                            continue

            return picks

        except Exception as e:
            print(f"Error extracting JSON data: {e}")
            return []

    def looks_like_pick_data(self, data: Dict) -> bool:
        """Check if data structure looks like a pick"""
        pick_indicators = ['expert', 'pick', 'sport', 'team', 'description', 'bet']
        return any(indicator in str(data).lower() for indicator in pick_indicators)

    def parse_pick_from_json(self, json_data: Dict) -> Optional[Dict]:
        """Parse a pick from JSON schema data"""
        try:
            # Try to extract pick information from various JSON structures
            pick = {
                'raw_data': json_data,
                'expert': None,
                'pick': None,
                'sport': None,
                'date': None,
                'description': None
            }

            # Common field mappings
            if 'name' in json_data:
                pick['expert'] = json_data['name']
            elif 'author' in json_data:
                pick['expert'] = json_data.get('author', {}).get('name')

            if 'description' in json_data:
                pick['description'] = json_data['description']
                pick['pick'] = json_data['description']

            if 'datePublished' in json_data:
                pick['date'] = json_data['datePublished']
            elif 'dateCreated' in json_data:
                pick['date'] = json_data['dateCreated']

            # Try to identify sport
            text_content = str(json_data).lower()
            if any(sport in text_content for sport in ['nfl', 'football']):
                pick['sport'] = 'NFL'
            elif any(sport in text_content for sport in ['mlb', 'baseball']):
                pick['sport'] = 'MLB'
            elif any(sport in text_content for sport in ['nba', 'basketball']):
                pick['sport'] = 'NBA'
            elif any(sport in text_content for sport in ['soccer', 'mls']):
                pick['sport'] = 'Soccer'

            return pick if pick['expert'] and pick['pick'] else None

        except Exception as e:
            print(f"Error parsing pick from JSON: {e}")
            return None

    def extract_picks_from_html(self, html_content: str) -> List[Dict]:
        """Fallback method to extract picks from HTML structure"""
        picks = []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Look for common pick container patterns
            pick_containers = []

            # Try various selectors that might contain picks
            selectors = [
                '[class*="pick"]',
                '[class*="expert"]',
                '[class*="bet"]',
                '[class*="prediction"]',
                '.card',
                '.item',
                '.post'
            ]

            for selector in selectors:
                containers = soup.select(selector)
                pick_containers.extend(containers)

            for container in pick_containers:
                text = container.get_text().strip()
                if len(text) > 20 and any(word in text.lower() for word in ['pick', 'bet', 'over', 'under', 'moneyline']):
                    pick = {
                        'expert': 'Unknown',
                        'pick': text[:200],  # Limit length
                        'sport': 'Unknown',
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'raw_html': str(container)[:500]
                    }
                    picks.append(pick)

            return picks

        except Exception as e:
            print(f"Error extracting picks from HTML: {e}")
            return []

    def get_yesterdays_picks(self) -> List[Dict]:
        """Get picks from yesterday (Eastern time)"""
        # Use Eastern time
        eastern = pytz.timezone('US/Eastern')
        now_eastern = datetime.now(eastern)
        yesterday_eastern = now_eastern - timedelta(days=1)
        return self.get_picks_for_date(yesterday_eastern)

    def get_picks_for_date(self, target_date: datetime) -> List[Dict]:
        """Get picks for a specific date"""
        print(f"🔍 Scraping Oddshopper free picks for {target_date.strftime('%Y-%m-%d')}")

        # Fetch the main free picks page
        html_content = self.fetch_page_content(self.free_picks_url)

        if not html_content:
            print("❌ Failed to fetch page content")
            return []

        print(f"✅ Fetched page content ({len(html_content)} characters)")

        # Extract picks from JSON data
        json_picks = self.extract_json_data(html_content)
        parsed_picks = []

        for json_data in json_picks:
            pick = self.parse_pick_from_json(json_data)
            if pick:
                parsed_picks.append(pick)

        print(f"📊 Found {len(parsed_picks)} picks from JSON data")

        # If no JSON picks found, try HTML extraction
        if not parsed_picks:
            print("🔄 Trying HTML extraction as fallback...")
            html_picks = self.extract_picks_from_html(html_content)
            parsed_picks.extend(html_picks)
            print(f"📊 Found {len(html_picks)} additional picks from HTML")

        # Filter picks for the target date
        date_filtered_picks = []
        target_date_str = target_date.strftime('%Y-%m-%d')

        for pick in parsed_picks:
            pick_date = pick.get('date', '') or ''
            if target_date_str in pick_date or not pick_date:
                # If no date or matches target date, include it
                pick['date'] = target_date_str  # Standardize date
                date_filtered_picks.append(pick)

        print(f"🎯 Final result: {len(date_filtered_picks)} picks for {target_date_str}")

        return date_filtered_picks

    def save_picks_to_file(self, picks: List[Dict], date: str) -> str:
        """Save picks to a JSON file"""
        filename = f"real_picks_{date}.json"

        data = {
            'date': date,
            'total_picks': len(picks),
            'scraped_at': datetime.now().isoformat(),
            'source': 'https://www.oddsshopper.com/expert-picks/free',
            'picks': picks
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        return filename

def main():
    """Main function to test the scraper"""
    scraper = OddshopperScraper()

    print("🚀 Starting Real Oddshopper Scraper")
    print("=" * 50)

    # Get yesterday's picks
    yesterday_picks = scraper.get_yesterdays_picks()

    if yesterday_picks:
        yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        filename = scraper.save_picks_to_file(yesterday_picks, yesterday_date)

        print(f"\n✅ Successfully scraped {len(yesterday_picks)} picks")
        print(f"💾 Saved to: {filename}")

        # Show sample picks
        print(f"\n📋 Sample picks:")
        for i, pick in enumerate(yesterday_picks[:3]):
            print(f"{i+1}. {pick.get('expert', 'Unknown')} - {pick.get('pick', 'N/A')[:100]}...")

    else:
        print("❌ No picks found")

if __name__ == "__main__":
    main()