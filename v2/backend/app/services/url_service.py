from sqlalchemy.orm import Session
from app.models.models import ScrapedURL
from datetime import datetime

class URLService:
    def __init__(self, db: Session):
        self.db = db

    def refresh_url(self, url_id: int) -> bool:
        url = self.db.query(ScrapedURL).filter(ScrapedURL.id == url_id).first()
        if not url:
            return False
        # Simulate refresh: update last_scraped and status
        url.last_scraped = datetime.utcnow()
        url.status = 'refreshing'
        self.db.commit()
        return True

    def refresh_all_urls(self) -> int:
        urls = self.db.query(ScrapedURL).all()
        count = 0
        for url in urls:
            url.last_scraped = datetime.utcnow()
            url.status = 'refreshing'
            count += 1
        self.db.commit()
        return count
