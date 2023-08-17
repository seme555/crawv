BOT_NAME = "crawv"

# Concurrency settings
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 0
CONCURRENT_ITEMS = 16

# Adaptive concurrency settings
ADAPTIVE_CONCURRENCY_ENABLED = False
ADAPTIVE_CONCURRENCY_TARGET_RESPONSE_TIME = 1.0  # seconds
ADAPTIVE_CONCURRENCY_MIN_REQUESTS = 8
ADAPTIVE_CONCURRENCY_MAX_REQUESTS = 32
ADAPTIVE_CONCURRENCY_WINDOW_SIZE = 20
ADAPTIVE_CONCURRENCY_ADJUSTMENT_INTERVAL = 10  # seconds

# Download settings
DOWNLOAD_DELAY = 0
DOWNLOAD_TIMEOUT = 20
RANDOMIZE_DOWNLOAD_DELAY = True

# Memory optimization settings
GC_ENABLED = True
GC_FREQUENCY = 10  # Run garbage collection every 10 heartbeats

# Task beat settings
TASK_BEAT_ACTIVE_SLEEP = 0.2  # Sleep when active (seconds)
TASK_BEAT_IDLE_SLEEP = 1.0    # Sleep when idle (seconds)
TASK_BEAT_BATCH_SIZE = 100    # Max requests per batch

# Handler and scheduler settings
# DOWNLOAD_HANDLER = "crawv.core.downloader.handlers.aiohttp.AioHttpDownloadHandler"
DOWNLOAD_HANDLER = "crawv.core.downloader.handlers.httpx.HttpxDownloadHandler"
# DOWNLOAD_HANDLER = "crawv.core.downloader.handlers.requests.RequestsDownloadHandler"
# SCHEDULER = "crawv.core.scheduler.redis.RedisScheduler"
SCHEDULER = "crawv.core.scheduler.memory.MemoryScheduler"
REQUESTS_SESSION_STATS = False

SPIDER_IDLE = False

# LOG CONFIG
LOG_LEVEL = "DEBUG"
LOG_FILE = False
LOG_FILENAME = f"{BOT_NAME}.log"
LOG_ENCODING = "utf-8"
LOG_ROTATION = "1 week"
LOG_RETENTION = "30 days"

DI_CONFIG = {
    "scheduler": f"{SCHEDULER}",
    "log_formatter": "crawv.logformatter.LogFormatter",
    "extension": "crawv.middleware.ExtensionManager",

}
DI_CONFIG_CLS = {
    "request": "crawv.http.Request",
    "response": "crawv.http.TextResponse",
    "form_request": "crawv.http.FormRequest",
    "json_request": "crawv.http.JsonRequest",
    "logger": "crawv.utils.log.logger",
    "log": "crawv.utils.log",
    "exceptions": "crawv.exceptions",
    "tools": "crawv.utils.tools",
    'downloader_middleware': 'crawv.middleware.DownloaderMiddlewareManager',
    "item_processor": "crawv.middleware.ItemPipelineManager",
}
DI_CREATE_CLS = {
    'crawler': 'crawv.crawler.Crawler',
    'crawler_process': 'crawv.crawler.CrawlerProcess',
    'engine': 'crawv.core.engine.ExecutionEngine',
    'spider': 'crawv.spider.Spider',
    'downloader_handler': f'{DOWNLOAD_HANDLER}',
    'stats': 'crawv.libs.statscollectors.MemoryStatsCollector',
    'scraper': 'crawv.core.scraper.Scraper',
    "downloader": "crawv.core.downloader.Downloader",
}
