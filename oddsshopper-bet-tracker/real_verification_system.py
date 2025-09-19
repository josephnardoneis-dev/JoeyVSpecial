#!/usr/bin/env python3
"""
Real Verification System

Verify actual expert picks against real ESPN game results
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time

class RealVerificationSystem:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_nfl_games(self, date_str: str) -> List[Dict]:
        """Get NFL games from ESPN for a specific date"""
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            params = {'dates': date_str}

            print(f"🏈 Fetching NFL games for {date_str}")
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                games = data.get('events', [])
                print(f"   Found {len(games)} NFL games")
                return games

        except Exception as e:
            print(f"❌ Error fetching NFL games: {e}")

        return []

    def get_mlb_games(self, date_str: str) -> List[Dict]:
        """Get MLB games from ESPN for a specific date"""
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
            params = {'dates': date_str}

            print(f"⚾ Fetching MLB games for {date_str}")
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                games = data.get('events', [])
                print(f"   Found {len(games)} MLB games")
                return games

        except Exception as e:
            print(f"❌ Error fetching MLB games: {e}")

        return []

    def get_nhl_games(self, date_str: str) -> List[Dict]:
        """Get NHL games from ESPN for a specific date"""
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
            params = {'dates': date_str}

            print(f"🏒 Fetching NHL games for {date_str}")
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                games = data.get('events', [])
                print(f"   Found {len(games)} NHL games")
                return games

        except Exception as e:
            print(f"❌ Error fetching NHL games: {e}")

        return []

    def get_cfb_games(self, date_str: str) -> List[Dict]:
        """Get College Football games from ESPN for a specific date"""
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
            params = {'dates': date_str}

            print(f"🏈🎓 Fetching CFB games for {date_str}")
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                games = data.get('events', [])
                print(f"   Found {len(games)} CFB games")
                return games

        except Exception as e:
            print(f"❌ Error fetching CFB games: {e}")

        return []

    def verify_nfl_player_prop(self, bet: Dict, games: List[Dict]) -> Dict:
        """Verify NFL player prop against game data"""
        structured_bet = bet['structured_bet']
        player_name = structured_bet.get('player', '').lower()
        stat_type = structured_bet.get('stat', '').lower()
        line = structured_bet.get('line')
        side = structured_bet.get('side', '').lower()

        print(f"🔍 Verifying: {player_name} {side} {line} {stat_type}")

        # For now, since ESPN API doesn't provide detailed player stats in scoreboard
        # We'll return a manual verification status
        # In production, you'd integrate with a detailed stats API

        # Example specific checks for known players
        if 'chase' in player_name and 'receiving' in stat_type:
            # Ja'Marr Chase receiving yards - check Bengals game
            for game in games:
                competitors = game.get('competitions', [{}])[0].get('competitors', [])
                for comp in competitors:
                    team_name = comp.get('team', {}).get('displayName', '').lower()
                    if 'bengals' in team_name or 'cincinnati' in team_name:
                        # Game found, but ESPN scoreboard doesn't have individual player stats
                        return {
                            'status': 'needs_manual_verification',
                            'result': None,
                            'notes': f'Found Bengals game but need detailed stats API for {player_name} receiving yards',
                            'game_info': {
                                'teams': [c.get('team', {}).get('displayName') for c in competitors],
                                'score': [c.get('score') for c in competitors],
                                'completed': game.get('status', {}).get('type', {}).get('completed', False)
                            }
                        }

        return {
            'status': 'api_limitation',
            'result': None,
            'notes': f'ESPN scoreboard API does not include detailed player stats for {stat_type}'
        }

    def verify_spread_bet(self, bet: Dict, games: List[Dict]) -> Dict:
        """Verify spread bet against game results"""
        structured_bet = bet['structured_bet']
        team = structured_bet.get('team', '').upper()
        line = structured_bet.get('line')

        print(f"🔍 Verifying: {team} {line:+}")

        # Convert team abbreviations to full names for matching
        # Determine sport context for proper team mapping
        sport = bet.get('sport', '').upper()

        if sport == 'MLB':
            team_mappings = {
                'MIL': ['milwaukee', 'brewers'],
                'LAD': ['los angeles', 'dodgers'],
                'ATH': ['athletics', 'oakland'],
                'TOR': ['toronto', 'blue jays'],
                'TB': ['tampa bay', 'rays'],
                'KC': ['kansas city', 'royals'],
                'CLE': ['cleveland', 'guardians'],
                'DET': ['detroit', 'tigers']
            }
        elif sport == 'NHL' or sport == 'HOCKEY':
            team_mappings = {
                'TOR': ['toronto', 'maple leafs'],
                'BOS': ['boston', 'bruins'],
                'NYR': ['new york', 'rangers'],
                'NYI': ['new york', 'islanders'],
                'FLA': ['florida', 'panthers'],
                'TB': ['tampa bay', 'lightning'],
                'WAS': ['washington', 'capitals'],
                'CAR': ['carolina', 'hurricanes'],
                'PHI': ['philadelphia', 'flyers'],
                'PIT': ['pittsburgh', 'penguins'],
                'COL': ['colorado', 'avalanche'],
                'VGK': ['vegas', 'golden knights'],
                'EDM': ['edmonton', 'oilers'],
                'CGY': ['calgary', 'flames'],
                'VAN': ['vancouver', 'canucks'],
                'SEA': ['seattle', 'kraken'],
                'MIN': ['minnesota', 'wild'],
                'WPG': ['winnipeg', 'jets'],
                'STL': ['st. louis', 'blues'],
                'CHI': ['chicago', 'blackhawks'],
                'NSH': ['nashville', 'predators'],
                'DAL': ['dallas', 'stars'],
                'ANA': ['anaheim', 'ducks'],
                'LAK': ['los angeles', 'kings'],
                'SJS': ['san jose', 'sharks'],
                'ARI': ['arizona', 'coyotes'],
                'NJD': ['new jersey', 'devils'],
                'CBJ': ['columbus', 'blue jackets'],
                'DET': ['detroit', 'red wings'],
                'BUF': ['buffalo', 'sabres'],
                'MTL': ['montreal', 'canadiens'],
                'OTT': ['ottawa', 'senators']
            }
        elif sport == 'COLLEGE FOOTBALL' or sport == 'CFB':
            # College football team mappings
            team_mappings = {
                'OSU': ['oklahoma state', 'cowboys'],
                'OKST': ['oklahoma state', 'cowboys'],
                'TULSA': ['tulsa', 'golden hurricane'],
                'OU': ['oklahoma', 'sooners'],
                'BAYLOR': ['baylor', 'bears'],
                'TCU': ['tcu', 'horned frogs'],
                'TEXAS': ['texas', 'longhorns'],
                'UT': ['texas', 'longhorns'],
                'TAMU': ['texas a&m', 'aggies'],
                'TTU': ['texas tech', 'red raiders'],
                'WVU': ['west virginia', 'mountaineers'],
                'ISU': ['iowa state', 'cyclones'],
                'KU': ['kansas', 'jayhawks'],
                'KSU': ['kansas state', 'wildcats'],
                'UGA': ['georgia', 'bulldogs'],
                'ALA': ['alabama', 'crimson tide'],
                'BAMA': ['alabama', 'crimson tide'],
                'LSU': ['lsu', 'tigers'],
                'UF': ['florida', 'gators'],
                'UT': ['tennessee', 'volunteers'],
                'MISS': ['ole miss', 'rebels'],
                'MSU': ['mississippi state', 'bulldogs'],
                'SC': ['south carolina', 'gamecocks'],
                'UK': ['kentucky', 'wildcats'],
                'MIZZOU': ['missouri', 'tigers'],
                'ARK': ['arkansas', 'razorbacks'],
                'VANDY': ['vanderbilt', 'commodores'],
                'CLEMSON': ['clemson', 'tigers'],
                'FSU': ['florida state', 'seminoles'],
                'MIAMI': ['miami', 'hurricanes'],
                'VT': ['virginia tech', 'hokies'],
                'UVA': ['virginia', 'cavaliers'],
                'DUKE': ['duke', 'blue devils'],
                'UNC': ['north carolina', 'tar heels'],
                'NCSU': ['nc state', 'wolfpack'],
                'WAKE': ['wake forest', 'demon deacons'],
                'BC': ['boston college', 'eagles'],
                'PITT': ['pittsburgh', 'panthers'],
                'LOU': ['louisville', 'cardinals'],
                'ND': ['notre dame', 'fighting irish'],
                'OHIO': ['ohio state', 'buckeyes'],
                'MICH': ['michigan', 'wolverines'],
                'MSU': ['michigan state', 'spartans'],
                'PSU': ['penn state', 'nittany lions'],
                'WISC': ['wisconsin', 'badgers'],
                'MINN': ['minnesota', 'golden gophers'],
                'IOWA': ['iowa', 'hawkeyes'],
                'ILL': ['illinois', 'fighting illini'],
                'NW': ['northwestern', 'wildcats'],
                'NEB': ['nebraska', 'cornhuskers'],
                'IND': ['indiana', 'hoosiers'],
                'PUR': ['purdue', 'boilermakers'],
                'RUT': ['rutgers', 'scarlet knights'],
                'MD': ['maryland', 'terrapins'],
                'USC': ['usc', 'trojans'],
                'UCLA': ['ucla', 'bruins'],
                'WASH': ['washington', 'huskies'],
                'ORE': ['oregon', 'ducks'],
                'ORST': ['oregon state', 'beavers'],
                'STAN': ['stanford', 'cardinal'],
                'CAL': ['california', 'golden bears'],
                'WSU': ['washington state', 'cougars'],
                'UTAH': ['utah', 'utes'],
                'COL': ['colorado', 'buffaloes'],
                'ASU': ['arizona state', 'sun devils'],
                'ARIZ': ['arizona', 'wildcats']
            }
        else:  # NFL or other
            team_mappings = {
                'MIA': ['miami', 'dolphins'],
                'BUF': ['buffalo', 'bills'],
                'KC': ['kansas city', 'chiefs'],
                'CLE': ['cleveland', 'browns'],
                'DET': ['detroit', 'lions']
            }

        team_keywords = team_mappings.get(team, [team.lower()])

        for game in games:
            competitors = game.get('competitions', [{}])[0].get('competitors', [])

            # Check if our team is in this game
            team_found = False
            home_team = None
            away_team = None

            for comp in competitors:
                team_name = comp.get('team', {}).get('displayName', '').lower()
                if any(keyword in team_name for keyword in team_keywords):
                    team_found = True

                if comp.get('homeAway') == 'home':
                    home_team = comp
                else:
                    away_team = comp

            if team_found and home_team and away_team:
                home_score = int(home_team.get('score', 0))
                away_score = int(away_team.get('score', 0))
                completed = game.get('status', {}).get('type', {}).get('completed', False)

                if not completed:
                    return {
                        'status': 'game_not_completed',
                        'result': None,
                        'notes': f'Game not yet completed: {away_team.get("team", {}).get("displayName")} @ {home_team.get("team", {}).get("displayName")}'
                    }

                # Determine which team we bet on and calculate result
                home_name = home_team.get('team', {}).get('displayName', '').lower()
                away_name = away_team.get('team', {}).get('displayName', '').lower()

                bet_on_home = any(keyword in home_name for keyword in team_keywords)

                if bet_on_home:
                    # Bet on home team
                    spread_result = home_score + line
                    won = spread_result > away_score
                    team_display = home_team.get('team', {}).get('displayName')
                else:
                    # Bet on away team
                    spread_result = away_score + line
                    won = spread_result > home_score
                    team_display = away_team.get('team', {}).get('displayName')

                return {
                    'status': 'verified',
                    'result': 'win' if won else 'loss',
                    'notes': f'{team_display} {line:+} - Final: {away_team.get("team", {}).get("displayName")} {away_score}, {home_team.get("team", {}).get("displayName")} {home_score}',
                    'game_info': {
                        'away_team': away_team.get('team', {}).get('displayName'),
                        'home_team': home_team.get('team', {}).get('displayName'),
                        'away_score': away_score,
                        'home_score': home_score,
                        'spread_line': line,
                        'bet_team': team_display,
                        'spread_result': spread_result
                    }
                }

        return {
            'status': 'team_not_found',
            'result': None,
            'notes': f'Could not find game for team {team}'
        }

    def verify_moneyline_bet(self, bet: Dict, games: List[Dict]) -> Dict:
        """Verify moneyline bet against game results"""
        structured_bet = bet['structured_bet']
        team = structured_bet.get('team', '').upper()

        # Use same team matching logic as spread bets
        return self.verify_spread_bet(
            {'structured_bet': {'team': team, 'line': 0}},
            games
        )

    def verify_bet(self, bet: Dict, date_str: str) -> Dict:
        """Verify a single bet against game results"""
        sport = bet.get('sport', '').upper()
        bet_type = bet.get('bet_type')

        print(f"\n🎯 Verifying {bet['expert']} - {bet_type} ({sport})")

        # Get appropriate games
        if sport == 'NFL':
            games = self.get_nfl_games(date_str)
        elif sport == 'MLB':
            games = self.get_mlb_games(date_str)
        elif sport == 'NHL' or sport == 'HOCKEY':
            games = self.get_nhl_games(date_str)
            # Check if this is international hockey (not NHL)
            structured_bet = bet.get('structured_bet', {})
            team = structured_bet.get('team', '').upper()
            raw_text = bet.get('raw_pick_text', '').lower()

            # International hockey teams that won't be in ESPN NHL API
            intl_hockey_indicators = [
                'hc davos', 'kalpa', 'ingolstadt', 'wolfsburg',
                'int. hockey', 'international hockey', 'european'
            ]

            if any(indicator in raw_text for indicator in intl_hockey_indicators):
                return {
                    'status': 'international_hockey',
                    'result': None,
                    'notes': f'International hockey leagues not supported by ESPN NHL API. Teams: {raw_text[:100]}...'
                }
        elif sport == 'COLLEGE FOOTBALL' or sport == 'CFB':
            games = self.get_cfb_games(date_str)
        else:
            return {
                'status': 'unsupported_sport',
                'result': None,
                'notes': f'Sport {sport} verification not implemented'
            }

        if not games:
            return {
                'status': 'no_games_found',
                'result': None,
                'notes': f'No {sport} games found for {date_str}'
            }

        # Verify based on bet type
        if bet_type == 'player_prop' and sport == 'NFL':
            return self.verify_nfl_player_prop(bet, games)
        elif bet_type == 'spread':
            return self.verify_spread_bet(bet, games)
        elif bet_type == 'moneyline':
            return self.verify_moneyline_bet(bet, games)
        else:
            return {
                'status': 'unsupported_bet_type',
                'result': None,
                'notes': f'Bet type {bet_type} verification not implemented'
            }

    def verify_all_bets(self, parsed_picks_file: str) -> List[Dict]:
        """Verify all bets from parsed picks file"""
        print("🚀 REAL BET VERIFICATION SYSTEM")
        print("="*50)

        with open(parsed_picks_file, 'r') as f:
            data = json.load(f)

        bets = data.get('bets', [])
        verified_bets = []

        # Get the date from first bet
        date_str = bets[0].get('date', '').replace('-', '') if bets else '20250918'

        print(f"📅 Verifying bets for date: {date_str}")
        print(f"🎯 Total bets to verify: {len(bets)}")

        for i, bet in enumerate(bets, 1):
            print(f"\n[{i}/{len(bets)}]", end=" ")

            verification = self.verify_bet(bet, date_str)

            bet['verification'] = verification
            bet['verified_at'] = datetime.now().isoformat()

            verified_bets.append(bet)

            # Show result
            status = verification.get('result')
            if status == 'win':
                print("   ✅ WIN")
            elif status == 'loss':
                print("   ❌ LOSS")
            else:
                print(f"   ⏳ {verification.get('status', 'Unknown')}")

            if verification.get('notes'):
                print(f"   📝 {verification['notes']}")

            time.sleep(0.5)  # Be nice to ESPN API

        return verified_bets

    def generate_results_report(self, verified_bets: List[Dict]):
        """Generate a comprehensive results report"""
        print("\n" + "="*80)
        print("📊 VERIFICATION RESULTS REPORT")
        print("="*80)

        # Filter bets with actual results
        completed_bets = [b for b in verified_bets if b.get('verification', {}).get('result') in ['win', 'loss']]

        if not completed_bets:
            print("❌ No bets could be verified with win/loss results")
            return

        wins = len([b for b in completed_bets if b['verification']['result'] == 'win'])
        losses = len([b for b in completed_bets if b['verification']['result'] == 'loss'])
        total = len(completed_bets)

        print(f"📈 OVERALL RESULTS:")
        print(f"   Total Verified: {total}")
        print(f"   Wins: {wins}")
        print(f"   Losses: {losses}")
        print(f"   Accuracy: {(wins/total*100):.1f}%")

        # Expert breakdown
        experts = {}
        for bet in completed_bets:
            expert = bet['expert']
            result = bet['verification']['result']

            if expert not in experts:
                experts[expert] = {'wins': 0, 'losses': 0, 'bets': []}

            if result == 'win':
                experts[expert]['wins'] += 1
            else:
                experts[expert]['losses'] += 1
            experts[expert]['bets'].append(bet)

        print(f"\n👥 EXPERT PERFORMANCE:")
        print("-" * 50)

        for expert, data in experts.items():
            total_expert = data['wins'] + data['losses']
            accuracy = (data['wins'] / total_expert * 100) if total_expert > 0 else 0

            print(f"\n🎯 {expert}")
            print(f"   Record: {data['wins']}-{data['losses']} ({accuracy:.1f}%)")

            for bet in data['bets']:
                result_emoji = "✅" if bet['verification']['result'] == 'win' else "❌"
                bet_info = bet['structured_bet'].get('raw_text', bet.get('raw_pick_text', 'Unknown bet'))[:50]
                print(f"   {result_emoji} {bet['sport']} - {bet_info}...")

def main():
    """Main verification function"""
    verifier = RealVerificationSystem()

    # Verify all parsed bets
    verified_bets = verifier.verify_all_bets('parsed_picks_2025-09-18.json')

    # Generate report
    verifier.generate_results_report(verified_bets)

    # Save results
    output_file = 'verified_results_real_2025-09-18.json'
    with open(output_file, 'w') as f:
        json.dump({
            'verified_at': datetime.now().isoformat(),
            'total_bets': len(verified_bets),
            'verified_bets': verified_bets
        }, f, indent=2)

    print(f"\n💾 Full results saved to: {output_file}")

if __name__ == "__main__":
    main()