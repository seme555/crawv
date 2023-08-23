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
                await self.crawl(request, spider)

    def _needs_backout(self) -> bool:
        return (
            not self.running
            or self.slot.closing
            or self.downloader.needs_backout()
            or self.scraper.slot.needs_backout()
        )

    async def _handle_downloader_output(self, result, request, spider):
        try:
            if isinstance(result, self.di.get('request')):
                await self.crawl(result, spider)
                return
            if isinstance(result, self.di.get('response')):
                result.request = request
                logkws = self.logformatter.crawled(request, result, spider)
                level, message, kwargs = self.di.get("log").logformatter_adapter(logkws)
                if logkws is not None:
                    self.logger.log(level, message, **kwargs)
                await self.signals.send_catch_log(signals.response_received,
                                                  response=result, request=request, spider=spider)
        except Exception as e:
            self.logger.error(f"enqueue_scrape: {traceback.format_exc()}")
        finally:
            self.slot.remove_request(request)
        await self.scraper.enqueue_scrape(result, request)

    async def spider_is_idle(self, spider):
        if self.scraper.slot.is_idle():
            # scraper is not idle
            return False

        if self.downloader.active:
            # downloader has pending requests
            return False

        if self.slot.start_requests is not None:
            # not all start requests are handled
            return False

        if self.slot.inprogress:
            # not all start requests are handled
            return False

        if await self.call_helper(self.slot.scheduler.has_pending_requests):
            # scheduler has pending requests
            return False

        return True

    @property
    def open_spiders(self):
        return (self.spider,) if self.spider else set()

    def has_capacity(self):
        return not bool(self.slot)

    async def crawl(self, request, spider):  # å°†ç½‘å€ è¯·æ±‚åŠ å…¥é˜Ÿåˆ—
        if spider not in self.open_spiders:
            raise RuntimeError("Spider %r not opened when crawling: %s" % (spider.name, request))

        await self.signals.send_catch_log(signals.request_scheduled, request=request, spider=spider)
        if not await self.call_helper(self.slot.scheduler.enqueue_request, request):
            await self.signals.send_catch_log(signals.request_dropped, request=request, spider=spider)

    async def open_spider(self, spider, start_requests=None, close_if_idle=True):
        if not self.has_capacity():
            raise RuntimeError("No free spider slot when opening %r" % spider.name)
        self.logger.info("Spider opened({name})", **{"name": spider.name}, extra={'spider': spider})

        self.slot = Slot(start_requests, close_if_idle, self.scheduler, self.crawler)
        self.spider = spider
        await self.call_helper(self.scheduler.open, start_requests)
        await self.call_helper(self.downloader.open, spider, self)
