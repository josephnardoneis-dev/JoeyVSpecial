#!/usr/bin/env python3
"""
Real Dashboard using actual verified picks
"""

from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

def load_real_verified_data():
    """Load the real verified picks data"""
    try:
        with open('verified_results_real_2025-09-18.json', 'r') as f:
            data = json.load(f)
        return data.get('verified_bets', [])
    except FileNotFoundError:
        return []

def get_stats_from_verified_data(verified_bets):
    """Calculate stats from verified data"""
    completed_bets = [
        bet for bet in verified_bets
        if bet.get('verification', {}).get('result') in ['win', 'loss']
    ]

    total_picks = len(completed_bets)
    wins = len([bet for bet in completed_bets if bet['verification']['result'] == 'win'])
    losses = len([bet for bet in completed_bets if bet['verification']['result'] == 'loss'])
    win_rate = (wins / total_picks * 100) if total_picks > 0 else 0

    # Expert breakdown
    experts = {}
    for bet in completed_bets:
        expert = bet['expert']
        result = bet['verification']['result']

        if expert not in experts:
            experts[expert] = {'wins': 0, 'losses': 0, 'total': 0}

        if result == 'win':
            experts[expert]['wins'] += 1
        else:
            experts[expert]['losses'] += 1
        experts[expert]['total'] += 1

    # Add accuracy to each expert
    for expert_data in experts.values():
        if expert_data['total'] > 0:
            expert_data['accuracy'] = (expert_data['wins'] / expert_data['total'] * 100)
        else:
            expert_data['accuracy'] = 0

    return {
        'total_picks': total_picks,
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate, 1),
        'experts': experts
    }

@app.route('/')
def real_dashboard():
    """Dashboard showing real verified picks"""
    verified_bets = load_real_verified_data()
    stats = get_stats_from_verified_data(verified_bets)

    # Filter to only show completed bets
    completed_bets = [
        bet for bet in verified_bets
        if bet.get('verification', {}).get('result') in ['win', 'loss']
    ]

    # Format picks for display
    formatted_picks = []
    for bet in completed_bets:
        verification = bet.get('verification', {})
        structured_bet = bet.get('structured_bet', {})

        formatted_pick = {
            'expert': bet['expert'],
            'sport': bet['sport'],
            'pick_description': structured_bet.get('raw_text', bet.get('raw_pick_text', 'Unknown'))[:100],
            'result': verification.get('result'),
            'notes': verification.get('notes', ''),
            'bet_type': bet.get('bet_type'),
            'date': bet.get('date')
        }
        formatted_picks.append(formatted_pick)

    return render_template('real_dashboard.html', picks=formatted_picks, stats=stats)

@app.route('/api/real-picks')
def api_real_picks():
    """API endpoint for real picks data"""
    verified_bets = load_real_verified_data()
    stats = get_stats_from_verified_data(verified_bets)

    return jsonify({
        'picks': verified_bets,
        'stats': stats,
        'last_updated': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9000, debug=True)