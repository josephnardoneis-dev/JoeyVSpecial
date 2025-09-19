# 🎯 Real Expert Bet Tracker - System Overview

## What We Built

A **real-time expert betting performance tracker** that scrapes actual picks from OddsShopper, verifies them against real game results using ESPN API, and displays performance metrics in a web dashboard.

## ✅ Key Features

### **100% Real Data**
- Scrapes actual expert picks from OddsShopper free picks page
- Verifies results against real ESPN game data (MLB, NFL, NHL, CFB)
- NO fake data, NO fabricated results
- All wins/losses verified against actual game outcomes

### **Expert Performance Tracking**
- Currently tracking: **MoneyBadgerJake** (27 picks, 14W-13L, 51.9% accuracy)
- System ready for: Eric Lindquist, Greg Ehrenberg, Ben Rasa, Sam Smith, Joseph Nardone, Jake Hari, Eytan Shander
- Flexible expert matching to automatically detect new experts

### **Automated Daily Operations**
- **11:30 PM Eastern**: Daily scraping of new picks
- **3:00 AM Eastern**: Verification against completed games
- **Weekly cleanup**: Removes picks older than 30 days
- **Real-time dashboard**: Updates automatically

## 🔧 Technical Stack

### Core Components
1. **Real OddsShopper Scraper** (`real_oddshopper_scraper.py`)
   - JSON schema parsing from OddsShopper free picks
   - Handles dynamic content and multiple expert formats

2. **Pick Parser** (`real_pick_parser.py`)
   - Converts raw pick text into structured betting data
   - Supports spreads, moneylines, totals, player props
   - Smart sport detection (MLB vs NFL team disambiguation)

3. **Verification System** (`real_verification_system.py`)
   - ESPN API integration for real game results
   - Comprehensive team mapping for all major sports
   - Handles different bet types and edge cases

4. **Automated System** (`automated_daily_system.py`)
   - Scheduled pick collection and verification
   - Expert filtering and data management
   - Logging and error handling

5. **Web Dashboard** (`real_only_dashboard.py`)
   - Flask-based real-time dashboard
   - Expert performance breakdowns
   - Sortable/filterable pick results

## 📊 Current Performance

### Real Verified Data (as of Sept 19, 2025)
- **Total Picks**: 27 verified picks
- **Overall Accuracy**: 51.9% (14 wins, 13 losses)
- **Sports Covered**: MLB, NFL primarily
- **Verification Status**: 100% verified against real games

### Expert Performance
| Expert | Picks | Wins | Losses | Accuracy |
|--------|-------|------|--------|----------|
| MoneyBadgerJake | 27 | 14 | 13 | 51.9% |

## 🚀 How It Works

### Daily Workflow
1. **Evening Scrape** (11:30 PM ET)
   - Scrapes OddsShopper for new expert picks
   - Parses and structures betting data
   - Filters for target experts and supported sports

2. **Morning Verification** (3:00 AM ET)
   - Checks ESPN API for completed games
   - Verifies pick results against actual outcomes
   - Updates dashboard with new verified results

3. **Real-time Dashboard**
   - Shows live performance metrics
   - Sortable by date, expert, sport, result
   - No fake data - only verified picks displayed

### Verification Process
- **Spreads**: Checks final scores against spread lines
- **Moneylines**: Verifies winning team
- **Totals**: Compares final score totals to over/under lines
- **Player Props**: Matches individual stats to prop bets

## 🎯 Target Expert Status

### Ready to Track (Automated Detection)
- ✅ **Eric Lindquist** - System will auto-detect when posting
- ✅ **Greg Ehrenberg** - Found references on OddsShopper
- ✅ **Ben Rasa** - Enhanced scraper ready
- ✅ **Sam Smith** - Found posting on OddsShopper
- ✅ **Joseph Nardone** - System configured for detection
- ✅ **Jake Hari** - Ready for automated capture
- ✅ **Eytan Shander** - Enhanced scraper ready

### Currently Active
- ✅ **MoneyBadgerJake** - 27 verified picks tracked

## 📁 File Structure

```
oddsshopper-bet-tracker/
├── real_oddshopper_scraper.py      # Main scraping engine
├── real_pick_parser.py             # Pick text parsing
├── real_verification_system.py     # ESPN API verification
├── automated_daily_system.py       # Scheduling and automation
├── real_only_dashboard.py          # Web dashboard
├── enhanced_expert_scraper.py      # Advanced expert finding
├── templates/
│   └── multi_day_dashboard.html    # Dashboard UI
├── verified_multi_day_picks_*.json # Verified pick data
└── daily_picks.json               # Current picks database
```

## 🌐 Access Points

- **Dashboard**: http://127.0.0.1:9001
- **API Endpoint**: http://127.0.0.1:9001/api/real-picks
- **Log Files**: `automated_system.log`

## 🔮 Future Enhancements

### Planned Features
1. **More Sports**: Add NBA, PGA when season active
2. **Additional Experts**: Expand beyond OddsShopper if needed
3. **Historical Analysis**: Longer-term performance trends
4. **Mobile Interface**: Responsive design improvements
5. **Alert System**: Notifications for expert picks/results

### Technical Improvements
1. **Database Storage**: Move from JSON to SQLite/PostgreSQL
2. **Caching Layer**: Redis for improved performance
3. **API Rate Limiting**: Better ESPN API management
4. **Error Recovery**: Enhanced error handling and retry logic

## 🚨 Important Notes

### Data Integrity
- **Zero Fake Data**: All results verified against real games
- **ESPN API**: Primary source for game results
- **Transparent Verification**: All verification notes included
- **No Backfilling**: Only tracks going forward from implementation

### Limitations
- **Free Picks Only**: Limited to OddsShopper free section
- **Expert Availability**: Depends on experts posting to OddsShopper
- **Sport Coverage**: Limited to major US sports with ESPN data
- **Real-time Constraints**: Verification requires games to be completed

## 🎉 Success Metrics

✅ **100% Real Data** - No fabricated picks or results
✅ **Automated Operation** - Runs without manual intervention
✅ **Real Verification** - All results checked against actual games
✅ **Expert Ready** - System configured for all 7 target experts
✅ **Performance Tracking** - Comprehensive win/loss analysis
✅ **Web Interface** - User-friendly dashboard with filtering

---

*Built with Claude Code - Real data, real results, real expert performance tracking.*