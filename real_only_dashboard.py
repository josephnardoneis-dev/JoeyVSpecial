#!/usr/bin/env python3
"""
Real Only Dashboard
Display only actual verified picks from Oddshopper scraping - no fake data
"""

from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

def load_real_verified_data():
    """Load only real verified picks from Oddshopper scraping"""
    try:
        with open('verified_multi_day_picks_20250919_111103.json', 'r') as f:
            data = json.load(f)
        verified_bets = data.get('verified_bets', [])

        # Filter to only include completed picks with real win/loss results
        completed_verified_bets = [
            bet for bet in verified_bets
            if bet.get('verification', {}).get('result') in ['win', 'loss']
        ]

        print(f"📊 Total real verified picks found: {len(completed_verified_bets)}")

        # Show which experts we actually have data for
        experts_found = set(bet.get('expert', 'Unknown') for bet in completed_verified_bets)
        print(f"🎯 Real experts found: {', '.join(sorted(experts_found))}")

        # Target experts we're looking for
        target_experts = ['Eric Lindquist', 'Greg Ehrenberg', 'Ben Rasa', 'Sam Smith', 'Joseph Nardone', 'Jake Hari', 'Eytan Shander']
        found_targets = [expert for expert in target_experts if any(expert.lower() in found.lower() for found in experts_found)]

        print(f"✅ Target experts found: {', '.join(found_targets) if found_targets else 'None from target list'}")
        print(f"⏳ Target experts still searching for: {', '.join([e for e in target_experts if e not in found_targets])}")

        return completed_verified_bets

    except FileNotFoundError:
        print("❌ No verified data file found")
        return []

def get_stats_from_real_data(verified_bets):
    """Calculate stats from only real verified data"""
    total_picks = len(verified_bets)
    wins = len([bet for bet in verified_bets if bet['verification']['result'] == 'win'])
    losses = len([bet for bet in verified_bets if bet['verification']['result'] == 'loss'])
    win_rate = (wins / total_picks * 100) if total_picks > 0 else 0

    # Expert breakdown
    experts = {}
    for bet in verified_bets:
        expert = bet['expert']
        result = bet['verification']['result']
        sport = bet.get('sport', 'Unknown')
        bet_type = bet.get('bet_type', 'Unknown')

        if expert not in experts:
            experts[expert] = {
                'wins': 0,
                'losses': 0,
                'total': 0,
                'verified': 0,
                'unverified': 0,
                'sports': {},
                'bet_types': {},
                'picks': []
            }

        experts[expert]['total'] += 1
        experts[expert]['verified'] += 1  # All our picks are verified since we filtered for verified only

        if result == 'win':
            experts[expert]['wins'] += 1
        else:
            experts[expert]['losses'] += 1

        # Track by sport
        if sport not in experts[expert]['sports']:
            experts[expert]['sports'][sport] = {'wins': 0, 'losses': 0}
        if result == 'win':
            experts[expert]['sports'][sport]['wins'] += 1
        else:
            experts[expert]['sports'][sport]['losses'] += 1

        # Track by bet type
        if bet_type not in experts[expert]['bet_types']:
            experts[expert]['bet_types'][bet_type] = {'wins': 0, 'losses': 0}
        if result == 'win':
            experts[expert]['bet_types'][bet_type]['wins'] += 1
        else:
            experts[expert]['bet_types'][bet_type]['losses'] += 1

        experts[expert]['picks'].append(bet)

    # Add accuracy to each expert
    for expert_data in experts.values():
        if expert_data['total'] > 0:
            expert_data['accuracy'] = (expert_data['wins'] / expert_data['total'] * 100)
        else:
            expert_data['accuracy'] = 0

    # Sport breakdown
    sports_summary = {}
    for bet in verified_bets:
        sport = bet.get('sport', 'Unknown')
        result = bet['verification']['result']

        if sport not in sports_summary:
            sports_summary[sport] = {'wins': 0, 'losses': 0, 'total': 0}

        if result == 'win':
            sports_summary[sport]['wins'] += 1
        else:
            sports_summary[sport]['losses'] += 1
        sports_summary[sport]['total'] += 1

    return {
        'total_picks': total_picks,
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate, 1),
        'experts': experts,
        'sports_summary': sports_summary
    }

@app.route('/')
def real_only_dashboard():
    """Dashboard showing only real verified picks"""
    verified_bets = load_real_verified_data()
    stats = get_stats_from_real_data(verified_bets)

    # Sort picks by date (newest first)
    verified_bets.sort(key=lambda x: x.get('date', ''), reverse=True)

    # Format picks for display
    formatted_picks = []
    for bet in verified_bets:
        verification = bet.get('verification', {})
        structured_bet = bet.get('structured_bet', {})

        # Get a better description from the pick
        description = structured_bet.get('raw_text', '')
        if not description and bet.get('raw_pick_text'):
            description = bet['raw_pick_text'][:100]
        if not description:
            description = f"{bet.get('sport', 'Unknown')} bet"

        formatted_pick = {
            'expert': bet['expert'],
            'sport': bet['sport'],
            'bet_type': bet.get('bet_type', 'Unknown'),
            'pick_description': description,
            'result': verification.get('result'),
            'notes': verification.get('notes', ''),
            'date': bet.get('date', 'Unknown'),
            'verification_status': verification.get('status', 'unknown')
        }
        formatted_picks.append(formatted_pick)

    return render_template('multi_day_dashboard.html',
                         picks=formatted_picks,
                         stats=stats,
                         total_bets=len(verified_bets))

@app.route('/api/real-picks')
def api_real_picks():
    """API endpoint for real picks data"""
    verified_bets = load_real_verified_data()
    stats = get_stats_from_real_data(verified_bets)

    return jsonify({
        'picks': verified_bets,
        'stats': stats,
        'total_analyzed': len(verified_bets),
        'last_updated': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Print debug info on startup
    print("🚀 Starting Real Only Dashboard")
    verified_bets = load_real_verified_data()
    stats = get_stats_from_real_data(verified_bets)

    print(f"📈 Dashboard Statistics:")
    print(f"   Total verified picks: {stats['total_picks']}")
    print(f"   Wins: {stats['wins']}")
    print(f"   Losses: {stats['losses']}")
    print(f"   Win rate: {stats['win_rate']}%")
    print(f"   Experts: {len(stats['experts'])}")

    app.run(host='127.0.0.1', port=9001, debug=True)