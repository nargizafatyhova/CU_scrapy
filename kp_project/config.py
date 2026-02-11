BOT_NAME = "kp_project"
SPIDER_MODULES = ["kp_project.spiders"]
NEWSPIDER_MODULE = "kp_project.spiders"

# --- HTTP request behavior ---------------------------------------------------
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 32
DOWNLOAD_DELAY = 0
COOKIES_ENABLED = False

# --- Crawl limits ------------------------------------------------------------
CLOSESPIDER_ITEMCOUNT = 10500
LOG_LEVEL = "INFO"

# --- Item pipelines ----------------------------------------------------------
ITEM_PIPELINES = {
    "kp_project.data_processing.PhotoBase64Pipeline": 300,
    "kp_project.data_processing.MongoPipeline": 400,
}

# --- MongoDB ------------------------------------------------------------------
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "kp_news_db"

# --- Playwright download handlers --------------------------------------------
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# --- Export -------------------------------------------------------------------
FEED_EXPORT_ENCODING = "utf-8"
