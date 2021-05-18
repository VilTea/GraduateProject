import os
import json


try:
    ROOT_PATH = os.environ['MYCHAN']
except Exception:
    raise ValueError

CONFIG_PATH = ROOT_PATH + '\\conf\\config.json'
with open(CONFIG_PATH, 'r') as config_file:
    config_file = json.loads(config_file.read())

# Mongo相关
MONGODB_CONFIG = config_file["DATABASE"]

MONGODB_HOST = MONGODB_CONFIG["host"]
MONGODB_PORT = MONGODB_CONFIG["port"]
MONGODB_DBNAME = MONGODB_CONFIG["dbname"]
MONGODB_USERNAME = MONGODB_CONFIG["username"] if "username" in MONGODB_CONFIG else None
MONGODB_PASSWORD = MONGODB_CONFIG["password"] if "password" in MONGODB_CONFIG else None

ADMIN_TABLE = MONGODB_CONFIG["collection"]["admin"]
USER_TABLE = MONGODB_CONFIG["collection"]["user"]
SECTION_TABLE = MONGODB_CONFIG["collection"]["section"]
STAGE_TABLE = MONGODB_CONFIG["collection"]["stage"]
LOG_TABLE = MONGODB_CONFIG["collection"]["log"]

# Redis相关
REDIS_CONFIG = config_file["CACHEBASE"]

REDIS_HOST = REDIS_CONFIG["host"]
REDIS_PORT = REDIS_CONFIG["port"]
REDIS_CACHE_MAXSIZE_FOR_NQ = REDIS_CONFIG["maxsize_NQ"]
REDIS_CACHE_EXPIRE_FOR_THC = REDIS_CONFIG["expire_THC"]  # 单位为秒
REDIS_CACHE_ASK_TIME_FOR_THC = REDIS_CONFIG["ask_time_THC"]  # 单位为秒
REDIS_CACHE_MAX_ASK_FOR_THC = REDIS_CONFIG["max_ask_THC"]  # 单位为秒

# DEBUG
DEBUG = config_file["DEBUG"]
