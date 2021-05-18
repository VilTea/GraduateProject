import logging

from foo.client.MongoClient import MongoClient
import foo.utils.BloomFilterUtils as bf
from foo.conf import config


class BloomFilterBuilder4Admin(bf.BloomFilterBuilder):
    def __new__(cls, *args, **kwargs):
        """
        单例模式
        """
        if not hasattr(cls, "_instance"):
            cls.__instance = super(BloomFilterBuilder4Admin, cls).__new__(cls)
        return cls.__instance


class BloomFilterReader4Admin(bf.BloomFilterReader):
    def __new__(cls, *args, **kwargs):
        """
        单例模式
        """
        if not hasattr(cls, "_instance"):
            cls.__instance = super(BloomFilterReader4Admin, cls).__new__(cls)
        return cls.__instance


def refresh():
    global bloomFilter
    client = MongoClient()
    client.set_col(config.ADMIN_TABLE)
    col = client.get_col()
    bloomFilter.initialize()
    for elem in col.find():
        bloomFilter.add(elem["name"])


def upload():
    global bloomFilter
    if isinstance(bloomFilter, BloomFilterBuilder4Admin):
        bloomFilter.upload("BloomFilter4Admin")
    else:
        bloomFilter.upload()


logger = logging.getLogger("BloomFilter.admin")

# noinspection PyBroadException
try:
    bloomFilter = BloomFilterReader4Admin("BloomFilter4Admin")
except Exception:
    logger.exception(Exception)
    bloomFilter = BloomFilterBuilder4Admin(5000000)
    print("bloom filter build...")
    refresh()
    upload()