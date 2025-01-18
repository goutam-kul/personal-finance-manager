import sys
import os 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from fastapi import FastAPI
from app.routes import router
from app.scheduler import start_scheduler

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(title="Personal Finance Manager")

# Include routes
app.include_router(router)

# Start the scheduler when the app starts
@app.on_event("startup")
def startup_event():
    logger.info("Starting the application...")
    try:
        start_scheduler()
        logger.info("Scheduler started successfully.")
    except Exception as e:
        logger.error(f"Failed to start the scheduler: {e}")


# Run the app if this script is executed directly 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6000)