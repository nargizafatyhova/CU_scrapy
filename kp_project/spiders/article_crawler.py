import random

import scrapy

from kp_project.models import NewsArticle

CATEGORY_URLS = [
    "https://www.kp.ru/online/",
    "https://www.kp.ru/daily/",
    "https://www.kp.ru/politics/",
    "https://www.kp.ru/economics/",
    "https://www.kp.ru/society/",
    "https://www.kp.ru/sports/",
    "https://www.kp.ru/stars/",
    "https://www.kp.ru/incidents/",
    "https://www.kp.ru/science/",
    "https://www.kp.ru/family/",
]

ARTICLE_PATH_MARKERS = ("/daily/", "/online/")
SKIP_PATTERNS = (".jpg", ".png", "login", "auth", "#")
EXPLORATION_PROBABILITY = 0.2
MIN_PARAGRAPH_LENGTH = 30
FALLBACK_TEXT_THRESHOLD = 100
MIN_ARTICLE_TEXT_LENGTH = 200
MAX_ARTICLE_TEXT_LENGTH = 3000
MIN_KEYWORD_WORD_LENGTH = 4


class ArticleCrawler(scrapy.Spider):
    name = "kp"
    allowed_domains = ["kp.ru"]
    start_urls = CATEGORY_URLS

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
            "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
        },
        "CONCURRENT_REQUESTS": 32,
        "DOWNLOAD_DELAY": 0,
        "COOKIES_ENABLED": False,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
        "CLOSESPIDER_ITEMCOUNT": 11000,
    }

    # ------------------------------------------------------------------
    # Category page handler
    # ------------------------------------------------------------------

    def parse(self, response):
        links = response.css("a::attr(href)").getall()
        random.shuffle(links)

        for href in links:
            url = response.urljoin(href)
            if "kp.ru" not in url:
                continue

            if self._looks_like_article(url):
                yield response.follow(url, callback=self.parse_article)
            elif self._is_explorable(url) and random.random() < EXPLORATION_PROBABILITY:
                yield response.follow(url, callback=self.parse)

    # ------------------------------------------------------------------
    # Article page handler
    # ------------------------------------------------------------------

    def parse_article(self, response):
        title = response.css("h1::text").get()
        if not title:
            return

        body = self._extract_body(response)
        if len(body) <= MIN_ARTICLE_TEXT_LENGTH:
            return

        article = NewsArticle(
            source_url=response.url,
            title=title,
            description=self._meta_attr(response, "description"),
            article_text=body[:MAX_ARTICLE_TEXT_LENGTH],
            header_photo_url=self._og_attr(response, "og:image"),
            publication_datetime=self._og_attr(response, "article:published_time"),
            authors=self._meta_attr(response, "author"),
            keywords=self._resolve_keywords(response, title),
        )

        self.logger.info("Saved: %s", title[:50])
        yield article

        for href in response.css("a::attr(href)").getall():
            url = response.urljoin(href)
            if any(marker in url for marker in ARTICLE_PATH_MARKERS):
                yield response.follow(url, callback=self.parse_article)

    # ------------------------------------------------------------------
    # URL classification helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _looks_like_article(url: str) -> bool:
        has_marker = any(m in url for m in ARTICLE_PATH_MARKERS)
        has_digit = any(ch.isdigit() for ch in url)
        return has_marker and has_digit

    @staticmethod
    def _is_explorable(url: str) -> bool:
        return not any(pat in url for pat in SKIP_PATTERNS)

    # ------------------------------------------------------------------
    # Content extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_body(response) -> str:
        paragraphs = response.css("div p::text").getall()
        text = " ".join(p.strip() for p in paragraphs if len(p.strip()) > MIN_PARAGRAPH_LENGTH)

        if len(text) < FALLBACK_TEXT_THRESHOLD:
            blocks = response.xpath('//div[contains(@class, "text")]//text()').getall()
            text = " ".join(b.strip() for b in blocks if len(b.strip()) > MIN_PARAGRAPH_LENGTH)

        return text

    @staticmethod
    def _meta_attr(response, name: str) -> str | None:
        return response.xpath(f'//meta[@name="{name}"]/@content').get()

    @staticmethod
    def _og_attr(response, prop: str) -> str | None:
        return response.xpath(f'//meta[@property="{prop}"]/@content').get()

    @staticmethod
    def _resolve_keywords(response, title: str) -> str | None:
        kw = response.xpath('//meta[@name="keywords"]/@content').get()
        if kw:
            return kw

        tags = response.xpath('//meta[@property="article:tag"]/@content').getall()
        if tags:
            return ", ".join(tags)

        words = [w.strip(".,!?-") for w in title.split() if len(w) > MIN_KEYWORD_WORD_LENGTH - 1]
        return ", ".join(words)
