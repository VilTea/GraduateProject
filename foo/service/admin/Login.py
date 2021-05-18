from foo.client.MongoClient import MongoClient
import foo.service.admin.BloomFilter4Admin as bf4admin
from typing import Optional
from foo.conf import config


def login(name: str, password: str) -> Optional[str]:
    """
    管理员登录
    """
    # 读取布隆过滤器
    if bf4admin.bloomFilter.contains(name):
        # 连接数据库
        client = MongoClient()
        client.set_col(config.ADMIN_TABLE)
        col = client.get_col()
        admin = col.find_one({"name": name})
        if admin is not None and admin["password"] == password:
            return admin["pet"]
    return None
