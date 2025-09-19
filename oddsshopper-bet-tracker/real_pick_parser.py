#!/usr/bin/env python3
"""
Real Pick Parser

Parse actual expert picks from Oddshopper into structured betting data
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

class RealPickParser:
    def __init__(self):
        self.parsed_picks = []

    def clean_html(self, html_text: str) -> str:
        """Remove HTML tags and clean up text"""
        if not html_text:
            return ""

        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text()
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_bet_from_text(self, text: str) -> List[Dict]:
        """Extract structured bet information from text"""
        bets = []

        # Common betting patterns
        patterns = [
            # Over/Under patterns: "Chase Over 69.5 Receiving Yards"
            r'(\w+(?:\s+\w+)*)\s+(Over|Under)\s+(\d+\.?\d*)\s+([A-Za-z\s]+)',
            # Spread patterns: "MIA 1H +7", "LAD -1.5"
            r'([A-Z]{2,4})\s+(?:1H\s+)?([+-]\d+\.?\d*)',
            # Moneyline patterns: "KC ML", "ATH F5 ML"
            r'([A-Z]{2,4})\s+(?:F5\s+)?ML',
            # Team total patterns: "BUF TT Un 31.5"
            r'([A-Z]{2,4})\s+TT\s+(Un|Ov)\s+(\d+\.?\d*)',
            # Player prop patterns: "D. Achane Ov 52.5 rush yds"
            r'([A-Z]\.?\s+\w+)\s+(Ov|Over)\s+(\d+\.?\d*)\s+([a-z\s]+)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                bet = self.parse_bet_match(match, pattern, text)
                if bet:
                    bets.append(bet)

        return bets

    def parse_bet_match(self, match, pattern: str, full_text: str) -> Optional[Dict]:
        """Parse a regex match into structured bet data"""
        groups = match.groups()

        # Over/Under player props
        if 'Over|Under' in pattern and len(groups) >= 4:
            return {
                'type': 'player_prop',
                'player': groups[0].strip(),
                'side': groups[1].lower(),
                'line': float(groups[2]),
                'stat': groups[3].strip(),
                'raw_text': match.group(0)
            }

        # Team spreads
        elif '[+-]' in pattern and len(groups) >= 2:
            return {
                'type': 'spread',
                'team': groups[0].strip(),
                'line': float(groups[1]),
                'raw_text': match.group(0)
            }

        # Moneylines
        elif 'ML' in pattern:
            return {
                'type': 'moneyline',
                'team': groups[0].strip(),
                'raw_text': match.group(0)
            }

        # Team totals
        elif 'TT' in pattern and len(groups) >= 3:
            return {
                'type': 'team_total',
                'team': groups[0].strip(),
                'side': 'under' if groups[1].lower() in ['un', 'under'] else 'over',
                'line': float(groups[2]),
                'raw_text': match.group(0)
            }

        return None

    def parse_pick(self, pick_data: Dict) -> List[Dict]:
        """Parse a single pick from Oddshopper data"""
        expert = pick_data.get('expert', '').replace(' Free Expert Pick', '').strip()
        raw_text = pick_data.get('pick', '')
        clean_text = self.clean_html(raw_text)

        parsed_bets = []

        # Extract bets from the text
        bets = self.extract_bet_from_text(clean_text)

        for bet in bets:
            parsed_bet = {
                'expert': expert,
                'date': pick_data.get('date'),
                'sport': self.determine_sport(clean_text, bet),
                'bet_type': bet['type'],
                'raw_pick_text': clean_text[:200],  # First 200 chars for context
                'structured_bet': bet,
                'original_data': pick_data
            }
            parsed_bets.append(parsed_bet)

        # If no structured bets found, create a general entry
        if not parsed_bets and clean_text:
            parsed_bets.append({
                'expert': expert,
                'date': pick_data.get('date'),
                'sport': pick_data.get('sport') or self.determine_sport(clean_text, {}),
                'bet_type': 'unknown',
                'raw_pick_text': clean_text[:200],
                'structured_bet': {'type': 'unknown', 'raw_text': clean_text[:100]},
                'original_data': pick_data
            })

        return parsed_bets

    def determine_sport(self, text: str, bet: Dict) -> str:
        """Determine sport from text content"""
        text_lower = text.lower()

        # Check bet context for team abbreviations
        bet_text = bet.get('raw_text', '').upper()

        # MLB team abbreviations
        mlb_teams = ['MIL', 'LAD', 'ATH', 'TOR', 'TB', 'KC', 'CLE', 'DET', 'NYY', 'BOS', 'BAL', 'TB']
        # NFL team abbreviations
        nfl_teams = ['MIA', 'BUF', 'NE', 'NYJ', 'PIT', 'BAL', 'CIN', 'CLE']

        # Check if bet contains specific team abbreviations
        for team in mlb_teams:
            if team in bet_text and team not in ['KC', 'CLE', 'DET']:  # These overlap
                return 'MLB'

        for team in nfl_teams:
            if team in bet_text:
                return 'NFL'

        # Context-based detection
        if 'recap' in text_lower and any(indicator in text_lower for indicator in ['mlb', 'f5', 'baseball']):
            # MoneyBadgerJake's recap mentions MLB and F5 (first 5 innings)
            return 'MLB'
        elif 'recap' in text_lower and any(indicator in text_lower for indicator in ['nfl', '1h', 'rush yds']):
            return 'NFL'

        # Original logic
        if any(word in text_lower for word in ['nfl', 'receiving yards', 'rush yds', 'touchdown', 'quarterback']):
            return 'NFL'
        elif any(word in text_lower for word in ['mlb', 'baseball', 'home run', 'rbi', 'strikeout', 'f5']):
            return 'MLB'
        elif any(word in text_lower for word in ['nba', 'basketball', 'points', 'rebounds', 'assists']) and 'football' not in text_lower:
            return 'NBA'
        elif any(word in text_lower for word in ['soccer', 'goal', 'la liga', 'bundesliga', 'champions league']):
            return 'Soccer'
        elif any(word in text_lower for word in ['college', 'ncaa', 'cfb']):
            return 'College Football'
        elif any(word in text_lower for word in ['hockey', 'nhl', 'puck']):
            return 'Hockey'

        return 'Unknown'

    def parse_all_picks(self, picks_file: str) -> List[Dict]:
        """Parse all picks from a JSON file"""
        print(f"📖 Parsing picks from {picks_file}")

        with open(picks_file, 'r') as f:
            data = json.load(f)

        all_parsed = []
        picks = data.get('picks', [])

        for pick in picks:
            parsed_bets = self.parse_pick(pick)
            all_parsed.extend(parsed_bets)

        print(f"📊 Parsed {len(all_parsed)} structured bets from {len(picks)} raw picks")

        return all_parsed

    def save_parsed_picks(self, parsed_picks: List[Dict], output_file: str):
        """Save parsed picks to JSON file"""
        data = {
            'parsed_at': datetime.now().isoformat(),
            'total_bets': len(parsed_picks),
            'bets': parsed_picks
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"💾 Saved {len(parsed_picks)} parsed bets to {output_file}")

    def show_parsing_summary(self, parsed_picks: List[Dict]):
        """Display summary of parsed picks"""
        print("\n" + "="*60)
        print("📋 PICK PARSING SUMMARY")
        print("="*60)

        # Group by expert
        experts = {}
        sports = {}
        bet_types = {}

        for bet in parsed_picks:
            expert = bet['expert']
            sport = bet['sport']
            bet_type = bet['bet_type']

            experts[expert] = experts.get(expert, 0) + 1
            sports[sport] = sports.get(sport, 0) + 1
            bet_types[bet_type] = bet_types.get(bet_type, 0) + 1

        print(f"🎯 Total Structured Bets: {len(parsed_picks)}")
        print(f"👥 Experts: {len(experts)}")
        print(f"🏈 Sports: {len(sports)}")

        print(f"\n📊 By Expert:")
        for expert, count in sorted(experts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {expert}: {count} bets")

        print(f"\n🏈 By Sport:")
        for sport, count in sorted(sports.items(), key=lambda x: x[1], reverse=True):
            print(f"   {sport}: {count} bets")

        print(f"\n🎲 By Bet Type:")
        for bet_type, count in sorted(bet_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   {bet_type}: {count} bets")

        # Show some examples
        print(f"\n📝 Sample Parsed Bets:")
        for i, bet in enumerate(parsed_picks[:5]):
            structured = bet['structured_bet']
            print(f"{i+1}. {bet['expert']} ({bet['sport']})")
            print(f"   Type: {bet['bet_type']}")
            print(f"   Bet: {structured.get('raw_text', 'N/A')}")
            print()

def main():
    """Test the parser"""
    parser = RealPickParser()

    # Parse the real picks we scraped
    parsed_picks = parser.parse_all_picks('real_picks_2025-09-18.json')

    # Show summary
    parser.show_parsing_summary(parsed_picks)

    # Save parsed picks
    parser.save_parsed_picks(parsed_picks, 'parsed_picks_2025-09-18.json')

    return parsed_picks

if __name__ == "__main__":
    main()