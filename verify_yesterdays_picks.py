#!/usr/bin/env python3
"""
Verify Yesterday's Picks

Run this tomorrow to check the results of today's tracked picks
"""

import json
import os
from datetime import datetime, timedelta
from result_verifier import ResultVerifier

class YesterdayPickVerifier:
    def __init__(self):
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.verifier = ResultVerifier()

    def load_yesterdays_picks(self):
        """Load yesterday's tracked picks"""
        filename = f"daily_picks_{self.yesterday}.json"

        if not os.path.exists(filename):
            print(f"❌ No pick file found for {self.yesterday}")
            print(f"   Looking for: {filename}")
            return None

        with open(filename, 'r') as f:
            data = json.load(f)

        return data

    def verify_all_picks(self, pick_data):
        """Verify results for all yesterday's picks"""
        picks = pick_data['picks']
        verified_picks = []

        print(f"🔍 Checking {len(picks)} picks from {self.yesterday}...")
        print()

        for pick in picks:
            # Verify the result
            result = self.verifier.verify_pick_result(pick)
            pick['verification'] = result
            pick['verified_at'] = datetime.now().isoformat()

            # Only include picks that have actual win/loss results
            status = result.get('result', 'pending')
            if status in ['win', 'loss']:
                verified_picks.append(pick)
                print(f"✓ {pick['expert']} - {pick['pick']}")

                if status == 'win':
                    print(f"   ✅ WIN")
                elif status == 'loss':
                    print(f"   ❌ LOSS")

                if result.get('notes'):
                    print(f"   📝 {result['notes']}")
                print()

        if len(verified_picks) < len(picks):
            skipped = len(picks) - len(verified_picks)
            print(f"ℹ️  Skipped {skipped} picks that couldn't be verified (unsupported sports/bet types)")
            print()

        return verified_picks

    def generate_accuracy_report(self, verified_picks):
        """Generate expert accuracy report"""
        print("="*80)
        print(f"📊 EXPERT PICK ACCURACY REPORT - {self.yesterday}")
        print("="*80)

        # Calculate overall stats
        total_picks = len(verified_picks)
        wins = sum(1 for p in verified_picks if p.get('verification', {}).get('result') == 'win')
        losses = sum(1 for p in verified_picks if p.get('verification', {}).get('result') == 'loss')
        verified = wins + losses

        print(f"📈 OVERALL RESULTS:")
        print(f"   Total Picks Tracked: {total_picks}")
        print(f"   Results Verified: {verified}")
        print(f"   Wins: {wins}")
        print(f"   Losses: {losses}")

        if verified > 0:
            accuracy = (wins / verified) * 100
            print(f"   Overall Accuracy: {accuracy:.1f}%")

        print()

        # Expert breakdown
        experts = {}
        for pick in verified_picks:
            expert = pick['expert']
            if expert not in experts:
                experts[expert] = {'picks': [], 'wins': 0, 'losses': 0}

            experts[expert]['picks'].append(pick)

            verification = pick.get('verification', {})
            if verification.get('result') == 'win':
                experts[expert]['wins'] += 1
            elif verification.get('result') == 'loss':
                experts[expert]['losses'] += 1

        print("👥 EXPERT PERFORMANCE:")
        print("-" * 50)

        # Only show experts who have verified picks
        experts_with_results = {k: v for k, v in experts.items() if v['wins'] + v['losses'] > 0}

        if not experts_with_results:
            print("\nNo experts had verifiable picks for this date.")
            return

        for expert, data in experts_with_results.items():
            expert_wins = data['wins']
            expert_losses = data['losses']
            expert_verified = expert_wins + expert_losses
            expert_accuracy = (expert_wins / expert_verified) * 100

            print(f"\n🎯 {expert}")
            print(f"   Record: {expert_wins}-{expert_losses} ({expert_accuracy:.1f}%)")

            # Show individual verified picks only
            for pick in data['picks']:
                verification = pick.get('verification', {})
                result = verification.get('result', 'pending')

                if result in ['win', 'loss']:  # Only show verified picks
                    emoji = "✅" if result == 'win' else "❌"
                    sport_emoji = "⚽" if pick['sport'] == 'Soccer' else "⚾" if pick['sport'] == 'MLB' else "🏈"
                    print(f"   {emoji} {sport_emoji} {pick['pick']}")

        # Sport breakdown
        sports = {}
        for pick in verified_picks:
            sport = pick['sport']
            if sport not in sports:
                sports[sport] = {'total': 0, 'wins': 0, 'losses': 0}

            sports[sport]['total'] += 1

            verification = pick.get('verification', {})
            if verification.get('result') == 'win':
                sports[sport]['wins'] += 1
            elif verification.get('result') == 'loss':
                sports[sport]['losses'] += 1

        print(f"\n🏈 SPORT PERFORMANCE:")
        print("-" * 30)

        for sport, data in sports.items():
            verified_count = data['wins'] + data['losses']
            if verified_count > 0:
                sport_accuracy = (data['wins'] / verified_count) * 100
                print(f"{sport}: {data['wins']}-{data['losses']} ({sport_accuracy:.1f}%)")
            else:
                print(f"{sport}: No completed picks")

        return {
            'date': self.yesterday,
            'total_picks': total_picks,
            'verified': verified,
            'wins': wins,
            'losses': losses,
            'accuracy': (wins / verified * 100) if verified > 0 else 0,
            'experts': experts,
            'sports': sports,
            'picks': verified_picks
        }

    def save_results(self, report):
        """Save verification results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"verified_results_{self.yesterday}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        return filename

    def run(self):
        """Main verification function"""
        print("🔍 YESTERDAY'S PICK VERIFICATION")
        print("=" * 50)
        print(f"Verifying picks from {self.yesterday}...")
        print()

        # Load yesterday's picks
        pick_data = self.load_yesterdays_picks()

        if not pick_data:
            print("❌ No picks to verify")
            return

        print(f"📋 Loaded {pick_data['total_picks']} picks from {self.yesterday}")
        print()

        # Verify all picks
        verified_picks = self.verify_all_picks(pick_data)

        # Generate report
        report = self.generate_accuracy_report(verified_picks)

        # Save results
        filename = self.save_results(report)

        print(f"\n💾 Full results saved to: {filename}")
        print()
        print("🏆 VERIFICATION COMPLETE!")

        return report

if __name__ == "__main__":
    verifier = YesterdayPickVerifier()
    verifier.run()