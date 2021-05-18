import logging
from foo.client.MongoClient import MongoClient
import foo.utils.BloomFilterUtils as bf
from foo.conf import config


class BloomFilterBuilder4User(bf.BloomFilterBuilder):
    def __new__(cls, *args, **kwargs):
        """
        单例模式
        """
        if not hasattr(cls, "_instance"):
            cls.__instance = super(BloomFilterBuilder4User, cls).__new__(cls)
        return cls.__instance


class BloomFilterReader4User(bf.BloomFilterReader):
    def __new__(cls, *args, **kwargs):
        """
        单例模式
        """
        if not hasattr(cls, "_instance"):
            cls.__instance = super(BloomFilterReader4User, cls).__new__(cls)
        return cls.__instance


def refresh():
    global bloomFilter
    client = MongoClient()
    client.set_col(config.USER_TABLE)
    col = client.get_col()
    bloomFilter.initialize()
    for elem in col.find({"is_del": False}, {"serial": 1}):
        bloomFilter.add(elem["serial"])


def upload():
    global bloomFilter
    if isinstance(bloomFilter, BloomFilterBuilder4User):
        bloomFilter.upload("BloomFilter4User")
    else:
        bloomFilter.upload()


logger = logging.getLogger("BloomFilter.user")

# noinspection PyBroadException
try:
    bloomFilter = BloomFilterReader4User("BloomFilter4User")
except Exception:
    logger.exception(Exception)
    bloomFilter = BloomFilterBuilder4User(800000000)
    print("bloom filter build...")
    refresh()
    upload()