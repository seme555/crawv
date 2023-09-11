import pprint
import asyncio
import anyio
import signal
import traceback

from typing import Optional, Type, Union, Any

from crawv.settings import overridden_settings
from crawv.settings import Settings
from crawv.signalmanager import SignalManager
from crawv.utils.ossignal import install_shutdown_handlers, signal_names
from crawv.inject import DependencyInjection
from crawv import call_grace_instance
from crawv.spider import Spider


class Crawler(object):

    def __init__(self, spidercls: Type[Spider], settings: Union[Settings, dict, None] = None, * args, ** kwargs):

        if isinstance(settings, dict) or settings is None:
            settings = Settings(settings)

        self.spidercls = spidercls
        self.settings = settings.copy()
        self.spidercls.update_settings(self.settings)
        self.signals = SignalManager(self)

        if d := dict(overridden_settings(self.settings)):
            self.logger.info("Overridden settings {spider}:\n{settings}",
                        **{'settings': pprint.pformat(d), "spider": spidercls.__name__})

        self.settings.freeze()
        self.crawling = False
        self.spider = self._create_spider(*args, **kwargs)
        self.engine = None
        self.stats = call_grace_instance('stats', self)
        self.DI = self._create_dependency()
        self.extensions = self.load('extension')
        self._close_wait = None

    async def crawl(self) -> None:
        if self.crawling:
            raise RuntimeError("Crawling already taking place")
        self.crawling = True

        try:
            if not self.spider.start_urls and "memory" in self.settings['SCHEDULER']:
                raise self.di.get("exceptions").UsageError("Crawler not found task exists in spider.start_urls.")
            await self.DI.inject_runner()
            self.engine = self._create_engine()
            start_requests = await self.di.get("tools").async_generator_wrapper(self.spider.start_requests())
            await self.engine.start(self.spider, start_requests)
            await self.di.get("tools").task_await(self, "_close_wait")
        except Exception as e:
            self.logger.error(f"crawler: {traceback.format_exc()}")
            self.crawling = False
            if self.engine is not None:
                await self.engine.close()
            raise e

    def load(self, key: str) -> Any:
        return self.DI.load(key)

    def _create_spider(self, *args, **kwargs):
        return self.spidercls.from_crawler(self, *args, **kwargs)

    def _create_engine(self):
        return call_grace_instance('engine', self, self.stop)

    def _create_dependency(self):
        return DependencyInjection(self.settings, self)

    async def stop(self):
        if self.crawling:
