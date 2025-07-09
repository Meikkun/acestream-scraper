"""
Service for managing scraping operations
"""
from sqlalchemy.orm import Session
from typing import List, Tuple, Dict, Any, Optional
import logging

from app.models.models import ScrapedURL
from app.schemas.scraper import ChannelResult, URLResponse, URLCreate, URLUpdate
from app.scrapers import create_scraper_for_url

logger = logging.getLogger(__name__)


class ScraperService:
    """Service for managing scraping operations"""

    def __init__(self, db: Session):
        self.db = db

    async def scrape_url(self, url: str, url_type: str = 'auto') -> Tuple[List[ChannelResult], str]:
        """
        Scrape a URL for acestream channels

        Args:
            url: The URL to scrape
            url_type: The URL type ('auto', 'regular', 'zeronet')

        Returns:
            Tuple[List[ChannelResult], str]: Tuple of (channels, status)
        """
        logger.info(f"Scraping URL: {url} (type: {url_type})")

        try:
            scraper = create_scraper_for_url(url, url_type)
            raw_channels, status = await scraper.scrape()

            # Convert raw channels to ChannelResult objects
            channels = [
                ChannelResult(
                    channel_id=channel_id,
                    name=name,
                    metadata=metadata
                )
                for channel_id, name, metadata in raw_channels
            ]

            return channels, status

        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return [], f"Error: {str(e)}"

    def get_scraped_urls(self, skip: int = 0, limit: int = 100) -> List[URLResponse]:
        """Get list of URLs that have been scraped"""
        urls = self.db.query(ScrapedURL).offset(skip).limit(limit).all()
        return [URLResponse.model_validate(url) for url in urls]

    def get_scraped_url(self, url_id: int) -> Optional[URLResponse]:
        """Get a specific scraped URL by ID"""
        url = self.db.query(ScrapedURL).filter(ScrapedURL.id == url_id).first()
        return URLResponse.model_validate(url) if url else None

    def create_scraped_url(self, url_data: URLCreate) -> URLResponse:
        """Create a new scraped URL or update existing if duplicate"""
        # Check for existing URL
        url = self.db.query(ScrapedURL).filter(ScrapedURL.url == url_data.url).first()
        if url:
            # Update fields if duplicate
            url.url_type = url_data.url_type
            url.enabled = url_data.enabled
            url.status = url_data.status
            self.db.commit()
            self.db.refresh(url)
            return URLResponse.model_validate(url)
        # Create new if not exists
        url = ScrapedURL(
            url=url_data.url,
            url_type=url_data.url_type,
            enabled=url_data.enabled,
            status=url_data.status
        )
        self.db.add(url)
        self.db.commit()
        self.db.refresh(url)
        return URLResponse.model_validate(url)

    def update_scraped_url(self, url_id: int, url_data: URLUpdate) -> Optional[URLResponse]:
        """Update a scraped URL"""
        url = self.db.query(ScrapedURL).filter(ScrapedURL.id == url_id).first()
        if not url:
            return None

        update_data = url_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(url, field, value)

        self.db.commit()
        self.db.refresh(url)
        return URLResponse.model_validate(url)

    def delete_scraped_url(self, url_id: int) -> bool:
        """Delete a scraped URL"""
        url = self.db.query(ScrapedURL).filter(ScrapedURL.id == url_id).first()
        if not url:
            return False

        self.db.delete(url)
        self.db.commit()
        return True

    def get_enabled_urls(self) -> List[ScrapedURL]:
        """Get all enabled URLs"""
        return self.db.query(ScrapedURL).filter(ScrapedURL.enabled == True).all()
