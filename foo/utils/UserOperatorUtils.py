from foo.client.MongoClient import MongoClient
from foo.conf.config import USER_TABLE

import foo.utils.StageUtils as StageUtils


client = MongoClient()
client.set_col(USER_TABLE)
col = client.get_col()


def get(query: dict = None, keys: dict = None):
    client.set_col(USER_TABLE)
    return client.get_new(query, keys)


def get_serial(uid: str):
    client.set_col(USER_TABLE)
    if client.contains_physic("id", uid):
        return client.get_one("id", uid)["serial"]
    else:
        return Exception("查询用户失败，可能是指定用户不存在或已经被删除。")


def update_query(serial: str, query: dict):
    col.update_one({"serial": serial}, query)


def update_set_one(serial: str, key: str, value: any):
    update_query(serial, {"$set": {key: value}})


def delete(serial: str):
    client.set_col(USER_TABLE)
    if client.contains("serial", serial):
        update_set_one(serial, "is_del", True)
    else:
        return Exception("删除用户失败，可能是指定用户不存在或已经被删除。")


def restore(serial: str):
    client.set_col(USER_TABLE)
    if client.contains_physic("serial", serial):
        update_set_one(serial, "is_del", False)
    else:
        return Exception("恢复用户失败，可能是指定用户不存在或已经被物理性删除。")


def new_uid(serial: str, uid: str):
    client.set_col(USER_TABLE)
    if client.contains("serial", serial):
        update_set_one(serial, "uid", uid)
    else:
        return Exception("更新数据失败，可能是指定用户不存在或已经被删除。")


def get_stage_list(user: str, is_admin: bool = False):
    stages = list()
    if is_admin:
        stages = StageUtils.get_stage_by_author(author=user, match=False)
    else:
        client.set_col(USER_TABLE)
        if client.contains_physic("serial", user):
            uid = client.get_one("serial", user)["id"]
            stages = StageUtils.get_stage_by_author(author=uid)
    return stages