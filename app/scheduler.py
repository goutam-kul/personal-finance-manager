import sys
import os 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from db.database import SessionLocal
from app.models import Budget

def reset_monthly_budget():
    """
    Reset the current total field of all budgets to 0 at the start of every month.
    """
    session = SessionLocal()
    try:
        # Reset current_total for all budgets
        session.query(Budget).update({Budget.current_total: 0})
        session.commit()
        print(f"Budgets reset at {datetime.now()}")
    except Exception as e:
        session.rollback()
        print(f"Error resetting budgets: {e}")
    finally:
        session.close()


def start_scheduler():
    """
    Start the APScheduler to run background tasks.
    """
    scheduler = BackgroundScheduler()
    # Schedule reste_monthly_budgets to run at midnight on the 1st of every month 
    scheduler.add_job(reset_monthly_budget, "cron", day=1, hour=0, minute=0)
    scheduler.start()
    print("Scheduler Started.")