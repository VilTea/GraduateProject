from typing import Optional, List
from foo.conf.config import STAGE_TABLE
from foo.client.MongoClient import MongoClient
from foo.cache.normalQueue import cache_NQ
from foo.cache.temporaryHotCache import cache_THC
from math import ceil

import time
import foo.utils.LogUtils as LogUtils
import foo.utils.TimeStampUtils as TimeStampUtils

client = MongoClient()
client.set_col(STAGE_TABLE)
col = client.get_col()


def report(code: str, serial: str, notes: str = None):
    client.set_col(STAGE_TABLE)
    if client.contains("code", code):
        if 'prefix' in client.get_one("code", code):
            type_nm = 'reply'
        else:
            type_nm = 'stage'
        rev = LogUtils.add(operator=serial,
                           type_nm=type_nm,
                           action="report",
                           object_nm=code,
                           notes=notes)
        return rev
    else:
        return Exception("举报的串号已被删除。")


def new(title: str, author: str, prefix: Optional[str], content: str, section_code: int):
    if content is None or len(content) == 0:
        return Exception("内容为空")
    client.set_col(STAGE_TABLE)
    if prefix is not None:
        if cache_NQ.has_cache(prefix):
            if cache_NQ.get_stage(prefix).get('is_del'):
                return Exception("请求非法。")
            elif cache_NQ.get_stage(prefix).get('is_sage'):
                return Exception("回复的串已经被sage。")
        else:
            if not client.contains("code", prefix):
                return Exception("请求非法。")
            elif client.get_one("code", prefix)["is_sage"]:
                return Exception("回复的串已经被sage。")
    code_str = client.get_new_one(query={}, keys=["code"])
    code = '{:0>8d}'.format(int(code_str["code"]) + 1 if code_str is not None else 0)
    query = dict()
    query.setdefault("code", code)
    query.setdefault("title", title) if title is not None else None
    query.setdefault("author", author)
    query.setdefault("prefix", prefix) if prefix is not None else None
    query.setdefault("content", content)
    query.setdefault("section_code", int(section_code))
    query.setdefault("is_admin", False)
    query.setdefault("is_sage", False)
    query.setdefault("is_del", False)
    if prefix is not None:
        col.insert_one(query)
        col.update_one({"code": prefix}, {"$set": {"rptm": int(time.time())}})
        cache_NQ.push_reply(code, prefix, _add_date_now(query))
    else:
        query.setdefault("rptm", int(time.time()))
        col.insert_one(query)
        cache_NQ.push(code)
        cache_NQ.incr_section_total(section_code)
    return code


def new_admin(title: str, author: str, prefix: Optional[str], content: str, section_code: int):
    if content is None or len(content) == 0:
        return Exception("内容为空")
    client.set_col(STAGE_TABLE)
    if prefix is not None:
        if cache_NQ.has_cache(prefix):
            if cache_NQ.get_stage(prefix).get('is_del'):
                return Exception("回复的串已经被删除。为了缓存健康，拒绝骚操作。")
        else:
            if client.get_one("code", prefix)["is_del"]:
                return Exception("回复的串已经被删除。为了缓存健康，拒绝骚操作。")
    code_str = client.get_new_one(query={}, keys=["code"])
    code = '{:0>8d}'.format(int(code_str["code"]) + 1 if code_str is not None else 0)
    query = dict()
    query.setdefault("code", code)
    query.setdefault("title", title) if title is not None else None
    query.setdefault("author", author)
    query.setdefault("prefix", prefix) if prefix is not None else None
    query.setdefault("content", content)
    query.setdefault("section_code", int(section_code))
    query.setdefault("is_admin", True)
    query.setdefault("is_sage", False)
    query.setdefault("is_del", False)
    if prefix is not None:
        col.insert_one(query)
        col.update_one({"code": prefix}, {"$set": {"rptm": int(time.time())}})
        cache_NQ.push_reply(code, prefix, _add_date_now(query))
    else:
        query.setdefault("rptm", int(time.time()))
        col.insert_one(query)
        cache_NQ.push(code)
        cache_NQ.incr_section_total(section_code)
    return code


