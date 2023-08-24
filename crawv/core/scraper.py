import asyncio
import traceback

from collections import deque

from crawv import signals, call_grace_instance


class Slot:
    MIN_RESPONSE_SIZE = 1024

    def __init__(self, max_active_size: int = 5000):
        self.max_active_size = max_active_size
        self.queue = deque()
        self.active = set()
        self.active_size = 0
        self.itemproc_size = 0
        self.closing_future = None
        self.closing_lock = True

    def add_response_request(self, response, request):
        self.queue.append((response, request))
        self.active.add(request)
        if hasattr(response, 'body') and response.body is not None:
            self.active_size += max(len(response.body), self.MIN_RESPONSE_SIZE)

    def next_response_request_deferred(self):
        response, request = self.queue.popleft()
        return response, request

    def finish_response(self, request, response):
        self.active.discard(request)
        # self.logger.warning(f'start finish response active del: {self.active_size}, active: {len(self.active)}, response: {len(response.body)}')
        if hasattr(response, 'body') and response.body is not None:
            self.active_size -= max(len(response.body), self.MIN_RESPONSE_SIZE)
        request, response = None, None        

    def is_idle(self):
        return self.queue or self.active

    def needs_backout(self):
        return self.active_size > self.max_active_size


class Scraper:

    def __init__(self, crawler):
        self.slot = None
        self.itemproc = call_grace_instance(self.di.get('item_processor'), only_instance=True).from_crawler(crawler)
        self.crawler = crawler
        self.signals = crawler.signals
        self.logformatter = crawler.load("log_formatter")
        self.call_helper = self.di.get("tools").call_helper
        self.concurrent_items_semaphore = asyncio.Semaphore(crawler.settings.getint('CONCURRENT_ITEMS', 100))
        self.task_scrape_next = None

    async def open_spider(self, spider):
        self.slot = call_grace_instance(Slot, self.crawler.settings.getint('SCRAPER_SLOT_MAX_ACTIVE_SIZE', 500000))
        await self.itemproc.open_spider(spider)
        self.task_scrape_next = asyncio.create_task(self._scrape_next(spider, self.slot))

    async def close_spider(self, spider):
        slot = self.slot
        await self.itemproc.close_spider(spider)
        if self.task_scrape_next is not None:
            self.task_scrape_next.cancel()
        self._check_if_closing(spider, slot)

    def is_idle(self):
        return not self.slot

    def _check_if_closing(self, spider, slot):
        if not slot.closing_future and slot.is_idle() and slot.closing_lock:
            slot.closing_lock = False

    async def enqueue_scrape(self, response, request):
