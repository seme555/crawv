

![crawv](./doc/images/crawv.png)

# Crawv

A powerful, high-performance asynchronous web crawling and scraping framework built on Python's asyncio ecosystem.

English | [ä¸­æ–‡](./doc/README_ZH.md)

## Overview

Crawv is a fast high-level web crawling and web scraping framework, used to crawl websites and extract structured data from their pages. It draws inspiration from Scrapy and scrapy_redis but is designed from the ground up to leverage the full power of asynchronous programming.

### Key Features

- **Fully Asynchronous**: Built on Python's asyncio for high-performance concurrent operations
- **Scrapy-like API**: Familiar API for those coming from Scrapy
- **Distributed Crawling**: Support for distributed crawling using Redis
- **Multiple HTTP Backends**: Support for aiohttp, httpx, and requests
- **Dynamic Variable Injection**: Powerful dependency injection system
- **Flexible Middleware System**: Customizable request/response processing pipeline
- **Robust Item Processing**: Pipeline for processing scraped items

## Requirements

- Python 3.8+
- Works on Linux, Windows, macOS, BSD

## Installation

### Basic Installation

```shell
pip install crawv
```

### With All Dependencies

```shell
pip install crawv[all]
```

### With Specific HTTP Backends

```shell
pip install crawv[aiohttp,httpx]
```

### Latest Version from GitHub

```shell
pip install git+https://github.com/seme555/crawv
```

## Quick Start

### Creating a New Project

```shell
crawv startproject myproject
cd myproject
```

### Creating a Spider

```shell
crawv genspider myspider
```

This will create a basic spider in the `spiders` directory.

![tree](./doc/images/tree.png)

### Example Spider

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

### Creating a Single Spider Script

```shell
crawv onespider single_quotes
```

### Advanced Spider Example

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
