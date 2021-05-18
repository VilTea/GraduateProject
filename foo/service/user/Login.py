from typing import Optional
from foo.client.MongoClient import MongoClient

import foo.conf.config as config
import foo.service.user.BloomFilter4User as bf4user


def login(serial) -> Optional[str]:
    if bf4user.bloomFilter.contains(serial):
        client = MongoClient()
        client.set_col(config.USER_TABLE)
        if client.contains("serial", serial):
            data = client.get_one("serial", serial)
            if data["is_del"] is False:
                return data["id"]
    return None


def logout():
    pass