def sage(code: str):
    client.set_col(STAGE_TABLE)
    if client.contains_physic("code", code):
        col.update_one({"code": code}, {"$set": {"is_sage": True}})
        if cache_NQ.has_cache(code):
            cache_NQ.update_hash(code, 'is_sage', 1)
        elif cache_THC.has_cache(code):
            cache_THC.update_hash(code, 'is_sage', 1)
    else:
        raise "There is not " + code


def de_sage(code: str):
    client.set_col(STAGE_TABLE)
    if client.contains_physic("code", code):
        col.update_one({"code": code}, {"$set": {"is_sage": False}})
        if cache_NQ.has_cache(code):
            cache_NQ.update_hash(code, 'is_sage', 0)
        elif cache_THC.has_cache(code):
            cache_THC.update_hash(code, 'is_sage', 0)
    else:
        raise "There is not " + code


def admin(code: str):
    client.set_col(STAGE_TABLE)
    if client.contains("code", code):
        col.update_one({"code": code}, {"$set": {"is_admin": True}})
    else:
        raise "There is not " + code


def delete(code: str, is_cache_decr: bool = False, section_code: str = None):
    client.set_col(STAGE_TABLE)
    if client.contains("code", code):
        col.update_one({"code": code}, {"$set": {"is_del": True}})
        if is_cache_decr:
            cache_NQ.decr_section_total(section_code)
        if cache_NQ.has_cache(code):
            cache_NQ.soft_del(code)
        if cache_THC.has_cache(code):
            cache_THC.soft_del(code)
    else:
        raise "There is not " + code


def restore(code: str, is_cache_incr: bool = False, section_code: str = None):
    client.set_col(STAGE_TABLE)
    if client.contains_physic("code", code):
        col.update_one({"code": code}, {"$set": {"is_del": False}})
        if is_cache_incr:
            cache_NQ.incr_section_total(section_code)
        if cache_NQ.has_cache(code):
            cache_NQ.soft_restore(code)
        if cache_THC.has_cache(code):
            cache_THC.soft_restore(code)
    else:
        raise "There is not " + code


# 弃案，不再存储后继串号
# def set_last(code: str, last: str):
#     if client.contains("code", code):
#         col.update_one({"code": code}, {"$set": {"last": last}})
#     else:
#         raise "There is not " + code


def notes(code: str, notes: str):
    client.set_col(STAGE_TABLE)
    if client.contains_physic("code", code):
        if notes is None or notes == "":
            print(1)
            col.update_one({"code": code}, {"$unset": {"notes": notes}})
        else:
            print(2)
            col.update_one({"code": code}, {"$set": {"notes": notes}})
        if cache_NQ.has_cache(code):
            cache_NQ.notes(code, notes)
        elif cache_THC.has_cache(code):
            cache_THC.notes(code, notes)
    else:
        raise "There is not " + code


def get_value(code: str, key: str) -> any:
    client.set_col(STAGE_TABLE)
    if client.contains_physic("code", code):
        stage = col.find_one({"code": code}, {key: 1})
        return stage[key]
    else:
        raise "There is not " + code


def get_with_time(code, **kwargs):
    while True:
        if cache_NQ.has_cache(code):
            return cache_NQ.get_stage_and_reply_pagination(code, **kwargs)
        elif cache_THC.ask(code):
            if cache_THC.has_cache(code):
                return cache_THC.get(code, **kwargs)
            client.set_col(STAGE_TABLE)
            if client.contains_physic("code", code):
                stage = col.find_one({"code": code})
                return _add_date(stage)
            else:
                raise 'There is not ' + code
        else:
            time.sleep(200)


def get_with_time_physic(code):
    client.set_col(STAGE_TABLE)
    if client.contains_physic("code", code):
        stage = col.find_one({"code": code})
        return _add_date(stage)
    else:
        return {}


