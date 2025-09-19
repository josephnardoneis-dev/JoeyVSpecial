#!/usr/bin/env python3
"""
Enhanced Expert Scraper for OddsShopper
Finds picks from specific experts across free picks and articles
"""

import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import time
import pytz

class EnhancedExpertScraper:
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

        # Target experts we want to find
        self.target_experts = [
            'Eric Lindquist',
            'Greg Ehrenberg',
            'Ben Rasa',
            'Sam Smith',
            'Joseph Nardone',
            'Jake Hari',
            'Eytan Shander'
        ]

        # Common expert name variations
        self.expert_aliases = {
            'Eric Lindquist': ['eric lindquist', 'elindquist', 'e.lindquist'],
            'Greg Ehrenberg': ['greg ehrenberg', 'gehrenberg', 'g.ehrenberg'],
            'Ben Rasa': ['ben rasa', 'brasa', 'b.rasa', 'jazzraz'],
            'Sam Smith': ['sam smith', 'ssmith', 's.smith'],
            'Joseph Nardone': ['joseph nardone', 'jnardone', 'j.nardone', 'joe nardone'],
            'Jake Hari': ['jake hari', 'jhari', 'j.hari'],
            'Eytan Shander': ['eytan shander', 'eshander', 'e.shander']
        }

    def fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch the HTML content of a page"""
        try:
            print(f"🔍 Fetching: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            return None

    def search_for_expert_content(self) -> List[Dict]:
        """Search multiple OddsShopper sections for expert content"""
        all_picks = []

        # 1. Free picks page
        print("🎯 Checking free picks...")
        free_picks = self.scrape_free_picks()
        all_picks.extend(free_picks)

        # 2. Recent articles
        print("📰 Checking recent articles...")
        article_picks = self.scrape_recent_articles()
        all_picks.extend(article_picks)

        # 3. Premium picks preview (if accessible)
        print("💎 Checking premium picks preview...")
        premium_picks = self.scrape_premium_preview()
        all_picks.extend(premium_picks)

        return all_picks

    def scrape_free_picks(self) -> List[Dict]:
        """Scrape the free picks page"""
        url = "https://www.oddsshopper.com/expert-picks/free"
        html = self.fetch_page_content(url)
        if not html:
            return []

        picks = []
        soup = BeautifulSoup(html, 'html.parser')

        # Look for JSON-LD schema data
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'productSchemas' in data:
                    for item in data['productSchemas']:
                        expert_pick = self.parse_schema_pick(item)
                        if expert_pick:
                            picks.append(expert_pick)
            except:
                continue

        return picks

    def scrape_recent_articles(self) -> List[Dict]:
        """Scrape recent articles for expert picks"""
        picks = []

        # Check main articles page
        url = "https://www.oddsshopper.com/articles"
        html = self.fetch_page_content(url)
        if not html:
            return picks

        soup = BeautifulSoup(html, 'html.parser')

        # Find article links
        article_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/articles/' in href and any(expert.lower().replace(' ', '-') in href for expert in self.target_experts):
                full_url = self.base_url + href if href.startswith('/') else href
                article_links.append(full_url)

        # Check author pages
        for expert in self.target_experts:
            author_slug = expert.lower().replace(' ', '').replace('.', '')
            author_url = f"https://www.oddsshopper.com/articles/author/{author_slug}"
            article_links.append(author_url)

            # Try common variations
            for alias in self.expert_aliases.get(expert, []):
                alias_slug = alias.replace(' ', '').replace('.', '')
                alias_url = f"https://www.oddsshopper.com/articles/author/{alias_slug}"
                article_links.append(alias_url)

        # Scrape each article for picks
        for url in set(article_links[:10]):  # Limit to 10 to avoid overloading
            time.sleep(1)  # Rate limiting
            article_picks = self.scrape_article_picks(url)
            picks.extend(article_picks)

        return picks

    def scrape_premium_preview(self) -> List[Dict]:
        """Try to scrape premium picks preview if available"""
        picks = []

        urls_to_check = [
            "https://www.oddsshopper.com/expert-picks",
            "https://www.oddsshopper.com/expert-picks/premium",
            "https://www.oddsshopper.com/picks"
        ]

        for url in urls_to_check:
            html = self.fetch_page_content(url)
            if html:
                # Look for any expert names in the content
                for expert in self.target_experts:
                    if expert.lower() in html.lower():
                        print(f"✅ Found {expert} mentioned in {url}")
                        # Try to extract picks from this page
                        page_picks = self.extract_picks_from_html(html, expert)
                        picks.extend(page_picks)

        return picks

    def scrape_article_picks(self, url: str) -> List[Dict]:
        """Scrape picks from a specific article"""
        html = self.fetch_page_content(url)
        if not html:
            return []

        picks = []
        soup = BeautifulSoup(html, 'html.parser')

        # Look for the author
        author = None
        author_elements = soup.find_all(['span', 'div', 'p'], class_=re.compile(r'author|byline', re.I))
        for elem in author_elements:
            text = elem.get_text().strip()
            for expert in self.target_experts:
                if expert.lower() in text.lower():
                    author = expert
                    break

        if not author:
            return picks

        print(f"📝 Found article by {author}: {url}")

        # Look for betting picks in the content
        content = soup.find(['div', 'article'], class_=re.compile(r'content|article|post', re.I))
        if content:
            picks_found = self.extract_picks_from_content(content.get_text(), author, url)
            picks.extend(picks_found)

        return picks

    def parse_schema_pick(self, item: Dict) -> Optional[Dict]:
        """Parse a pick from schema.org JSON-LD data"""
        try:
            expert_name = item.get('name', '') or item.get('brand', '')

            # Check if this expert is one we're looking for
            target_expert = None
            for expert in self.target_experts:
                if expert.lower() in expert_name.lower():
                    target_expert = expert
                    break
                # Check aliases
                for alias in self.expert_aliases.get(expert, []):
                    if alias in expert_name.lower():
                        target_expert = expert
                        break

            if not target_expert:
                return None

            pick = {
                'expert': target_expert,
                'raw_data': item,
                'source': 'free_picks',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'description': item.get('description', ''),
                'sport': self.extract_sport_from_text(item.get('description', '')),
                'pick_text': item.get('description', '')
            }

            return pick

        except Exception as e:
            print(f"❌ Error parsing schema pick: {e}")
            return None

    def extract_picks_from_content(self, content: str, author: str, source_url: str) -> List[Dict]:
        """Extract betting picks from article content"""
        picks = []

        # Look for common betting patterns
        betting_patterns = [
            r'(\w+\s+[+-]?\d+\.?\d*)',  # Team +/- spread
            r'(over|under)\s+(\d+\.?\d*)',  # Over/under totals
            r'(\w+)\s+(ml|moneyline)',  # Moneyline
            r'(\w+)\s+to\s+win',  # To win
            r'pick:\s*(.+?)(?:\n|$)',  # "Pick: ..."
            r'bet:\s*(.+?)(?:\n|$)',   # "Bet: ..."
        ]

        found_picks = []
        for pattern in betting_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                found_picks.append(match.group(0).strip())

        if found_picks:
            for pick_text in found_picks[:5]:  # Limit to 5 picks per article
                pick = {
                    'expert': author,
                    'source': 'article',
                    'source_url': source_url,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'pick_text': pick_text,
                    'sport': self.extract_sport_from_text(content),
                    'raw_content': content[:500]  # First 500 chars for context
                }
                picks.append(pick)

        return picks

    def extract_picks_from_html(self, html: str, expert: str) -> List[Dict]:
        """Extract picks from HTML content"""
        picks = []
        soup = BeautifulSoup(html, 'html.parser')

        # Look for sections containing the expert's name
        expert_sections = soup.find_all(text=re.compile(expert, re.I))

        for section in expert_sections[:3]:  # Limit to 3 sections
            parent = section.parent
            if parent:
                section_text = parent.get_text()
                content_picks = self.extract_picks_from_content(section_text, expert, "preview")
                picks.extend(content_picks)

        return picks

    def extract_sport_from_text(self, text: str) -> str:
        """Extract sport from text content"""
        sport_keywords = {
            'NFL': ['nfl', 'football', 'patriots', 'bills', 'cowboys', 'chiefs'],
            'NBA': ['nba', 'basketball', 'lakers', 'celtics', 'warriors'],
            'MLB': ['mlb', 'baseball', 'yankees', 'dodgers', 'astros'],
            'NHL': ['nhl', 'hockey', 'rangers', 'bruins', 'lightning'],
            'CFB': ['college football', 'cfb', 'alabama', 'georgia', 'michigan'],
            'PGA': ['pga', 'golf', 'masters', 'tournament']
        }

        text_lower = text.lower()
        for sport, keywords in sport_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return sport

        return 'Unknown'

    def get_all_expert_picks(self) -> List[Dict]:
        """Get all picks from target experts"""
        print(f"🎯 Searching for picks from: {', '.join(self.target_experts)}")

        all_picks = self.search_for_expert_content()

        # Filter to only target experts
        target_picks = []
        for pick in all_picks:
            if pick.get('expert') in self.target_experts:
                target_picks.append(pick)

        print(f"📊 Found {len(target_picks)} picks from target experts")

        # Group by expert
        expert_counts = {}
        for pick in target_picks:
            expert = pick.get('expert', 'Unknown')
            expert_counts[expert] = expert_counts.get(expert, 0) + 1

        for expert, count in expert_counts.items():
            print(f"   {expert}: {count} picks")

        return target_picks

if __name__ == '__main__':
    scraper = EnhancedExpertScraper()
    picks = scraper.get_all_expert_picks()

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'enhanced_expert_picks_{timestamp}.json'

    with open(output_file, 'w') as f:
        json.dump({
            'scraped_at': datetime.now().isoformat(),
            'target_experts': scraper.target_experts,
            'total_picks': len(picks),
            'picks': picks
        }, f, indent=2)

    print(f"💾 Results saved to: {output_file}")