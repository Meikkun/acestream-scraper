from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import List, Optional
from datetime import datetime

from app.models.models import ScrapedURL

class URLRepository:
    """Repository for ScrapedURL operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ScrapedURL]:
        """Get all ScrapedURLs"""
        result = self.db.execute(select(ScrapedURL).offset(skip).limit(limit))
        return result.scalars().all()

    def get_by_id(self, url_id: int) -> Optional[ScrapedURL]:
        """Get a ScrapedURL by id"""
        result = self.db.execute(select(ScrapedURL).where(ScrapedURL.id == url_id))
        return result.scalar_one_or_none()

    def get_by_url(self, url: str) -> Optional[ScrapedURL]:
        """Get a ScrapedURL by url"""
        result = self.db.execute(select(ScrapedURL).where(ScrapedURL.url == url))
        return result.scalar_one_or_none()

    def get_by_type_and_url(self, url_type: str, url: str) -> Optional[ScrapedURL]:
        """Get a ScrapedURL by type and url"""
        result = self.db.execute(
            select(ScrapedURL).where(ScrapedURL.url_type == url_type, ScrapedURL.url == url)
        )
        return result.scalar_one_or_none()

    def get_or_create_by_type_and_url(
        self,
        url_type: str,
        url: str,
        trigger_scrape: bool = True
    ) -> ScrapedURL:
        """Get or create a ScrapedURL by type and url"""
        scraped_url = self.get_by_type_and_url(url_type, url)

        if scraped_url:
            return scraped_url

        # Create new ScrapedURL
        scraped_url = ScrapedURL(
            url=url,
            url_type=url_type,
            added_at=datetime.utcnow(),
            last_scraped=None
        )

        self.db.add(scraped_url)
        self.db.flush()
        self.db.commit()

        return scraped_url

    def add(self, scraped_url: ScrapedURL) -> ScrapedURL:
        """Add a new ScrapedURL"""
        self.db.add(scraped_url)
        self.db.flush()
        self.db.commit()
        return scraped_url

    def update(self, scraped_url: ScrapedURL) -> ScrapedURL:
        """Update an existing ScrapedURL"""
        self.db.add(scraped_url)
        self.db.commit()
        return scraped_url

    def delete(self, scraped_url: ScrapedURL) -> None:
        """Delete a ScrapedURL"""
        self.db.delete(scraped_url)
        self.db.commit()
