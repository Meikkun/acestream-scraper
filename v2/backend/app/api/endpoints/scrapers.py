"""
API endpoints for scraper management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.config.database import get_db
from app.schemas.scraper import ScraperRequest, ScraperResult, URLResponse, URLCreate, URLUpdate
from app.services.scraper_service import ScraperService
from app.models.models import ScrapedURL

router = APIRouter()


class ScraperResultExtended(ScraperResult):
    channels_found: int
    status: str


@router.post("/scrape", response_model=ScraperResultExtended)
async def scrape_url(
    request: ScraperRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Scrape a URL for Acestream channels.

    Request body:
    - url: The URL to scrape
    - url_type: (Optional) URL type ('auto', 'regular', 'zeronet')
    - run_async: (Optional) Run scraping in background
    """
    scraper_service = ScraperService(db)
    # Basic validation for invalid URLs
    if not request.url or not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Scraping failed: invalid URL")
    try:
        if request.run_async:
            # Run in background
            background_tasks.add_task(
                scraper_service.scrape_url,
                request.url,
                request.url_type
            )
            return ScraperResultExtended(
                message="Scraping started in background",
                channels=[],
                url=request.url,
                channels_found=0,
                status="pending"
            )
        else:
            # Run synchronously
            channels, status_msg = await scraper_service.scrape_url(request.url, request.url_type)

            return ScraperResultExtended(
                message="Scraping completed successfully" if status_msg == "OK" else status_msg,
                channels=channels,
                url=request.url,
                channels_found=len(channels),
                status=status_msg
            )
    except Exception as e:
        return ScraperResultExtended(
            message=f"Scraping failed: {str(e)}",
            channels=[],
            url=request.url,
            channels_found=0,
            status=f"error: {str(e)}"
        )


@router.get("/urls", response_model=List[URLResponse])
async def get_scraped_urls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get list of URLs that have been scraped.
    """
    scraper_service = ScraperService(db)
    return scraper_service.get_scraped_urls(skip=skip, limit=limit)


@router.post("/urls", response_model=URLResponse, status_code=201)
async def create_scraped_url(
    url_data: URLCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new URL to be scraped.
    """
    scraper_service = ScraperService(db)
    # Validate required fields
    if not url_data.url or not url_data.url_type:
        raise HTTPException(status_code=422, detail="Missing required fields: url and url_type")
    return scraper_service.create_scraped_url(url_data)


@router.get("/urls/{url_id}", response_model=URLResponse)
async def get_scraped_url(
    url_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific scraped URL by ID.
    """
    scraper_service = ScraperService(db)
    url = scraper_service.get_scraped_url(url_id)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return url


@router.patch("/urls/{url_id}", response_model=URLResponse)
async def update_scraped_url(
    url_id: int,
    url_data: URLUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a scraped URL.
    """
    scraper_service = ScraperService(db)
    url = scraper_service.update_scraped_url(url_id, url_data)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return url


@router.delete("/urls/{url_id}", status_code=204)
async def delete_scraped_url(
    url_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a scraped URL.
    """
    scraper_service = ScraperService(db)
    success = scraper_service.delete_scraped_url(url_id)
    if not success:
        raise HTTPException(status_code=404, detail="URL not found")
    return


@router.post("/urls/{url_id}/scrape", response_model=ScraperResultExtended)
async def scrape_specific_url(
    url_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Scrape a specific URL by ID.
    """
    scraper_service = ScraperService(db)
    url = scraper_service.get_scraped_url(url_id)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    # Check if URL is enabled
    db_url = db.query(ScrapedURL).filter(ScrapedURL.id == url_id).first()
    if db_url and not db_url.enabled:
        raise HTTPException(status_code=400, detail="URL is disabled")
    background_tasks.add_task(
        scraper_service.scrape_url,
        url.url,
        url.url_type
    )
    return ScraperResultExtended(
        message="Scraping started in background",
        channels=[],
        url=url.url,
        channels_found=0,
        status="pending"
    )


@router.post("/urls/scrape_all", response_model=List[ScraperResultExtended])
async def scrape_all_urls(
    background_tasks: BackgroundTasks,
    limit: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Scrape all enabled URLs, with optional limit.
    """
    scraper_service = ScraperService(db)
    urls = scraper_service.get_enabled_urls()
    if limit is not None:
        urls = urls[:limit]
    results = []
    for url in urls:
        background_tasks.add_task(
            scraper_service.scrape_url,
            url.url,
            url.url_type
        )
        results.append(ScraperResultExtended(
            message="Scraping started in background",
            channels=[],
            url=url.url,
            channels_found=0,
            status="pending"
        ))
    return results
