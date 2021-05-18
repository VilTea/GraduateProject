from foo.conf.config import REDIS_CACHE_MAXSIZE_FOR_NQ
from foo.cache.stageCacheBase import stageCacheBase

import foo.utils.StageUtils as StageUtils
import time


class normalCacheQueue(stageCacheBase):
    """
    常驻的先进先出时间线队列
    """
    def __init__(self):
        super().__init__()
        # 队列左进右出
        self.queue = "NQ"
        self.hits = "NQ_Hits"
        self.section = "NQ_SECTION_{}"
        self.section_count = "N_SECTION_TOTAL_{}"
        self.maxsize = REDIS_CACHE_MAXSIZE_FOR_NQ

    def __new__(cls, *args, **kwargs):
        """
        单例模式
        """
        if not hasattr(cls, "_instance"):
            cls.__instance = super(normalCacheQueue, cls).__new__(cls)
        return cls.__instance

    def push(self, code: str):
        """
        注意，传入的串号必须为主题串
        :param code: 主题串号
        :return: None
        """
        # code = StageUtils.get_prefix(code)
        if self.has_cache(code):
            data_dict = self.add_stage(code)
            self.conn.lrem(self.queue, 1, code)
            section_queue = self.section.format(int(data_dict.get('section_code')))
            self.conn.lrem(section_queue, 1, code)
        else:
            # data_dict: dict = StageUtils.get_with_time(code)
            # data_dict.pop('_id')
            # for key, value in data_dict.items():
            #     if isinstance(value, bool):
            #         data_dict[key] = int(value)
            data_dict = self.add_stage(code)
            section_queue = self.section.format(int(data_dict.get('section_code')))
            size_now = self.conn.llen(self.queue)
            while size_now >= self.maxsize:
                tmp = self.conn.rpop(self.queue)
                tmp = str(tmp, encoding='utf-8')
                self.conn.rpop(self.section.format(int(self.hget_value(tmp, 'section_code'))))
                print("一个缓存被删除：" + self.data.format(tmp))
                self.remove_stage(tmp)
                size_now = self.conn.llen(self.queue)
        self.conn.lpush(self.queue, code)
        self.conn.lpush(section_queue, code)

    def push_reply(self, code: str, prefix: str, data_dict: dict):
        """
        注意，必须传入回复串和主题串
        :param code: 回复串号
        :param prefix: 主题串号
        :return: None
        """
        if self.conn.sismember(self.hits, prefix):
            self.add_reply(code, prefix, data_dict)
            data_dict_for_prefix: dict = self._get_stage(prefix)
            self.conn.lrem(self.queue, 1, prefix)
            section_queue = self.section.format(int(data_dict_for_prefix.get('section_code')))
            self.conn.lrem(section_queue, 1, prefix)
        else:
            self.add_reply(code, prefix, data_dict)
            section_queue = self.section.format(int(data_dict.get('section_code')))
            size_now = self.conn.llen(self.queue)
            while size_now >= self.maxsize:
                tmp = self.conn.rpop(self.queue)
                tmp = str(tmp, encoding='utf-8')
                self.conn.rpop(self.section.format(int(self.hget_value(tmp, 'section_code'))))
                print("一个缓存被删除：" + self.data.format(tmp))
                self.remove_stage(tmp)
                size_now = self.conn.llen(self.queue)
        self.conn.lpush(self.queue, prefix)
        self.conn.lpush(section_queue, prefix)

    def rem(self, code: str):
        if self.has_cache(code):
            data_dict: dict = self._get_stage(code)
            self.conn.lrem(self.queue, 1, code)
            section_queue = self.section.format(int(data_dict.get('section_code')))
            self.conn.lrem(section_queue, 1, code)
            self.conn.srem(self.hits, code)
            # self.conn.decr(self.section_count.format(int(data_dict.get('section_code'))))
        else:
            print(''.join(['指定的串', code, '不在缓存中']))

    def get_queue(self, section_code: int = None, limit: int = -1, skip: int = 0) -> dict:
        queue = self._get_queue_name(section_code)
        length = self._get_queue_len(queue)
        if skip >= length:
            return {'data': [], 'rest': limit}
        else:
            rest = limit - length + skip
            limit = min(length - skip, limit)
        keys = [str(code, encoding='utf-8') for code in self.conn.lrange(queue, skip, skip + limit)]
        return {'data': keys, 'rest': rest}

    def get_queue_len(self, section_code: int = None) -> int:
        queue = self._get_queue_name(section_code)
        return self.conn.llen(queue)

    def get_queue_data(self, section_code: int = None, limit: int = -1, skip: int = 0) -> dict:
        """
        取出指定队列数据
        :param section_code: 指定模块队列，为空则取总队列
        :param limit:
        :param skip:
        :return: {'data': 取出的队列数据, 'rest': 期望取出数据量与实际取出数据量之差}
        """
        queue = self._get_queue_name(section_code)
        length = self._get_queue_len(queue)
        if skip >= length:
            return {'data': [], 'rest': limit}
        else:
            rest = limit - length + skip
            limit = min(length - skip, limit)
        data_code = self.conn.lrange(queue, skip, skip + limit - 1)
        data = list()
        for code in data_code:
            data.append(self.get_stage(str(code, encoding='utf-8')))
        return {'data': data, 'rest': rest}

    def _get_queue_name(self, section_code: int = None) -> str:
        if section_code is not None:
            return self.section.format(section_code)
        else:
            return self.queue

    def _get_queue_len(self, key: str) -> int:
        return self.conn.llen(key)

    def set_section_total(self, section_code: int, total: int):
        if section_code is None:
            section_code = 'time'
        self.conn.set(self.section_count.format(section_code), total)

    def get_section_total(self, section_code: int):
        if section_code is None:
            section_code = 'time'
        return int(self.conn.get(self.section_count.format(section_code)))

    def incr_section_total(self, section_code: int):
        self.conn.incr(self.section_count.format(section_code))
        self.conn.incr(self.section_count.format('time'))

    def decr_section_total(self, section_code: int):
        self.conn.decr(self.section_count.format(section_code))
        self.conn.decr(self.section_count.format('time'))

    def has_section_total(self, section_code: int) -> bool:
        if section_code is None:
            section_code = 'time'
        return self.conn.exists(self.section_count.format(section_code))

    def refresh(self):
        topics, t1, t2 = StageUtils.get_topics_with_time(page_size=self.maxsize, has_reply=False)
        for topic in topics[::-1]:
            self.push(topic.get('code'))


cache_NQ = normalCacheQueue()
