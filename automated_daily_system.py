#!/usr/bin/env python3
"""
Automated Daily Bet Collection and Verification System

Automatically:
1. Scrape new picks daily at midnight Eastern
2. Verify completed picks at 3 AM Eastern with real game results
3. Update dashboard with latest data
"""

import schedule
import time
import json
import logging
from datetime import datetime, timedelta
import pytz
from real_oddshopper_scraper import OddshopperScraper
from real_pick_parser import RealPickParser
from real_verification_system import RealVerificationSystem

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_system.log'),
        logging.StreamHandler()
    ]
)

class AutomatedBettingSystem:
    def __init__(self):
        self.scraper = OddshopperScraper()
        self.parser = RealPickParser()
        self.verifier = RealVerificationSystem()
        self.eastern = pytz.timezone('US/Eastern')

        # Current data files
        self.daily_picks_file = 'daily_picks.json'
        self.verified_picks_file = 'verified_daily_picks.json'
        self.dashboard_data_file = 'dashboard_data.json'

    def scrape_daily_picks(self):
        """Scrape new picks for today and add to running database"""
        try:
            current_time = datetime.now(self.eastern)
            date_str = current_time.strftime('%Y-%m-%d')

            logging.info(f"🚀 Starting daily pick scraping for {date_str}")

            # Get today's picks
            picks = self.scraper.get_picks_for_date(current_time)

            if not picks:
                logging.warning(f"No picks found for {date_str}")
                return

            logging.info(f"📊 Found {len(picks)} raw picks for {date_str}")

            # Parse picks into structured format
            parsed_picks = []
            for pick in picks:
                structured_bets = self.parser.parse_pick(pick)
                for bet in structured_bets:
                    bet['scraped_date'] = date_str
                    bet['scraped_time'] = current_time.isoformat()
                    bet['verification_status'] = 'pending'
                    parsed_picks.append(bet)

            # Filter for supported sports and target experts
            sports_filter = ['MLB', 'NFL', 'College Football', 'Hockey', 'NBA', 'PGA']
            target_experts = [
                'MoneyBadgerJake', 'JoshEngleman', 'Sam Smith', 'Eric Lindquist',
                'Greg Ehrenberg', 'Ben Rasa', 'Joseph Nardone', 'Jake Hari', 'Eytan Shander'
            ]

            filtered_picks = []
            for pick in parsed_picks:
                # Check sport filter
                if pick['sport'] not in sports_filter:
                    continue

                # Check if expert is in our target list (flexible matching)
                expert_name = pick.get('expert', '')
                is_target_expert = False

                for target in target_experts:
                    if target.lower() in expert_name.lower() or expert_name.lower() in target.lower():
                        pick['expert'] = target  # Normalize the expert name
                        is_target_expert = True
                        break

                if is_target_expert:
                    filtered_picks.append(pick)

            logging.info(f"📈 Parsed {len(filtered_picks)} structured bets for tracking")

            # Load existing daily picks database
            daily_data = self.load_daily_picks_database()

            # Add new picks to database
            daily_data['picks'].extend(filtered_picks)
            daily_data['last_updated'] = current_time.isoformat()
            daily_data['total_picks'] = len(daily_data['picks'])

            # Save updated database
            self.save_daily_picks_database(daily_data)

            # Update dashboard data
            self.update_dashboard_data()

            logging.info(f"✅ Successfully added {len(filtered_picks)} picks to daily database")

        except Exception as e:
            logging.error(f"❌ Error in daily pick scraping: {e}")

    def verify_pending_picks(self):
        """Verify all pending picks at 3 AM Eastern"""
        try:
            current_time = datetime.now(self.eastern)
            logging.info(f"🔍 Starting verification process at {current_time}")

            # Load daily picks database
            daily_data = self.load_daily_picks_database()
            pending_picks = [
                pick for pick in daily_data['picks']
                if pick.get('verification_status') == 'pending'
            ]

            if not pending_picks:
                logging.info("No pending picks to verify")
                return

            logging.info(f"🎯 Verifying {len(pending_picks)} pending picks")

            verified_count = 0
            for pick in pending_picks:
                try:
                    # Get the game date for verification
                    pick_date = pick.get('date', pick.get('scraped_date', '2025-09-18'))
                    date_str = pick_date.replace('-', '')

                    # Verify the bet
                    verification = self.verifier.verify_bet(pick, date_str)

                    # Update pick with verification results
                    pick['verification'] = verification
                    pick['verified_at'] = current_time.isoformat()
                    pick['verification_status'] = 'completed'

                    # Log verification result
                    result = verification.get('result')
                    if result in ['win', 'loss']:
                        verified_count += 1
                        logging.info(f"✅ Verified: {pick['expert']} - {result.upper()}")
                    else:
                        logging.info(f"⏳ Could not verify: {pick['expert']} - {verification.get('status')}")

                except Exception as e:
                    logging.error(f"❌ Error verifying pick from {pick.get('expert', 'Unknown')}: {e}")
                    pick['verification_status'] = 'error'
                    pick['verification_error'] = str(e)

            # Save updated database
            daily_data['last_verified'] = current_time.isoformat()
            self.save_daily_picks_database(daily_data)

            # Update dashboard data
            self.update_dashboard_data()

            logging.info(f"🎉 Verification complete: {verified_count} picks verified with results")

        except Exception as e:
            logging.error(f"❌ Error in verification process: {e}")

    def load_daily_picks_database(self):
        """Load the daily picks database"""
        try:
            with open(self.daily_picks_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create new database structure
            return {
                'created_at': datetime.now(self.eastern).isoformat(),
                'picks': [],
                'total_picks': 0,
                'last_updated': None,
                'last_verified': None
            }

    def save_daily_picks_database(self, data):
        """Save the daily picks database"""
        with open(self.daily_picks_file, 'w') as f:
            json.dump(data, f, indent=2)

    def update_dashboard_data(self):
        """Update dashboard data file for the web interface"""
        try:
            daily_data = self.load_daily_picks_database()

            # Get completed picks for dashboard
            completed_picks = [
                pick for pick in daily_data['picks']
                if pick.get('verification_status') == 'completed' and
                pick.get('verification', {}).get('result') in ['win', 'loss']
            ]

            # Add Greg Ehrenberg and update dashboard data
            dashboard_data = {
                'generated_at': datetime.now(self.eastern).isoformat(),
                'total_picks_collected': daily_data['total_picks'],
                'verified_picks': len(completed_picks),
                'pending_verification': len([p for p in daily_data['picks'] if p.get('verification_status') == 'pending']),
                'last_updated': daily_data.get('last_updated'),
                'last_verified': daily_data.get('last_verified'),
                'verified_bets': completed_picks
            }

            with open(self.dashboard_data_file, 'w') as f:
                json.dump(dashboard_data, f, indent=2)

            logging.info(f"📊 Dashboard updated: {len(completed_picks)} verified picks available")

        except Exception as e:
            logging.error(f"❌ Error updating dashboard data: {e}")

    def cleanup_old_picks(self):
        """Remove picks older than 30 days to keep database manageable"""
        try:
            daily_data = self.load_daily_picks_database()
            cutoff_date = datetime.now(self.eastern) - timedelta(days=30)

            original_count = len(daily_data['picks'])
            daily_data['picks'] = [
                pick for pick in daily_data['picks']
                if datetime.fromisoformat(pick.get('scraped_time', '2025-09-18T00:00:00')) > cutoff_date
            ]

            removed_count = original_count - len(daily_data['picks'])
            if removed_count > 0:
                daily_data['total_picks'] = len(daily_data['picks'])
                self.save_daily_picks_database(daily_data)
                logging.info(f"🧹 Cleaned up {removed_count} old picks")

        except Exception as e:
            logging.error(f"❌ Error in cleanup: {e}")

def run_automated_system():
    """Set up and run the automated scheduling system"""
    system = AutomatedBettingSystem()

    # Schedule daily pick collection at 11:30 PM Eastern (to catch all daily picks)
    schedule.every().day.at("23:30").do(system.scrape_daily_picks)

    # Schedule verification at 3:00 AM Eastern (after games are complete)
    schedule.every().day.at("03:00").do(system.verify_pending_picks)

    # Schedule weekly cleanup on Sundays at 4:00 AM Eastern
    schedule.every().sunday.at("04:00").do(system.cleanup_old_picks)

    logging.info("🤖 Automated betting system started")
    logging.info("📅 Daily scraping scheduled: 11:30 PM Eastern")
    logging.info("🔍 Daily verification scheduled: 3:00 AM Eastern")
    logging.info("🧹 Weekly cleanup scheduled: Sundays 4:00 AM Eastern")

    # Run initial update if database is empty
    daily_data = system.load_daily_picks_database()
    if daily_data['total_picks'] == 0:
        logging.info("🚀 Running initial pick collection...")
        system.scrape_daily_picks()

    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    run_automated_system()