

![crawv](./images/crawv.png)

# Crawv

ä¸€ä¸ªå¼ºå¤§çš„ã€é«˜æ€§èƒ½çš„å¼‚æ­¥Webçˆ¬å–å’ŒæŠ“å–æ¡†æž¶ï¼ŒåŸºäºŽPythonçš„asyncioç”Ÿæ€ç³»ç»Ÿæž„å»ºã€‚

[è‹±æ–‡](../README.md) | ä¸­æ–‡

## æ¦‚è¿°

Crawvæ˜¯ä¸€ä¸ªå¿«é€Ÿçš„é«˜çº§webçˆ¬è¡Œå’ŒwebæŠ“å–æ¡†æž¶ï¼Œç”¨äºŽæŠ“å–ç½‘ç«™å¹¶ä»Žå…¶é¡µé¢æå–ç»“æž„åŒ–æ•°æ®ã€‚å®ƒå—åˆ°Scrapyå’Œscrapy_redisçš„å¯å‘ï¼Œä½†ä»Žå¤´å¼€å§‹è®¾è®¡ï¼Œå……åˆ†åˆ©ç”¨å¼‚æ­¥ç¼–ç¨‹çš„å…¨éƒ¨åŠŸèƒ½ã€‚

### ä¸»è¦ç‰¹ç‚¹

- **å®Œå…¨å¼‚æ­¥**ï¼šåŸºäºŽPythonçš„asyncioï¼Œå®žçŽ°é«˜æ€§èƒ½å¹¶å‘æ“ä½œ
- **Scrapyé£Žæ ¼çš„API**ï¼šä¸ºæ¥è‡ªScrapyçš„ç”¨æˆ·æä¾›ç†Ÿæ‚‰çš„API
- **åˆ†å¸ƒå¼çˆ¬å–**ï¼šæ”¯æŒä½¿ç”¨Redisè¿›è¡Œåˆ†å¸ƒå¼çˆ¬å–
- **å¤šç§HTTPåŽç«¯**ï¼šæ”¯æŒaiohttpã€httpxå’Œrequests
- **åŠ¨æ€å˜é‡æ³¨å…¥**ï¼šå¼ºå¤§çš„ä¾èµ–æ³¨å…¥ç³»ç»Ÿ
- **çµæ´»çš„ä¸­é—´ä»¶ç³»ç»Ÿ**ï¼šå¯å®šåˆ¶çš„è¯·æ±‚/å“åº”å¤„ç†ç®¡é“
- **å¼ºå¤§çš„æ•°æ®å¤„ç†**ï¼šç”¨äºŽå¤„ç†çˆ¬å–æ•°æ®çš„ç®¡é“

## ç³»ç»Ÿè¦æ±‚

- Python 3.8+
- æ”¯æŒLinuxã€Windowsã€macOSã€BSD

## å®‰è£…

### åŸºæœ¬å®‰è£…

```shell
pip install crawv
```

### å®‰è£…æ‰€æœ‰ä¾èµ–

```shell
pip install crawv[all]
```

### å®‰è£…ç‰¹å®šHTTPåŽç«¯

```shell
pip install crawv[aiohttp,httpx]
```

### ä»Žæœ€æ–°ç‰ˆæœ¬å®‰è£…

```shell
pip install git+https://github.com/seme555/crawv
```

## å¿«é€Ÿå¼€å§‹

### åˆ›å»ºæ–°é¡¹ç›®

```shell
crawv startproject myproject
cd myproject
```

### åˆ›å»ºçˆ¬è™«

```shell
crawv genspider myspider
```

è¿™å°†åœ¨`spiders`ç›®å½•ä¸­åˆ›å»ºä¸€ä¸ªåŸºæœ¬çˆ¬è™«ã€‚

![tree](./images/tree.png)

### ç¤ºä¾‹çˆ¬è™«

