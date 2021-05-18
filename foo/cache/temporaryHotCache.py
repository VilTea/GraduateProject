from flask import request
from foo.cache.stageCacheBase import stageCacheBase
from foo.conf.config import REDIS_CACHE_EXPIRE_FOR_THC, REDIS_CACHE_MAX_ASK_FOR_THC, REDIS_CACHE_ASK_TIME_FOR_THC, DEBUG

import time
import foo.utils.StageUtils as StageUtils


class temporaryHotCache(stageCacheBase):
    """
    临时的热点数据缓存，缓存穿透问题解决方案
    """
    def __init__(self):
        super().__init__()
        self.requests = "THC_Request_{}"
        self.hits = "THC_Hits"  # THC使用有序集合
        self._locks = "THC_Lock"
        self.expire_time = REDIS_CACHE_EXPIRE_FOR_THC
        self.ask_time = REDIS_CACHE_ASK_TIME_FOR_THC
        self.max_ask = REDIS_CACHE_MAX_ASK_FOR_THC
        self.debug = DEBUG

    def __new__(cls, *args, **kwargs):
        """
        单例模式
        """
        if not hasattr(cls, "_instance"):
            cls.__instance = super(temporaryHotCache, cls).__new__(cls)
        return cls.__instance

    def ask(self, code: str) -> bool:
        while True:
            if self.has_cache(code):
                if self.conn.exists(self.data.format(code)) or self.conn.exists(self.data_reply.format(code)):
                    self.conn.expire(self.get_cache_name(code), self.expire_time)
                    self.conn.zadd(self.hits, {code: int(time.time())})
                    if self.conn.exists(self.data.format(code)):
                        replies = self.get_replies_code(code)
                        print(replies)
                        for reply in replies:
                            self.conn.expire(self.data_reply.format(reply), self.expire_time)
                    return True
                else:
                    self.conn.zrem(self.hits, code)
            else:
                if self.is_lock(code):
                    return False
                if self.debug:
                    name = self.requests.format("_".join(['debug', code]))
                    self.conn.incr(name)
                    ask_times = int(self.conn.get(name))
                else:
                    name = self.requests.format(code)
                    ip_addr = request.remote_addr
                    self.conn.sadd(name, ip_addr)
                    ask_times = self.conn.scard(name)
                self.conn.expire(name, self.ask_time)
                if ask_times >= self.max_ask:
                    self._lock(code)
                    self.add_stage(code)
                    self._release(code)
                return True

    def is_lock(self, code: str) -> bool:
        return self.conn.sismember(self._locks, code)

    def _lock(self, code: str):
        # 上锁时顺便清理有序集合hits中的过期数据
        self.conn.zremrangebyscore(self.hits, 0, int(time.time() - self.expire_time))
        self.conn.sadd(self._locks, code)

    def _release(self, code: str):
        self.conn.srem(self._locks, code)
        if self.debug:
            name = self.requests.format("_".join(['debug', code]))
        else:
            name = self.requests.format(code)
        self.conn.delete(name)

    def add_stage(self, code: str):
        """
        重写add_stage方法，加入过期时间，以及针对有序集合hits做了更改
        得到新回应的串会被填入NQ队列，因此回应操作不会
        :param code:
        :return:
        """
        if self.has_cache(code):
            data_dict: dict = self._get_stage(code)
            data_dict['rptm'] = int(time.time())
            self.conn.zadd(self.hits, {code: int(time.time())})
        else:
            data_dict: dict = StageUtils.get_with_time_physic(code)
            data_dict.pop('_id')
            for key, value in data_dict.items():
                if isinstance(value, bool):
                    data_dict[key] = int(value)
            # self.conn.sadd(self.hits, code)
            self.conn.zadd(self.hits, {code: int(time.time())})
            replies = StageUtils.get_reply_all_physic(code)
            replies_code = list()
            for reply in replies:
                reply.pop('_id')
                for key, value in reply.items():
                    if isinstance(value, bool):
                        reply[key] = int(value)
                self.conn.hmset(self.data_reply.format(reply.get('code')), reply)
                self.conn.expire(self.data_reply.format(reply.get('code')), self.expire_time)
                replies_code.append(reply.get('code'))
            data_dict['replies'] = ",".join(replies_code)
        self.conn.hmset(self.data.format(code), data_dict)
        self.conn.expire(self.data.format(code), self.expire_time)
        return data_dict

    def has_cache(self, code: str) -> bool:
        """
        重写has_cache方法，因为回应串没有存入THC集合
        :param code:
        :return:
        """
        if self.conn.zscore(self.hits, code) or self.conn.exists(self.data_reply.format(code)):
            return True
        else:
            return False


cache_THC = temporaryHotCache()
