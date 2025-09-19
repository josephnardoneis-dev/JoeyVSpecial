#!/usr/bin/env python3
"""
Verify Multi-Day Picks
Verify all picks from the multi-day scraping with enhanced verification system
"""

import json
from datetime import datetime
from real_verification_system import RealVerificationSystem
from real_pick_parser import RealPickParser

def main():
    """Verify all multi-day picks"""
    print("🚀 MULTI-DAY PICK VERIFICATION")
    print("="*50)

    # Load latest multi-day picks
    with open('multi_day_picks_20250919_111046.json', 'r') as f:
        data = json.load(f)

    picks = data.get('picks', [])
    print(f"📊 Total picks to verify: {len(picks)}")

    # Parse picks into structured bets
    parser = RealPickParser()
    verifier = RealVerificationSystem()

    all_verified_bets = []

    for i, pick in enumerate(picks, 1):
        print(f"\n[{i}/{len(picks)}] Processing pick from {pick['expert']} ({pick['sport']})")

        # Use the pick as-is since it's already structured
        bet = pick.copy()
        print(f"   🎯 Verifying: {bet.get('bet_type', 'Unknown')} bet")

        # Get the date for verification (use scraped_date or date)
        bet_date = bet.get('scraped_date') or bet.get('date', '2025-09-18')
        date_str = bet_date.replace('-', '')

        # Verify the bet
        verification = verifier.verify_bet(bet, date_str)

        # Add verification to bet
        bet['verification'] = verification
        bet['verified_at'] = datetime.now().isoformat()

        all_verified_bets.append(bet)

        # Show result
        status = verification.get('result')
        if status == 'win':
            print("      ✅ WIN")
        elif status == 'loss':
            print("      ❌ LOSS")
        else:
            print(f"      ⏳ {verification.get('status', 'Unknown')}")

        if verification.get('notes'):
            print(f"      📝 {verification['notes'][:80]}...")

    # Save verified results
    output_file = f'verified_multi_day_picks_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    with open(output_file, 'w') as f:
        json.dump({
            'verified_at': datetime.now().isoformat(),
            'total_bets': len(all_verified_bets),
            'date_range': data.get('date_range', 'Unknown'),
            'sports_focus': data.get('sports_focus', []),
            'verified_bets': all_verified_bets
        }, f, indent=2)

    print(f"\n💾 Verified results saved to: {output_file}")

    # Generate summary
    completed_bets = [b for b in all_verified_bets if b.get('verification', {}).get('result') in ['win', 'loss']]

    if completed_bets:
        wins = len([b for b in completed_bets if b['verification']['result'] == 'win'])
        losses = len([b for b in completed_bets if b['verification']['result'] == 'loss'])
        accuracy = (wins / len(completed_bets) * 100) if completed_bets else 0

        print(f"\n📈 VERIFICATION SUMMARY:")
        print(f"   Total verified: {len(completed_bets)}")
        print(f"   Wins: {wins}")
        print(f"   Losses: {losses}")
        print(f"   Accuracy: {accuracy:.1f}%")

        # Expert breakdown
        experts = {}
        for bet in completed_bets:
            expert = bet['expert']
            result = bet['verification']['result']

            if expert not in experts:
                experts[expert] = {'wins': 0, 'losses': 0}

            if result == 'win':
                experts[expert]['wins'] += 1
            else:
                experts[expert]['losses'] += 1

        print(f"\n👥 EXPERT PERFORMANCE:")
        for expert, data in experts.items():
            total = data['wins'] + data['losses']
            acc = (data['wins'] / total * 100) if total > 0 else 0
            print(f"   {expert}: {data['wins']}-{data['losses']} ({acc:.1f}%)")

    return output_file

if __name__ == "__main__":
    main()