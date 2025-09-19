#!/usr/bin/env python3
"""
Real Expert Pick Checker

This tool fetches actual expert picks from Oddsshopper and checks real game results.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
from result_verifier import ResultVerifier

class RealPickChecker:
    def __init__(self):
        self.base_url = "https://www.oddsshopper.com/expert-picks/free"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.verifier = ResultVerifier()

    def get_real_picks(self):
        """Get the current real expert picks from the analysis"""
        real_picks = [
            {
                'expert': 'Chef T',
                'pick': 'Christos Tzolis To Score or Assist',
                'sport': 'Soccer',
                'bet_type': 'player_prop',
                'competition': 'Champions League',
                'date': '2025-09-18'
            },
            {
                'expert': 'Big Smokey Picks',
                'pick': 'Oakland Athletics Moneyline',
                'sport': 'MLB',
                'bet_type': 'moneyline',
                'team': 'Oakland Athletics',
                'date': '2025-09-18'
            },
            {
                'expert': 'Big Smokey Picks',
                'pick': 'Toronto Blue Jays -1.5 Run Line',
                'sport': 'MLB',
                'bet_type': 'spread',
                'team': 'Toronto Blue Jays',
                'line': '-1.5',
                'date': '2025-09-18'
            },
            {
                'expert': 'NUKE THE HOUSE',
                'pick': 'Tulsa at Oklahoma State Under 55.5',
                'sport': 'College Football',
                'bet_type': 'total',
                'line': '55.5',
                'side': 'under',
                'teams': ['Tulsa', 'Oklahoma State'],
                'date': '2025-09-18'
            },
            {
                'expert': 'CDR Betting',
                'pick': 'Riley Greene Home Run',
                'sport': 'MLB',
                'bet_type': 'player_prop',
                'player': 'Riley Greene',
                'prop_type': 'home_run',
                'date': '2025-09-18'
            },
            {
                'expert': 'BettingThePitch',
                'pick': 'Christos Tzolis To Score Or Assist',
                'sport': 'Soccer',
                'bet_type': 'player_prop',
                'competition': 'Champions League',
                'date': '2025-09-18'
            }
        ]

        return real_picks

    def check_mlb_results_today(self):
        """Check today's MLB results"""
        try:
            today = datetime.now().strftime('%Y%m%d')
            url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
            params = {'dates': today, 'limit': 100}

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                games = data.get('events', [])

                game_results = []
                for game in games:
                    competition = game.get('competitions', [{}])[0]
                    competitors = competition.get('competitors', [])

                    if len(competitors) >= 2:
                        home_team = next((c for c in competitors if c.get('homeAway') == 'home'), {})
                        away_team = next((c for c in competitors if c.get('homeAway') == 'away'), {})

                        game_info = {
                            'home_team': home_team.get('team', {}).get('displayName'),
                            'away_team': away_team.get('team', {}).get('displayName'),
                            'home_score': int(home_team.get('score', 0)),
                            'away_score': int(away_team.get('score', 0)),
                            'status': game.get('status', {}).get('type', {}).get('description'),
                            'completed': game.get('status', {}).get('type', {}).get('completed', False),
                            'inning': game.get('status', {}).get('period', 0),
                            'game_id': game.get('id')
                        }
                        game_results.append(game_info)

                return game_results

        except Exception as e:
            print(f"Error fetching MLB results: {e}")

        return []

    def check_real_pick_results(self, picks):
        """Check results for real picks"""
        results = []

        # Get current MLB games
        mlb_games = self.check_mlb_results_today()

        print(f"Found {len(mlb_games)} MLB games today")

        for pick in picks:
            print(f"\n🔍 Checking: {pick['expert']} - {pick['pick']}")

            result = {'status': 'pending', 'result': None, 'notes': ''}

            if pick['sport'] == 'MLB':
                result = self.verify_mlb_pick(pick, mlb_games)
            elif pick['sport'] == 'Soccer':
                result = {'status': 'pending', 'result': None, 'notes': 'Soccer games need manual verification'}
            elif pick['sport'] == 'College Football':
                result = {'status': 'pending', 'result': None, 'notes': 'College football games typically on weekends'}
            else:
                result = {'status': 'unsupported', 'result': None, 'notes': f'Sport not supported: {pick["sport"]}'}

            pick['result'] = result
            results.append(pick)

        return results

    def verify_mlb_pick(self, pick, mlb_games):
        """Verify an MLB pick against real game results"""
        team_name = pick.get('team', '').lower()
        pick_text = pick.get('pick', '').lower()

        # Find the relevant game
        relevant_game = None
        for game in mlb_games:
            home_team = game.get('home_team', '').lower()
            away_team = game.get('away_team', '').lower()

            if (team_name in home_team or team_name in away_team or
                any(part in home_team for part in team_name.split()) or
                any(part in away_team for part in team_name.split())):
                relevant_game = game
                break

        if not relevant_game:
            return {'status': 'game_not_found', 'result': None, 'notes': f'Could not find game for {pick.get("team")}'}

        if not relevant_game.get('completed'):
            status_desc = relevant_game.get('status', 'In Progress')
            return {'status': 'in_progress', 'result': None, 'notes': f'Game status: {status_desc}'}

        # Evaluate the pick
        bet_type = pick.get('bet_type', '').lower()

        if bet_type == 'moneyline':
            return self.evaluate_mlb_moneyline(pick, relevant_game)
        elif bet_type == 'spread':
            return self.evaluate_mlb_spread(pick, relevant_game)
        else:
            return {'status': 'unsupported_bet', 'result': None, 'notes': f'Bet type not supported: {bet_type}'}

    def evaluate_mlb_moneyline(self, pick, game):
        """Evaluate MLB moneyline bet"""
        team_name = pick.get('team', '').lower()
        home_team = game.get('home_team', '').lower()
        away_team = game.get('away_team', '').lower()

        home_score = game.get('home_score', 0)
        away_score = game.get('away_score', 0)

        # Determine which team was picked
        if any(part in home_team for part in team_name.split()):
            # Picked home team
            won = home_score > away_score
        elif any(part in away_team for part in team_name.split()):
            # Picked away team
            won = away_score > home_score
        else:
            return {'status': 'team_mismatch', 'result': None, 'notes': 'Could not match team to game'}

        game_score = f"{game.get('away_team')} {away_score} - {home_score} {game.get('home_team')}"

        return {
            'status': 'verified',
            'result': 'win' if won else 'loss',
            'notes': f'Final Score: {game_score}'
        }

    def evaluate_mlb_spread(self, pick, game):
        """Evaluate MLB spread (run line) bet"""
        team_name = pick.get('team', '').lower()
        line = float(pick.get('line', 0))

        home_team = game.get('home_team', '').lower()
        away_team = game.get('away_team', '').lower()

        home_score = game.get('home_score', 0)
        away_score = game.get('away_score', 0)

        # Determine which team was picked and apply spread
        if any(part in home_team for part in team_name.split()):
            # Picked home team
            adjusted_score = home_score + line
            won = adjusted_score > away_score
        elif any(part in away_team for part in team_name.split()):
            # Picked away team
            adjusted_score = away_score + line
            won = adjusted_score > home_score
        else:
            return {'status': 'team_mismatch', 'result': None, 'notes': 'Could not match team to game'}

        game_score = f"{game.get('away_team')} {away_score} - {home_score} {game.get('home_team')}"

        return {
            'status': 'verified',
            'result': 'win' if won else 'loss',
            'notes': f'Final Score: {game_score} (Line: {line:+.1f})'
        }

    def generate_real_report(self, picks_with_results):
        """Generate report with real results"""
        print("\n" + "="*80)
        print("🏆 REAL EXPERT PICK RESULTS - " + datetime.now().strftime('%Y-%m-%d'))
        print("="*80)

        verified_count = 0
        wins = 0
        losses = 0

        for pick in picks_with_results:
            expert = pick['expert']
            bet = pick['pick']
            sport = pick['sport']
            result = pick.get('result', {})
            status = result.get('status', 'unknown')
            outcome = result.get('result', 'pending')
            notes = result.get('notes', '')

            print(f"\n👤 Expert: {expert}")
            print(f"🎯 Pick: {bet}")
            print(f"🏈 Sport: {sport}")
            print(f"📊 Status: {status}")

            if outcome:
                if outcome == 'win':
                    print(f"✅ Result: WIN")
                    wins += 1
                    verified_count += 1
                elif outcome == 'loss':
                    print(f"❌ Result: LOSS")
                    losses += 1
                    verified_count += 1
                else:
                    print(f"⏳ Result: {outcome}")
            else:
                print(f"⏳ Result: Pending")

            if notes:
                print(f"📝 {notes}")

        print(f"\n" + "="*80)
        print("📈 SUMMARY")
        print(f"Total Picks Analyzed: {len(picks_with_results)}")
        print(f"Verified Results: {verified_count}")
        print(f"Wins: {wins}")
        print(f"Losses: {losses}")

        if verified_count > 0:
            accuracy = (wins / verified_count) * 100
            print(f"Accuracy: {accuracy:.1f}%")

        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_picks': len(picks_with_results),
            'verified': verified_count,
            'wins': wins,
            'losses': losses,
            'accuracy': (wins / verified_count * 100) if verified_count > 0 else 0,
            'picks': picks_with_results
        }

    def run(self):
        """Run the real pick checker"""
        print("🔥 REAL EXPERT PICK CHECKER")
        print("Checking actual expert picks with real game results...")

        # Get real picks
        picks = self.get_real_picks()

        # Check results
        picks_with_results = self.check_real_pick_results(picks)

        # Generate report
        report = self.generate_real_report(picks_with_results)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_pick_report_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Report saved to: {filename}")

        return report

if __name__ == "__main__":
    checker = RealPickChecker()
    checker.run()