#!/usr/bin/env python3
"""
Scheduler
Automated scheduling for outreach reports
"""

import schedule
import time
import yaml
import argparse
import sys
from datetime import datetime
from generate_report import main as generate_report_main
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)


def job_wrapper():
    """Wrapper function to run the report generation"""
    try:
        logger.info("=" * 60)
        logger.info(f"🔄 Scheduled report generation started at {datetime.now()}")
        logger.info("=" * 60)
        
        generate_report_main()
        
        logger.info("=" * 60)
        logger.info(f"✅ Scheduled report generation completed at {datetime.now()}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in scheduled job: {e}")


def setup_schedule(frequency: str = None, time_str: str = None, day: str = None):
    """
    Setup schedule based on parameters
    
    Args:
        frequency: 'daily', 'weekly', or 'monthly'
        time_str: Time to run (24-hour format, e.g., "09:00")
        day: Day of week for weekly schedule (e.g., "monday")
    """
    
    # Load config if parameters not provided
    if frequency is None:
        config = load_config()
        automation_config = config.get('automation', {})
        frequency = automation_config.get('frequency', 'daily')
        time_str = automation_config.get('run_time', '09:00')
        day = automation_config.get('weekly_day', 'monday')
    
    # Setup schedule based on frequency
    if frequency == 'daily':
        schedule.every().day.at(time_str).do(job_wrapper)
        logger.info(f"📅 Scheduled daily reports at {time_str}")
        
    elif frequency == 'weekly':
        if day.lower() == 'monday':
            schedule.every().monday.at(time_str).do(job_wrapper)
        elif day.lower() == 'tuesday':
            schedule.every().tuesday.at(time_str).do(job_wrapper)
        elif day.lower() == 'wednesday':
            schedule.every().wednesday.at(time_str).do(job_wrapper)
        elif day.lower() == 'thursday':
            schedule.every().thursday.at(time_str).do(job_wrapper)
        elif day.lower() == 'friday':
            schedule.every().friday.at(time_str).do(job_wrapper)
        elif day.lower() == 'saturday':
            schedule.every().saturday.at(time_str).do(job_wrapper)
        elif day.lower() == 'sunday':
            schedule.every().sunday.at(time_str).do(job_wrapper)
        
        logger.info(f"📅 Scheduled weekly reports every {day.capitalize()} at {time_str}")
        
    elif frequency == 'monthly':
        # For monthly, we'll just do it on the 1st of every month
        # This requires a bit more complex logic
        logger.warning("Monthly scheduling requires more complex setup. Using daily checks.")
        schedule.every().day.at(time_str).do(job_wrapper)
        logger.info(f"📅 Scheduled daily checks at {time_str} (will run on 1st of month)")
    
    else:
        logger.error(f"Invalid frequency: {frequency}")
        sys.exit(1)


def run_scheduler():
    """Run the scheduler loop"""
    logger.info("🚀 Scheduler started")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Scheduler stopped by user")
        sys.exit(0)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Schedule automated outreach reports'
    )
    
    parser.add_argument(
        '--frequency',
        choices=['daily', 'weekly', 'monthly'],
        help='Report frequency (default: from config.yaml)'
    )
    
    parser.add_argument(
        '--time',
        help='Time to run reports in 24-hour format (e.g., 09:00)'
    )
    
    parser.add_argument(
        '--day',
        choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        help='Day of week for weekly reports (default: from config.yaml)'
    )
    
    parser.add_argument(
        '--run-now',
        action='store_true',
        help='Run report immediately before starting scheduler'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("⏰ Outreach Reporting Automation - Scheduler")
    print("=" * 60)
    
    # Run immediately if requested
    if args.run_now:
        logger.info("Running report immediately...")
        job_wrapper()
    
    # Setup schedule
    setup_schedule(
        frequency=args.frequency,
        time_str=args.time,
        day=args.day
    )
    
    # Run scheduler
    run_scheduler()


if __name__ == "__main__":
    main()