```python
from crawv.spider import Spider


class QuotesSpider(Spider):
    name = 'quotes'
    custom_settings = {
        "SPIDER_IDLE": False
    }
    start_urls = [
        'https://quotes.toscrape.com/tag/humor/',
    ]

    async def parse(self, response):
        for quote in response.css('div.quote'):
            yield {
                'author': quote.xpath('span/small/text()').get(),
                'text': quote.css('span.text::text').get(),
            }

        next_page = response.css('li.next a::attr("href")').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)
```

### åˆ›å»ºå•ä¸ªçˆ¬è™«è„šæœ¬

```shell
crawv onespider single_quotes
```

### é«˜çº§çˆ¬è™«ç¤ºä¾‹

```python
from crawv.spider import Spider
from anti_header import Header
from pprint import pprint, pformat


class SingleQuotesSpider(Spider):
    name = 'single_quotes'
    custom_settings = {
        "SPIDER_IDLE": False
    }
    start_urls = [
        'https://quotes.toscrape.com/',
    ]

    async def process_request(self, request):
        request.headers = Header(url=request.url, platform='windows', connection=True).random
        return request

    async def process_response(self, request, response):
        if response.status in [404, 503]:
            return request
        return response

    async def process_exception(self, request, exc):
        raise exc

    async def parse(self, response):
        for quote in response.css('div.quote'):
            yield {
                'author': quote.xpath('span/small/text()').get(),
                'text': quote.css('span.text::text').get(),
            }

        next_page = response.css('li.next a::attr("href")').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    async def process_item(self, item):
        self.logger.info("{item}", **{'item': pformat(item)})


if __name__ == '__main__':
    quotes = SingleQuotesSpider()
    quotes.start()
```

### è¿è¡Œçˆ¬è™«

```shell
# ä»Žé¡¹ç›®ä¸­è¿è¡Œçˆ¬è™«
crawv crawl quotes

# è¿è¡Œå•ä¸ªçˆ¬è™«è„šæœ¬
crawv runspider quotes.py
```

![run](./images/run.png)

### ä»Žä»£ç ä¸­è¿è¡Œ

```python
from crawv.crawler import call_grace_instance
from crawv.utils.tools import get_project_settings

# æ–¹æ³•1ï¼šä»Žç›®å½•ä¸­åŠ è½½æ‰€æœ‰çˆ¬è™«
def load_spiders_from_directory():
    process = call_grace_instance("crawler_process", get_project_settings())
    process.load_spider(path='./spiders')
    process.start()

# æ–¹æ³•2ï¼šæŒ‰åç§°è¿è¡Œç‰¹å®šçˆ¬è™«
def run_specific_spider():
    process = call_grace_instance("crawler_process", get_project_settings())
    process.crawl('myspider')
    process.start()

if __name__ == '__main__':
    run_specific_spider()
```

## é…ç½®

Crawvå¯ä»¥é€šè¿‡é¡¹ç›®ä¸­çš„`settings.py`æ–‡ä»¶è¿›è¡Œé…ç½®ã€‚ä»¥ä¸‹æ˜¯æœ€é‡è¦çš„è®¾ç½®ï¼š

### å¹¶å‘è®¾ç½®

```python
# æœ€å¤§å¹¶å‘å¤„ç†é¡¹ç›®æ•°
CONCURRENT_ITEMS = 100

# æœ€å¤§å¹¶å‘è¯·æ±‚æ•°
CONCURRENT_REQUESTS = 16

# æ¯ä¸ªåŸŸåçš„æœ€å¤§å¹¶å‘è¯·æ±‚æ•°
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# æ¯ä¸ªIPçš„æœ€å¤§å¹¶å‘è¯·æ±‚æ•°
CONCURRENT_REQUESTS_PER_IP = 0
```

### ä¸‹è½½è®¾ç½®

