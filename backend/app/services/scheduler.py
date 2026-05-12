from apscheduler.schedulers.asyncio import AsyncIOScheduler
import structlog

logger = structlog.get_logger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()

def start_scheduler():
    """
    Start the APScheduler instance.
    This can be used to schedule background tasks periodically.
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("scheduler_started")

def stop_scheduler():
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("scheduler_stopped")
