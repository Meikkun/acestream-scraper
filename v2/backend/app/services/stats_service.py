from sqlalchemy.orm import Session
from app.models.models import AcestreamChannel, ScrapedURL, TVChannel
from app.schemas.stats_schemas import URLStats, StatsResponse, TVChannelStatsResponse
from app.config.settings import settings
from app.services.task_service import task_service

class StatsService:
    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> StatsResponse:
        urls = self.db.query(ScrapedURL).all()
        channels = self.db.query(AcestreamChannel).all()
        # URL stats
        url_stats = []
        for url in urls:
            channel_count = self.db.query(AcestreamChannel).filter(AcestreamChannel.source_url == url.url).count()
            url_stats.append(URLStats(
                id=url.id,
                url=url.url,
                url_type=url.url_type,
                status=url.status,
                last_processed=str(url.last_scraped) if url.last_scraped else None,
                channel_count=channel_count,
                enabled=url.status != 'disabled',
                error_count=url.error_count or 0,
                last_error=url.last_error
            ))
        # Channel stats
        total_channels = len(channels)
        channels_checked = sum(1 for ch in channels if ch.last_checked is not None)
        channels_online = sum(1 for ch in channels if ch.last_checked is not None and ch.is_online is True)
        channels_offline = sum(1 for ch in channels if ch.last_checked is not None and ch.is_online is False)
        # Config
        base_url = getattr(settings, 'BASE_URL', '')
        ace_engine_url = getattr(settings, 'ACE_ENGINE_URL', '')
        rescrape_interval = getattr(settings, 'RESCRAPE_INTERVAL', 24)
        addpid = getattr(settings, 'ADDPID', False)
        # Task manager status
        try:
            jobs = task_service.get_jobs()
            task_manager_status = 'running' if jobs else 'stopped'
        except Exception:
            task_manager_status = 'unknown'
        return StatsResponse(
            urls=url_stats,
            total_channels=total_channels,
            channels=total_channels,  # Alias for compatibility
            channels_checked=channels_checked,
            channels_online=channels_online,
            channels_offline=channels_offline,
            base_url=base_url,
            ace_engine_url=ace_engine_url,
            rescrape_interval=rescrape_interval,
            addpid=addpid,
            task_manager_status=task_manager_status
        )

    def get_tv_channel_stats(self) -> TVChannelStatsResponse:
        total = self.db.query(TVChannel).count()
        active = self.db.query(TVChannel).filter(TVChannel.is_active == True).count()
        with_epg = self.db.query(TVChannel).filter(TVChannel.epg_id.isnot(None)).count()
        acestreams = self.db.query(AcestreamChannel).filter(AcestreamChannel.tv_channel_id.isnot(None)).count()
        return TVChannelStatsResponse(
            total=total,
            active=active,
            with_epg=with_epg,
            acestreams=acestreams
        )