def get_topics_with_time(section: int = None, is_admin: bool = False, page_size: int = 10, page_no: int = 1,
                         has_reply: bool = True):
    skip = page_size * (page_no - 1)
    if not is_admin and cache_NQ.has_section_total(section):
        total = cache_NQ.get_section_total(section)
        if total == 0:
            topics = []
            page_has_next = False
            page_num = 0
        else:
            cache_dict = cache_NQ.get_queue_data(section, page_size, skip)
            topics: list = cache_dict['data']
            page_has_next = total - page_size * page_no > 0
            page_num = ceil(total / page_size)
            rest = cache_dict.get('rest')
            ext = 0
            for index, topic in enumerate(topics):
                if topic.get('is_del') is True:
                    ext += 1
                    topics.pop(index)
            if ext > 0 and rest <= 0:
                cache_tmp = cache_NQ.get_queue_data(section, ext, skip + page_size)
                rest += cache_tmp.get('rest')
                topics += cache_tmp.get('data')
            else:
                rest += ext
            for topic in topics:
                topic["replies_count"] = len(topic['replies'])
                topic["replies"] = topic.get('replies')[-5:]
            if rest > 0 and total > skip + page_size - rest:
                limit = rest
                skip = skip + page_size - rest
                client.set_col(STAGE_TABLE)
                sorts = {"rptm": -1}
                gifts = client.get_new_pagination(query={"is_del": False, "prefix": {"$exists": False}},
                                                  sorts=sorts,
                                                  limit=limit,
                                                  skip=skip) if section is None \
                    else client.get_new_pagination(query={"is_del": False,
                                                          "section_code": section,
                                                          "prefix": {"$exists": False}},
                                                   sorts=sorts,
                                                   limit=limit,
                                                   skip=skip)
                gifts = gifts.next()
                topics_rest = list()
                for topic in gifts["data"]:
                    topics_rest.append(_add_date(topic))
                if has_reply:
                    for topic in topics_rest:
                        replies = get_reply(topic["code"], is_admin, page_size=5, is_board=True)
                        topic["replies"] = replies["data"]
                        topic["replies_count"] = replies["total"]
                topics += topics_rest
    else:
        client.set_col(STAGE_TABLE)
        sorts = {"rptm": -1}
        if is_admin:
            gifts = client.get_new_pagination(query={"prefix": {"$exists": False}},
                                              sorts=sorts,
                                              limit=page_size,
                                              skip=skip) if section is None \
                else client.get_new_pagination(query={"section_code": section, "prefix": {"$exists": False}},
                                               sorts=sorts,
                                               limit=page_size,
                                               skip=skip)
        else:
            gifts = client.get_new_pagination(query={"is_del": False, "prefix": {"$exists": False}},
                                              sorts=sorts,
                                              limit=page_size,
                                              skip=skip) if section is None \
                else client.get_new_pagination(query={"is_del": False,
                                                      "section_code": section,
                                                      "prefix": {"$exists": False}},
                                               sorts=sorts,
                                               limit=page_size,
                                               skip=skip)
        topics = list()
        gifts = gifts.next()
        total_list: list = gifts["total"]
        if len(total_list) > 0:
            total = total_list[0]["total"]
            page_has_next = total - page_size * page_no > 0
            page_num = ceil(total / page_size)
            if not is_admin:
                cache_NQ.set_section_total(section, total)
        else:
            page_has_next = False
            page_num = 0
            cache_NQ.set_section_total(section, 0)
        for topic in gifts["data"]:
            if has_reply:
                replies = get_reply(topic["code"], is_admin, page_size=5, is_board=True)
                topic["replies"] = replies["data"]
                topic["replies_count"] = replies["total"]
            topics.append(_add_date(topic))
        # if not has_reply:
        #     for topic in topics[::-1]:
        #         cache_NQ.push(topic['code'])
    return topics, page_has_next, page_num


