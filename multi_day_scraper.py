#!/usr/bin/env python3
"""
Multi-Day Scraper for Expert Picks

Scrape multiple days to get more expert pick data
"""

import json
from datetime import datetime, timedelta
from real_oddshopper_scraper import OddshopperScraper
from real_pick_parser import RealPickParser
import time

class MultiDayScraper:
    def __init__(self):
        self.scraper = OddshopperScraper()
        self.parser = RealPickParser()

    def scrape_date_range(self, start_date: datetime, num_days: int):
        """Scrape picks for multiple days"""
        all_picks = []

        print(f"🚀 Scraping picks for {num_days} days starting from {start_date.strftime('%Y-%m-%d')}")

        for i in range(num_days):
            target_date = start_date - timedelta(days=i)
            date_str = target_date.strftime('%Y-%m-%d')

            print(f"\n📅 Scraping {date_str}...")

            # Use the existing scraper but for specific dates
            picks = self.scraper.get_picks_for_date(target_date)

            if picks:
                print(f"   ✅ Found {len(picks)} picks")

                # Save raw picks for this date
                filename = f"real_picks_{date_str}.json"
                self.scraper.save_picks_to_file(picks, date_str)

                # Parse the picks
                parsed_picks = []
                for pick in picks:
                    parsed_bets = self.parser.parse_pick(pick)
                    parsed_picks.extend(parsed_bets)

                # Filter for MLB, NFL, CFB, NHL
                sports_filter = ['MLB', 'NFL', 'College Football', 'Hockey']
                filtered_picks = [
                    pick for pick in parsed_picks
                    if pick['sport'] in sports_filter
                ]

                print(f"   📊 Parsed {len(filtered_picks)} MLB/NFL/CFB/NHL picks")

                # Add to master list
                for pick in filtered_picks:
                    pick['scraped_date'] = date_str
                    all_picks.append(pick)

            else:
                print(f"   ❌ No picks found for {date_str}")

            # Be nice to the server
            time.sleep(2)

        return all_picks

    def get_expert_summary(self, all_picks):
        """Get summary of experts and their pick counts"""
        experts = {}

        for pick in all_picks:
            expert = pick['expert']
            sport = pick['sport']

            if expert not in experts:
                experts[expert] = {
                    'total_picks': 0,
                    'sports': {},
                    'dates': set()
                }

            experts[expert]['total_picks'] += 1
            experts[expert]['sports'][sport] = experts[expert]['sports'].get(sport, 0) + 1
            experts[expert]['dates'].add(pick['scraped_date'])

        # Convert sets to lists for JSON serialization
        for expert_data in experts.values():
            expert_data['dates'] = list(expert_data['dates'])

        return experts

    def save_multi_day_data(self, all_picks, expert_summary):
        """Save consolidated multi-day data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save all picks
        picks_filename = f"multi_day_picks_{timestamp}.json"
        with open(picks_filename, 'w') as f:
            json.dump({
                'scraped_at': datetime.now().isoformat(),
                'total_picks': len(all_picks),
                'date_range': f"{min(pick['scraped_date'] for pick in all_picks)} to {max(pick['scraped_date'] for pick in all_picks)}",
                'sports_focus': ['MLB', 'NFL', 'College Football', 'Hockey'],
                'picks': all_picks
            }, f, indent=2)

        # Save expert summary
        summary_filename = f"expert_summary_{timestamp}.json"
        with open(summary_filename, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_experts': len(expert_summary),
                'experts': expert_summary
            }, f, indent=2)

        return picks_filename, summary_filename

def main():
    """Main scraping function"""
    scraper = MultiDayScraper()

    # Scrape last 7 days to get more experts
    start_date = datetime.now() - timedelta(days=1)  # Start from yesterday
    num_days = 7

    print("🎯 Multi-Day Expert Pick Scraper")
    print("=" * 50)
    print("Focusing on: MLB, NFL, College Football, NHL")
    print(f"Scraping {num_days} days of data...")

    # Scrape multiple days
    all_picks = scraper.scrape_date_range(start_date, num_days)

    # Get expert summary
    expert_summary = scraper.get_expert_summary(all_picks)

    # Save data
    picks_file, summary_file = scraper.save_multi_day_data(all_picks, expert_summary)

    # Display results
    print(f"\n🎉 SCRAPING COMPLETE!")
    print("=" * 50)
    print(f"📊 Total picks collected: {len(all_picks)}")
    print(f"👥 Total experts found: {len(expert_summary)}")
    print(f"💾 Data saved to: {picks_file}")
    print(f"📋 Summary saved to: {summary_file}")

    print(f"\n🏆 TOP EXPERTS BY PICK COUNT:")
    sorted_experts = sorted(expert_summary.items(), key=lambda x: x[1]['total_picks'], reverse=True)

    for expert, data in sorted_experts[:10]:  # Top 10
        sports_list = ', '.join([f"{sport}({count})" for sport, count in data['sports'].items()])
        print(f"   {expert}: {data['total_picks']} picks - {sports_list}")

    return all_picks, expert_summary

if __name__ == "__main__":
    main()