import base64

import pymongo
import requests
from itemadapter import ItemAdapter

IMAGE_DOWNLOAD_TIMEOUT = 5
COLLECTION_NAME = "articles"


class PhotoBase64Pipeline:
    """Downloads the header photo and stores its Base64 encoding on the item."""

    def process_item(self, item, spider):
        url = item.get("header_photo_url")
        if not url:
            return item

        try:
            resp = requests.get(url, timeout=IMAGE_DOWNLOAD_TIMEOUT)
            if resp.status_code == 200:
                item["header_photo_base64"] = base64.b64encode(resp.content).decode("utf-8")
        except Exception:
            spider.logger.warning("Failed to download photo: %s", url)

        return item


class MongoPipeline:
    """Persists each scraped item into a MongoDB collection."""

    def __init__(self, uri: str, database: str):
        self.uri = uri
        self.database = database
        self.client: pymongo.MongoClient | None = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            uri=crawler.settings.get("MONGO_URI"),
            database=crawler.settings.get("MONGO_DATABASE", "items"),
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.uri)

    def close_spider(self, spider):
        if self.client:
            self.client.close()

    def process_item(self, item, spider):
        db = self.client[self.database]
        db[COLLECTION_NAME].insert_one(ItemAdapter(item).asdict())
        return item