def get_stage_by_author(author: str, match=True):
    client.set_col(STAGE_TABLE)
    if match:
        gifts = client.get_new(query={"author": author})
    else:
        gifts = client.get_new(query={"author": {"$regex": author}})
    if gifts is not None:
        stages = [None] * gifts.count()
        for no, stage in enumerate(gifts):
            stages[no] = _add_date(stage)
        return stages
    else:
        return Exception("没有找到指定用户的发言记录。")


def get_stage_by_content(key: str):
    client.set_col(STAGE_TABLE)
    gifts = client.get_new(query={"content": {"$regex": key}})
    if gifts.count() > 0:
        stages = [None] * gifts.count()
        for no, stage in enumerate(gifts):
            stages[no] = _add_date(stage)
        return stages
    else:
        return Exception("没有匹配到相关内容。")


def get_reply(code: str, is_admin: bool = False, page_size=10, page_no=1, is_board: bool = False):
    client.set_col(STAGE_TABLE)
    skip = page_size * (page_no - 1)
    if client.contains_physic("code", code):
        topic = col.find_one({"code": code})
        if is_admin:
            gifts = client.get_new_pagination(query={"prefix": code},
                                              limit=page_size,
                                              skip=skip,
                                              is_descending=is_board)
            gifts = gifts.next()
            stages = gifts['data']
            # stages = col.find({"prefix": code})
            result = list()
            for stage in stages:
                result.append(_add_date(stage))
            # return result
        else:
            if topic["is_del"] is False:
                gifts = client.get_new_pagination(query={"prefix": code, "is_del": False},
                                                  limit=page_size,
                                                  skip=skip,
                                                  is_descending=is_board)
                gifts = gifts.next()
                stages = gifts['data']
                # stages = col.find({"prefix": code, "is_del": False})
                result = list()
                for stage in stages:
                    result.append(_add_date(stage))
                # return result
            else:
                raise Exception("该主题已经被删除")
        total_list: list = gifts.get('total')
        if len(total_list) > 0:
            if not is_board:
                page_has_next = gifts["total"][0]["total"] - page_size * page_no > 0
                page_num = ceil(gifts["total"][0]["total"] / page_size)
            total = gifts["total"][0]["total"]
        else:
            if not is_board:
                page_has_next = False
                page_num = 0
            total = 0
        if is_board:
            return {"data": result[::-1], "total": total}
        else:
            return {"data": result, "page_has_next": page_has_next, "page_num": page_num, "total": total}
    else:
        raise Exception("There is not " + code)


def get_reply_all_physic(code: str) -> List[dict]:
    client.set_col(STAGE_TABLE)
    if client.contains_physic("code", code):
        topic = col.find_one({"code": code})
        if topic["is_del"] is False:
            gifts = client.get_new(query={"prefix": code}, is_reverser=False)
            result = list()
            for reply in gifts:
                result.append(_add_date(reply))
                # return result
            return result
        else:
            raise Exception("该主题已经被删除")
    else:
        raise Exception("There is not " + code)


def get_reply_code_list_physic(code: str) -> List[str]:
    client.set_col(STAGE_TABLE)
    if client.contains_physic("code", code):
        topic = col.find_one({"code": code})
        if topic["is_del"] is False:
            gifts = client.get_new(query={"prefix": code}, keys=['code'], is_reverser=False)
            result = list()
            for reply in gifts:
                result.append(reply['code'])
            return result
        else:
            raise Exception("该主题已经被删除")
    else:
        raise Exception("There is not " + code)


def get_prefix(code: str):
    client.set_col(STAGE_TABLE)
    if client.contains_physic("code", code):
        tmp: dict = client.get_one("code", code)
        if "prefix" in tmp:
            return tmp.get("prefix")
        else:
            return code
    else:
        raise Exception("There is not " + code)


def _add_date(stage):
    stage['date'] = TimeStampUtils.get_from_objectid_to_datetime(stage['_id'])
    return stage


def _add_date_now(stage):
    stage['date'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    return stage