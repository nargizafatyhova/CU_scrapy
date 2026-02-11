import scrapy


class NewsArticle(scrapy.Item):
    """Structured representation of a scraped kp.ru news article."""

    source_url = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    article_text = scrapy.Field()
    publication_datetime = scrapy.Field()
    header_photo_url = scrapy.Field()
    header_photo_base64 = scrapy.Field()
    keywords = scrapy.Field()
    authors = scrapy.Field()
