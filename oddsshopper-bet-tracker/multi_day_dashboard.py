#!/usr/bin/env python3
"""
Multi-Day Expert Dashboard
Display verified picks from multiple experts across multiple days
"""

from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

def load_multi_day_verified_data():
    """Load the multi-day verified picks data and add additional expert examples"""
    try:
        with open('verified_multi_day_picks_20250919_111103.json', 'r') as f:
            data = json.load(f)
        verified_bets = data.get('verified_bets', [])

        # Only show real verified data from actual Oddshopper scraping
        # Filter to only show picks from the 7 requested experts (if any exist in real data)
        requested_experts = ['Eric Lindquist', 'Greg Ehrenberg', 'Ben Rasa', 'Sam Smith', 'Joseph Nardone', 'Jake Hari', 'Eytan Shander']

        # Filter verified bets to only include completed picks with real results
        completed_verified_bets = [
            bet for bet in verified_bets
            if bet.get('verification', {}).get('result') in ['win', 'loss']
        ]

        print(f"📊 Total real verified picks: {len(completed_verified_bets)}")
        print(f"🎯 Requested experts: {', '.join(requested_experts)}")

        # Check which requested experts appear in real data
        real_experts_found = set(bet.get('expert', '') for bet in completed_verified_bets)
        requested_experts_found = [expert for expert in requested_experts if expert in real_experts_found]

        if requested_experts_found:
            print(f"✅ Found real data for: {', '.join(requested_experts_found)}")
        else:
            print("⚠️  No real picks found for the 7 requested experts")
            print("📋 Showing all available real verified picks from Oddshopper")

        # Return only real verified data
        verified_bets = completed_verified_bets
        return verified_bets

    except FileNotFoundError:
        return []

def get_stats_from_multi_day_data(verified_bets):
    """Calculate comprehensive stats from multi-day verified data"""
    completed_bets = [
        bet for bet in verified_bets
        if bet.get('verification', {}).get('result') in ['win', 'loss']
    ]

    total_picks = len(completed_bets)
    wins = len([bet for bet in completed_bets if bet['verification']['result'] == 'win'])
    losses = len([bet for bet in completed_bets if bet['verification']['result'] == 'loss'])
    win_rate = (wins / total_picks * 100) if total_picks > 0 else 0

    # Expert breakdown with detailed stats - include ALL experts
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
                'picks': [],
                'verification_status': {}
            }

        experts[expert]['total'] += 1

        if result == 'win':
            experts[expert]['wins'] += 1
            experts[expert]['verified'] += 1
        elif result == 'loss':
            experts[expert]['losses'] += 1
            experts[expert]['verified'] += 1
        else:
            experts[expert]['unverified'] += 1
            # Track verification status reasons
            status = bet.get('verification', {}).get('status', 'unknown')
            if status not in experts[expert]['verification_status']:
                experts[expert]['verification_status'][status] = 0
            experts[expert]['verification_status'][status] += 1

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
    for bet in completed_bets:
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
def multi_day_dashboard():
    """Multi-day dashboard showing all verified experts"""
    verified_bets = load_multi_day_verified_data()
    stats = get_stats_from_multi_day_data(verified_bets)

    # Filter to only show completed bets (verified wins/losses only)
    completed_bets = [
        bet for bet in verified_bets
        if bet.get('verification', {}).get('result') in ['win', 'loss']
    ]

    # Update stats to only include experts with verified picks
    stats['experts'] = {
        expert: data for expert, data in stats['experts'].items()
        if data['verified'] > 0
    }

    # Sort picks by date (newest first)
    completed_bets.sort(key=lambda x: x.get('date', ''), reverse=True)

    # Format picks for display
    formatted_picks = []
    for bet in completed_bets:
        verification = bet.get('verification', {})
        structured_bet = bet.get('structured_bet', {})

        formatted_pick = {
            'expert': bet['expert'],
            'sport': bet['sport'],
            'bet_type': bet.get('bet_type', 'Unknown'),
            'pick_description': structured_bet.get('raw_text', bet.get('raw_pick_text', 'Unknown'))[:100],
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

@app.route('/api/multi-day-picks')
def api_multi_day_picks():
    """API endpoint for multi-day picks data"""
    verified_bets = load_multi_day_verified_data()
    stats = get_stats_from_multi_day_data(verified_bets)

    return jsonify({
        'picks': verified_bets,
        'stats': stats,
        'total_analyzed': len(verified_bets),
        'last_updated': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)