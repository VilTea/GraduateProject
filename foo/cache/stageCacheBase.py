from math import ceil
from typing import List

from foo.client.RedisClient import RedisClient

import foo.utils.StageUtils as StageUtils
import time


class stageCacheBase(object):
    """
    串相关缓存基类
    """
    def __init__(self):
        self.redis_client = RedisClient()
        self.conn = self.redis_client.get_client()
        self.data = "Stage_Data_{}"
        self.data_reply = "Stage_Data_reply_{}"
        self.hits = "Stage_Hits"

    def has_cache(self, code: str) -> bool:
        return self.conn.sismember(self.hits, code)

    def soft_del(self, code: str):
        if self.has_cache(code):
            if self.get_type(code) == 'reply':
                self.update_reply(code, 'is_del', 1)
            else:
                self.update_hash(code, 'is_del', 1)
        else:
            print(''.join(['指定的串', code, '不在缓存中']))

    def notes(self, code: str, notes: str):
        if self.has_cache(code):
            print(notes)
            if self.get_type(code) == 'reply':
                if notes is None or notes == '':
                    self.conn.hdel(self.data_reply.format(code), "notes")
                else:
                    self.update_reply(code, 'notes', notes)
            else:
                if notes is None or notes == '':
                    self.conn.hdel(self.data.format(code), "notes")
                else:
                    self.update_hash(code, 'notes', notes)
        else:
            print(''.join(['指定的串', code, '不在缓存中']))

    def soft_restore(self, code: str):
        if self.has_cache(code):
            if self.get_type(code) == 'reply':
                self.update_reply(code, 'is_del', 0)
            else:
                self.update_hash(code, 'is_del', 0)
        else:
            print(''.join(['指定的串', code, '不在缓存中']))

    def add_force(self, code: str):
        data_dict: dict = StageUtils.get_with_time_physic(code)
        data_dict.pop('_id')
        for key, value in data_dict.items():
            if isinstance(value, bool):
                data_dict[key] = int(value)
        if 'prefix' in data_dict:
            name = self.data_reply.format(code)
        else:
            name = self.data.format(code)
        self.conn.sadd(self.hits, code)
        self.conn.hmset(name, data_dict)

    def get(self, code: str, **kwargs):
        if self.conn.exists(self.data.format(code)):
            return self.get_stage_and_reply_pagination(code, **kwargs)
        elif self.conn.exists(self.data_reply.format(code)):
            return self.get_reply(code)

    def get_type(self, code: str):
        if self.conn.exists(self.data.format(code)):
            return 'stage'
        elif self.conn.exists(self.data_reply.format(code)):
            return 'reply'

    def get_cache_name(self, code: str):
        if self.conn.exists(self.data.format(code)):
            return self.data.format(code)
        elif self.conn.exists(self.data_reply.format(code)):
            return self.data_reply.format(code)

    def hget_value(self, code: str, key: str):
        name = self.get_cache_name(code)
        return self.conn.hget(name, key)

    def pop(self, code: str):
        if self.conn.exists(self.data.format(code)):
            return self.pop_stage(code)
        elif self.conn.exists(self.data_reply.format(code)):
            return self.pop_reply(code)

    def remove(self, code: str):
        if self.conn.exists(self.data.format(code)):
            self.remove_stage(code)
        elif self.conn.exists(self.data_reply.format(code)):
            self.remove_reply(code)

    def add_stage(self, code: str):
        if self.has_cache(code):
            data_dict: dict = self._get_stage(code)
            data_dict['rptm'] = int(time.time())
        else:
            data_dict: dict = StageUtils.get_with_time_physic(code)
            data_dict.pop('_id')
            for key, value in data_dict.items():
                if isinstance(value, bool):
                    data_dict[key] = int(value)
            self.conn.sadd(self.hits, code)
            # 全量获取回应的目的在于防止管理员恢复其中已删除回应的骚操作
            replies = StageUtils.get_reply_all_physic(code)
            replies_code = list()
            for reply in replies:
                reply.pop('_id')
                for key, value in reply.items():
                    if isinstance(value, bool):
                        reply[key] = int(value)
                self.conn.hmset(self.data_reply.format(reply.get('code')), reply)
                replies_code.append(reply.get('code'))
                self.conn.sadd(self.hits, reply.get('code'))
            data_dict['replies'] = ",".join(replies_code)
        self.conn.hmset(self.data.format(code), data_dict)
        return data_dict

    def pop_stage(self, code: str):
        name = self.data.format(code)
        if self.has_cache(code):
            data_dict: dict = self.get_stage(code)
            self.conn.srem(self.hits, code)
            for reply in data_dict.get('replies'):
                self.remove_reply(reply.get('code'))
            self.conn.delete(name)
            return data_dict
        else:
            raise Exception(''.join(['缓存', name, '不存在']))

    def remove_stage(self, code: str):
        name = self.data.format(code)
        if self.has_cache(code):
            self.conn.srem(self.hits, code)
            replies = str(self.conn.hget(name, 'replies'), encoding='utf-8').split(',')
            self.conn.delete(name)
            for reply in replies:
                if reply != '':
                    self.remove_reply(reply)
        else:
            print(''.join(['缓存', name, '不存在']))

    def update_hash(self, code: str, key: str, value: any):
        name = self.data.format(code)
        self.conn.hset(name, key, value)

    def get_stage(self, code: str) -> dict:
        values = dict()
        name = self.data.format(code)
        values['code'] = code
        if self.conn.hget(name, 'title') is not None:
            values['title'] = str(self.conn.hget(name, 'title'), encoding='utf-8')
        values['author'] = str(self.conn.hget(name, 'author'), encoding='utf-8')
        values['content'] = str(self.conn.hget(name, 'content'), encoding='utf-8')
        if self.conn.hget(name, 'notes') is not None:
            values['notes'] = str(self.conn.hget(name, 'notes'), encoding='utf-8')
        values['section_code'] = int(self.conn.hget(name, 'section_code'))
        values['is_admin'] = bool(int(self.conn.hget(name, 'is_admin')))
        values['is_sage'] = bool(int(self.conn.hget(name, 'is_sage')))
        values['is_del'] = bool(int(self.conn.hget(name, 'is_del')))
        values['rptm'] = int(self.conn.hget(name, 'rptm'))
        values['date'] = str(self.conn.hget(name, 'date'), encoding='utf-8')
        replies_code = str(self.conn.hget(name, 'replies'), encoding='utf-8').split(',')
        values['replies'] = list()
        for reply_code in replies_code:
            if reply_code != '':
                reply = self.get_reply(reply_code)
                values['replies'].append(reply)
        return values

    def get_stage_and_reply_pagination(self,
                                       code: str = None,
                                       page_size: int = 10,
                                       page_no: int = 1,
                                       is_admin: bool = False,
                                       is_board: bool = False) -> dict:
        values = dict()
        name = self.data.format(code)
        values['code'] = code
        values['author'] = str(self.conn.hget(name, 'author'), encoding='utf-8')
        if self.conn.hget(name, 'title') is not None:
            values['title'] = str(self.conn.hget(name, 'title'), encoding='utf-8')
        values['content'] = str(self.conn.hget(name, 'content'), encoding='utf-8')
        if self.conn.hget(name, 'notes') is not None:
            values['notes'] = str(self.conn.hget(name, 'notes'), encoding='utf-8')
        values['section_code'] = int(self.conn.hget(name, 'section_code'))
        values['is_admin'] = bool(int(self.conn.hget(name, 'is_admin')))
        values['is_sage'] = bool(int(self.conn.hget(name, 'is_sage')))
        values['is_del'] = bool(int(self.conn.hget(name, 'is_del')))
        values['rptm'] = int(self.conn.hget(name, 'rptm'))
        values['date'] = str(self.conn.hget(name, 'date'), encoding='utf-8')
        replies_code = self.get_replies_code(code)
        replies_data = list()
        total = len(replies_code)
        start = max(0, page_size * (page_no - 1))
        end = min(total, page_size * page_no)
        rest = 0
        for reply_code in replies_code[start:end]:
            if reply_code != '':
                reply = self.get_reply(reply_code)
                if reply.get('is_del') is False or is_admin:
                    replies_data.append(reply)
                    continue
            rest += 1
        while rest > 0:
            if end + rest < total:
                start, end = end, end + rest
                rest = 0
                for reply_code in replies_code[start:end]:
                    if reply_code != '':
                        reply = self.get_reply(reply_code)
                        if reply.get('is_del') is False or is_admin:
                            replies_data.append(reply)
                            continue
                    rest += 1
            else:
                break
        replies_data_real = replies_data
        if total > 0:
            if not is_board:
                values['replies'] = {'data': replies_data_real,
                                     'total': total,
                                     'page_has_next': total - page_size * page_no > 0,
                                     'page_num': ceil(total / page_size)}
        else:
            if not is_board:
                values['replies'] = {'data': replies_data_real,
                                     'total': total,
                                     'page_has_next': False,
                                     'page_num': 0}
        if is_board:
            values['replies'] = {'data': replies_data_real, 'total': total}
        return values

    def _get_stage(self, code) -> dict:
        values = dict()
        name = self.data.format(code)
        values['code'] = code
        if self.conn.hget(name, 'title') is not None:
            values['title'] = self.conn.hget(name, 'title')
        values['author'] = self.conn.hget(name, 'author')
        values['content'] = self.conn.hget(name, 'content')
        if self.conn.hget(name, 'notes') is not None:
            values['notes'] = self.conn.hget(name, 'notes')
        values['section_code'] = self.conn.hget(name, 'section_code')
        values['is_admin'] = self.conn.hget(name, 'is_admin')
        values['is_sage'] = self.conn.hget(name, 'is_sage')
        values['is_del'] = self.conn.hget(name, 'is_del')
        values['rptm'] = self.conn.hget(name, 'rptm')
        values['date'] = self.conn.hget(name, 'date')
        values['replies'] = str(self.conn.hget(name, 'replies'), encoding='utf-8')
        return values

    def add_reply(self, code: str, prefix: str, data_dict: dict):
        if self.has_cache(code):
            data_dict: dict = self._get_reply(code)
            print(''.join(['缓存', self.data_reply.format(code), '已存在']))
        else:
            if self.has_cache(prefix):
                data_dict_for_prefix: dict = self._get_stage(prefix)
                data_dict_for_prefix['rptm'] = int(time.time())
                if data_dict_for_prefix['replies'] == '':
                    data_dict_for_prefix['replies'] = code
                else:
                    data_dict_for_prefix['replies'] = ','.join([data_dict_for_prefix['replies'], code])
                data_dict.pop('_id')
                for key, value in data_dict.items():
                    if isinstance(value, bool):
                        data_dict[key] = int(value)
                self.conn.hmset(self.data.format(prefix), data_dict_for_prefix)
                self.conn.hmset(self.data_reply.format(code), data_dict)
                self.conn.sadd(self.hits, code)
            else:
                self.add_stage(prefix)
                data_dict = self.get_reply(code)
        return data_dict

    def pop_reply(self, code: str):
        name = self.data_reply.format(code)
        if self.has_cache(code):
            data_dict: dict = self.get_reply(code)
            self.conn.srem(self.hits, code)
            self.conn.delete(name)
            return data_dict
        else:
            raise Exception(''.join(['缓存', name, '不存在']))

    def remove_reply(self, code: str):
        name = self.data_reply.format(code)
        if self.has_cache(code):
            self.conn.srem(self.hits, code)
            self.conn.delete(name)
        else:
            print(''.join(['缓存', name, '不存在']))

    def update_reply(self, code: str, key: str, value: any):
        name = self.data_reply.format(code)
        self.conn.hset(name, key, value)

    def get_reply(self, code: str) -> dict:
        values = dict()
        name = self.data_reply.format(code)
        values['code'] = code
        if self.conn.hget(name, 'title') is not None:
            values['title'] = str(self.conn.hget(name, 'title') , encoding='utf-8')
        values['prefix'] = str(self.conn.hget(name, 'prefix'), encoding='utf-8')
        values['author'] = str(self.conn.hget(name, 'author'), encoding='utf-8')
        values['content'] = str(self.conn.hget(name, 'content'), encoding='utf-8')
        if self.conn.hget(name, 'notes') is not None:
            values['notes'] = str(self.conn.hget(name, 'notes'), encoding='utf-8')
        values['section_code'] = int(self.conn.hget(name, 'section_code'))
        values['is_admin'] = bool(int(self.conn.hget(name, 'is_admin')))
        values['is_sage'] = bool(int(self.conn.hget(name, 'is_sage')))
        values['is_del'] = bool(int(self.conn.hget(name, 'is_del')))
        values['date'] = str(self.conn.hget(name, 'date'), encoding='utf-8')
        return values

    def _get_reply(self, code) -> dict:
        values = dict()
        name = self.data_reply.format(code)
        values['code'] = code
        if self.conn.hget(name, 'title') is not None:
            values['title'] = self.conn.hget(name, 'title')
        values['prefix'] = self.conn.hget(name, 'prefix')
        values['author'] = self.conn.hget(name, 'author')
        values['content'] = self.conn.hget(name, 'content')
        if self.conn.hget(name, 'notes') is not None:
            values['notes'] = self.conn.hget(name, 'notes')
        values['section_code'] = self.conn.hget(name, 'section_code')
        values['is_admin'] = self.conn.hget(name, 'is_admin')
        values['is_sage'] = self.conn.hget(name, 'is_sage')
        values['is_del'] = self.conn.hget(name, 'is_del')
        values['date'] = self.conn.hget(name, 'date')
        return values

    def get_replies_code(self, code: str) -> List[str]:
        name = self.data.format(code)
        replies_code = str(self.conn.hget(name, 'replies'), encoding='utf-8').split(',')
        replies = list()
        for reply_code in replies_code:
            if reply_code != '':
                replies.append(reply_code)
        return replies

