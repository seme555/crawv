

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
