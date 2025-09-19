import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from typing import List, Dict, Any
import time
from database import BetTrackerDB

class EnhancedScraper:
    def __init__(self):
        self.base_url = "https://www.oddsshopper.com/expert-picks/free"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.db = BetTrackerDB()

    def find_all_experts_fast(self) -> List[Dict[str, Any]]:
        """Fast method to find all experts and their picks"""
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            picks = []

            print(f"Page loaded: {len(response.content)} bytes")

            # Method 1: JSON-LD Product schemas (fastest)
            json_scripts = soup.find_all('script', type='application/ld+json')
            print(f"Found {len(json_scripts)} JSON-LD scripts")

            for i, script in enumerate(json_scripts):
                if script.string:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and data.get('@type') == 'Product':
                            pick = self.extract_expert_pick(data)
                            if pick:
                                picks.append(pick)
                                print(f"✓ Expert: {pick.get('expert', 'Unknown')}")

                    except json.JSONDecodeError:
                        continue

            print(f"Found {len(picks)} picks via JSON-LD")

            # Method 2: Search for expert names in all text
            all_text = soup.get_text()
            expert_names = self.find_expert_names_in_text(all_text)
            print(f"Found potential expert names: {expert_names}")

            # Method 3: Look for specific patterns
            additional_picks = self.find_picks_by_patterns(soup)
            picks.extend(additional_picks)

            # Remove duplicates
            seen_experts = set()
            unique_picks = []
            for pick in picks:
                expert = pick.get('expert', 'Unknown')
                if expert not in seen_experts:
                    seen_experts.add(expert)
                    unique_picks.append(pick)

            print(f"Total unique experts found: {len(unique_picks)}")
            for pick in unique_picks:
                print(f"  - {pick.get('expert', 'Unknown')}: {pick.get('bet_details', 'No details')[:50]}...")

            return unique_picks

        except Exception as e:
            print(f"Error in enhanced scraping: {e}")
            return []

    def extract_expert_pick(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Extract expert pick from product schema"""
        try:
            pick = {}

            # Extract expert name
            if 'brand' in product:
                if isinstance(product['brand'], dict):
                    pick['expert'] = product['brand'].get('name', 'Unknown')
                else:
                    pick['expert'] = str(product['brand'])

            # Extract bet details
            description = product.get('description', '')
            name = product.get('name', '')

            if description:
                soup = BeautifulSoup(description, 'html.parser')
                clean_text = soup.get_text(separator=' ').strip()
                pick['bet_details'] = clean_text
            else:
                pick['bet_details'] = name

            # Extract other data
            pick['pick_title'] = name
            pick['sport'] = self.determine_sport(f"{name} {pick.get('bet_details', '')}")
            pick['pick_date'] = datetime.now()

            # Extract odds
            combined_text = f"{name} {pick.get('bet_details', '')}"
            odds = re.findall(r'[+-]\d+', combined_text)
            if odds:
                pick['odds'] = ', '.join(odds)

            return pick if pick.get('expert') else None

        except Exception as e:
            print(f"Error extracting pick: {e}")
            return None

    def find_expert_names_in_text(self, text: str) -> List[str]:
        """Find expert names in page text"""
        expert_names = []

        # Common expert name patterns
        patterns = [
            r'by\s+([A-Z][a-zA-Z\s]+?)(?:\s|$)',
            r'Expert:\s*([A-Z][a-zA-Z\s]+?)(?:\s|$)',
            r'@([A-Z][a-zA-Z\s]+?)(?:\s|$)',
            r'([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+)',  # FirstName LastName
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                name = match.strip()
                if len(name) > 3 and len(name) < 30:  # Reasonable name length
                    expert_names.append(name)

        # Look for specific names
        if 'joseph' in text.lower() and 'nardone' in text.lower():
            expert_names.append('Joseph Nardone')

        return list(set(expert_names))  # Remove duplicates

    def find_picks_by_patterns(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find picks by searching for common betting patterns"""
        picks = []

        # Look for elements containing betting terminology
        betting_elements = soup.find_all(text=re.compile(r'(moneyline|spread|over|under|total|\+\d+|\-\d+)', re.I))

        for element in betting_elements[:20]:  # Limit to first 20
            try:
                # Get parent element for context
                parent = element.parent
                if parent:
                    full_text = parent.get_text(separator=' ')

                    # Try to extract expert name and bet info
                    expert_match = re.search(r'(?:by|expert:?)\s*([A-Z][a-zA-Z\s]+)', full_text, re.I)
                    expert_name = expert_match.group(1).strip() if expert_match else 'Unknown Expert'

                    if len(full_text) > 30:  # Has enough content
                        pick = {
                            'expert': expert_name,
                            'bet_details': full_text[:200],
                            'sport': self.determine_sport(full_text),
                            'pick_date': datetime.now()
                        }

                        # Extract odds
                        odds = re.findall(r'[+-]\d+', full_text)
                        if odds:
                            pick['odds'] = ', '.join(odds)

                        picks.append(pick)

            except Exception:
                continue

        return picks

    def determine_sport(self, text: str) -> str:
        """Determine sport from text"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['nfl', 'football', 'quarterback', 'touchdown']):
            return 'NFL'
        elif any(word in text_lower for word in ['mlb', 'baseball', 'home run', 'strikeout']):
            return 'MLB'
        elif any(word in text_lower for word in ['nba', 'basketball', 'points', 'rebounds']):
            return 'NBA'
        elif any(word in text_lower for word in ['nhl', 'hockey', 'goals', 'assists']):
            return 'NHL'
        elif any(word in text_lower for word in ['soccer', 'football', 'goals', 'champions league']):
            return 'Soccer'
        elif any(word in text_lower for word in ['tennis', 'sets', 'games']):
            return 'Tennis'
        else:
            return 'Other'

    def save_picks(self, picks: List[Dict[str, Any]]) -> int:
        """Save picks to database"""
        saved_count = 0
        for pick in picks:
            try:
                expert_name = pick.get('expert', 'Unknown Expert')
                self.db.add_pick(expert_name, pick)
                saved_count += 1
            except Exception as e:
                print(f"Error saving pick: {e}")
                continue
        return saved_count

    def run(self):
        """Run the enhanced scraper"""
        print("=== ENHANCED EXPERT FINDER ===")
        picks = self.find_all_experts_fast()

        if picks:
            saved_count = self.save_picks(picks)
            print(f"\n✅ SUCCESS: Found {len(picks)} experts, saved {saved_count} picks")

            print("\n📋 EXPERT SUMMARY:")
            for pick in picks:
                expert = pick.get('expert', 'Unknown')
                sport = pick.get('sport', 'Unknown')
                print(f"  • {expert} ({sport})")

        else:
            print("❌ No experts found")

if __name__ == "__main__":
    scraper = EnhancedScraper()
    scraper.run()