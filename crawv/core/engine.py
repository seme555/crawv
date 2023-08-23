import asyncio
import traceback
import gc
import os

from time import time

from crawv import signals, call_grace_instance


class Slot(object):

    def __init__(self, start_requests, close_if_idle, scheduler, crawler):
        self.closing = None
        self.inprogress = set()

        self.start_requests = start_requests
        self.close_if_idle = close_if_idle
        self.scheduler = scheduler
        self.crawler = crawler
        self.heartbeat = None
        self.closing_wait = None

    def add_request(self, request):
        self.inprogress.add(request)

    def remove_request(self, request):
        self.inprogress.discard(request)

    async def close(self):
        self.closing = True


class ExecutionEngine(object):

    def __init__(self, crawler, spider_closed_callback):
        self.start_time = time()
        self.crawler = crawler
        self.settings = crawler.settings
        self.slot = None
        self.spider = None
        self.scheduler = None
        self.running = False
        self._heart_beat = None
        self._task_beat = None
        self.signals = crawler.signals
        self.logformatter = crawler.load("log_formatter")
        self.scheduler = crawler.load("scheduler")
        self.downloader = call_grace_instance('downloader', crawler)
        self.scraper = call_grace_instance("scraper", crawler)
        self.call_helper = self.di.get("tools").call_helper
        self.lock = asyncio.Lock()
        self._spider_closed_callback = spider_closed_callback

    async def start(self, spider, start_requests=None):
        self.start_time = time()
        await self.signals.send_catch_log_coroutine(signal=signals.engine_started)
        self.running = True
        await self.open_spider(spider, start_requests, close_if_idle=True)

    async def stop(self):
        self.running = False
        # await self._close_all_spiders()
        await self.signals.send_catch_log_coroutine(signal=signals.engine_stopped)

    async def start_spider_request(self, spider):
        if self.slot.start_requests and not self._needs_backout():
            try:
                request = await self.slot.start_requests.__anext__()
            except StopAsyncIteration:
                self.slot.start_requests = None
            except Exception:
                self.slot.start_requests = None
                self.logger.error('Error while obtaining start requests',
                                    exc_info=True, extra={'spider': spider})
            else:
