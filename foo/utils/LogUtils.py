from math import ceil

from foo.client.MongoClient import MongoClient
from foo.conf.config import LOG_TABLE
from foo.conf.config import STAGE_TABLE
import foo.utils.TimeStampUtils as TimeStampUtils

client = MongoClient()
client.set_col(LOG_TABLE)
col = client.get_col()


def add(operator: str, type_nm: str, action: str, object_nm: str, notes: str = None):
    client.set_col(LOG_TABLE)
    if action == "report" and col.find({"operator": operator, "action": action, "object": object_nm}).count() > 0:
        return Exception("重复举报。")
    else:
        query = dict()
        query.setdefault("operator", operator)
        query.setdefault("type_nm", type_nm)
        query.setdefault("action", action)
        query.setdefault("object", object_nm)
        if notes is not None and notes != '':
            query.setdefault("notes", notes)
        query.setdefault("is_del", False)
        client.insert(query)
        return "success"


def delete_one(query: dict):
    try:
        client.set_col(LOG_TABLE)
        col.update(query, {"$set": {"is_del": True}})
    except Exception as err:
        return err


def find(query, projection: dict = None):
    client.set_col(LOG_TABLE)
    if projection is None:
        return col.find(query)
    else:
        return col.find(query, projection)


def find_pagination(query, projection: list = None, page_size: int = 10, page_no: int = 1):
    client.set_col(LOG_TABLE)
    skip = page_size * (page_no - 1)
    logs_iter = client.get_new_pagination(query=query, keys=projection, limit=page_size, skip=skip, is_descending=True)
    logs = logs_iter.next()
    total_list = logs['total']
    if len(total_list) > 0:
        total = total_list[0]["total"]
        page_has_next = total - page_size * page_no > 0
        page_num = ceil(total / page_size)
    else:
        total = 0
        page_has_next = False
        page_num = 0
    dataset = list()
    for data in logs['data']:
        dataset.append(_add_date(data))
    return dataset, page_has_next, page_num, total


def get_report_pagination(operator: str = None, page_size: int = 10, page_no: int = 1):
    query = dict()
    if operator is not None:
        query["operator"] = operator
    query["action"] = "report"
    query["is_del"] = False
    dataset, page_has_next, page_num, total = find_pagination(query=query, page_size=page_size, page_no=page_no)
    for data in dataset:
        if data['type_nm'] == 'stage':
            data['link'] = data['object']
        else:
            client.set_col(STAGE_TABLE)
            stage = client.get_one('code', data['object'])
            data['link'] = stage['prefix']
    return dataset, page_has_next, page_num, total


def get_report_all(operator: str = None):
    query = dict()
    if operator is not None:
        query["operator"] = operator
    query["action"] = "report"
    query["is_del"] = False
    return find(query)


def delete_report(operator: str, object: str):
    query = dict()
    query["operator"] = operator
    query["object"] = object
    query["action"] = "report"
    query["is_del"] = False
    delete_one(query)


def get_admin_pagination(operator: str = None, action: str = None, page_size: int = 10, page_no: int = 1):
    query = dict()
    if operator is not None:
        query["operator"] = operator
    query["type_nm"] = "admin"
    if action is not None:
        query["action"] = action
    query["is_del"] = False
    return find_pagination(query=query, page_size=page_size, page_no=page_no)


def get_admin_all(operator: str = None, action: str = None):
    query = dict()
    if operator is not None:
        query["operator"] = operator
    query["type_nm"] = "admin"
    if action is not None:
        query["action"] = action
    query["is_del"] = False
    return find(query)


def _add_date(logger):
    logger['date'] = TimeStampUtils.get_from_objectid_to_datetime(logger['_id'])
    logger.pop('_id')
    return logger