"""
Periodic task for scraping URLs.
"""
from app.config.database import SessionLocal
from app.services.scraper_service import ScraperService
import logging
import asyncio


def run_url_scraping_task():
    db = SessionLocal()
    try:
        service = ScraperService(db)
        enabled_urls = service.get_enabled_urls()
        logger = logging.getLogger("url_scraping_task")
        logger.info(f"Starting URL scraping task for {len(enabled_urls)} URLs.")
        async def scrape_all():
            for url_obj in enabled_urls:
                channels, status = await service.scrape_url(url_obj.url, url_obj.url_type)
                logger.info(f"Scraped {url_obj.url} (type: {url_obj.url_type}): {status}, channels found: {len(channels)}")
        asyncio.run(scrape_all())
    except Exception as e:
        logging.getLogger("url_scraping_task").error(f"URL scraping task failed: {e}")
    finally:
        db.close()