```python
# è¯·æ±‚é—´çš„å»¶è¿Ÿï¼ˆç§’ï¼‰
DOWNLOAD_DELAY = 0

# è¯·æ±‚è¶…æ—¶æ—¶é—´ï¼ˆç§’ï¼‰
DOWNLOAD_TIMEOUT = 20

# æ˜¯å¦éšæœºåŒ–ä¸‹è½½å»¶è¿Ÿ
RANDOMIZE_DOWNLOAD_DELAY = True

# ä½¿ç”¨çš„HTTPåŽç«¯
DOWNLOAD_HANDLER = "crawv.core.downloader.handlers.httpx.HttpxDownloadHandler"
# å…¶ä»–é€‰é¡¹ï¼š
# DOWNLOAD_HANDLER = "crawv.core.downloader.handlers.aiohttp.AioHttpDownloadHandler"
# DOWNLOAD_HANDLER = "crawv.core.downloader.handlers.requests.RequestsDownloadHandler"
```

### è°ƒåº¦å™¨è®¾ç½®

```python
# ä½¿ç”¨çš„è°ƒåº¦å™¨ï¼ˆåŸºäºŽå†…å­˜æˆ–Redisï¼‰
SCHEDULER = "crawv.core.scheduler.memory.MemoryScheduler"
# åˆ†å¸ƒå¼çˆ¬å–ï¼š
# SCHEDULER = "crawv.core.scheduler.redis.RedisScheduler"

# Redisè¿žæŽ¥è®¾ç½®ï¼ˆç”¨äºŽRedisè°ƒåº¦å™¨ï¼‰
REDIS_URI = "redis://localhost:6379"
QUEUE_KEY = "%(spider)s:queue"
```

## å“åº”API

Crawvæä¾›äº†ä¸°å¯Œçš„APIæ¥å¤„ç†å“åº”ï¼š

### æå–æ•°æ®

```python
# ä½¿ç”¨CSSé€‰æ‹©å™¨
title = response.css('title::text').get()
all_links = response.css('a::attr(href)').getall()

# ä½¿ç”¨XPath
title = response.xpath('//title/text()').get()
all_links = response.xpath('//a/@href').getall()
```

### è·Ÿè¸ªé“¾æŽ¥

```python
# è·Ÿè¸ªé“¾æŽ¥
yield response.follow('next-page.html', self.parse)

# ä½¿ç”¨å›žè°ƒè·Ÿè¸ªé“¾æŽ¥
yield response.follow('details.html', self.parse_details)

# è·Ÿè¸ªæ‰€æœ‰åŒ¹é…çš„CSSé€‰æ‹©å™¨çš„é“¾æŽ¥
yield from response.follow_all(css='a.product::attr(href)', callback=self.parse_product)
```

## æ›´å¤šå‘½ä»¤

```shell
crawv -h
```

## åˆ†å¸ƒå¼çˆ¬å–

è¦å¯ç”¨åŸºäºŽRedisçš„åˆ†å¸ƒå¼çˆ¬å–ï¼š

1. åœ¨è®¾ç½®ä¸­é…ç½®Redisï¼š

```python
SCHEDULER = "crawv.core.scheduler.redis.RedisScheduler"
REDIS_URI = "redis://localhost:6379"
QUEUE_KEY = "%(spider)s:queue"
```

2. åœ¨ä¸åŒçš„æœºå™¨ä¸Šè¿è¡Œå¤šä¸ªçˆ¬è™«å®žä¾‹ï¼Œå…¨éƒ¨è¿žæŽ¥åˆ°åŒä¸€ä¸ªRedisæœåŠ¡å™¨ã€‚

## è´¡çŒ®

è¯·é€šè¿‡åˆ›å»ºissueå‘é¡¹ç›®æ‰€æœ‰è€…æäº¤æ‚¨çš„å»ºè®®ã€‚

## æ„Ÿè°¢

[aiohttp](https://github.com/aio-libs/aiohttp/)

[scrapy](https://github.com/scrapy/scrapy)

[loguru](https://github.com/Delgan/loguru)

[httpx](https://github.com/encode/httpx)
