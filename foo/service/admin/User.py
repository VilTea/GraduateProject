import foo.service.user.BloomFilter4User as bf4user
import foo.utils.UserOperatorUtils as UserOperatorUtils
import foo.utils.UUIDGeneratorUtils as UUIDGeneratorUtils
import foo.utils.LogUtils as LogUtils


def delete(serial: str):
    if bf4user.bloomFilter.contains(serial):
        rev = UserOperatorUtils.delete(serial)
        if isinstance(rev, Exception):
            return rev
        else:
            return True
    else:
        return False


def restore(serial: str):
    if bf4user.bloomFilter.contains(serial):
        rev = UserOperatorUtils.restore(serial)
        if isinstance(rev, Exception):
            return rev
        else:
            return True
    else:
        return False


def new_uid(serial: str, operator: str):
    if bf4user.bloomFilter.contains(serial):
        rev = UserOperatorUtils.new_uid(serial, UUIDGeneratorUtils.get_uuid())
        if isinstance(rev, Exception):
            return rev
        else:
            return True
    else:
        return False


def get_stages(user: str, is_admin: bool = False):
    """
    获取指定用户发言记录
    :param user: 查询普通用户输入序列号；查询管理员用户不经过布隆过滤器，输入昵称。
    :param is_admin:
    :return:
    """
    if is_admin:
        return UserOperatorUtils.get_stage_list(user, is_admin=True)
    else:
        if bf4user.bloomFilter.contains(user):
            rev = UserOperatorUtils.get_stage_list(user)
            return rev
        else:
            return False


def get_user():
    return UserOperatorUtils.get({"is_del": False})


def get_user_deleted():
    return UserOperatorUtils.get({"is_del": True})


switch_actions = {
    "delete": delete,
    "restore": restore,
    "search": get_stages
}

actions_name = {
    "delete": "清退用户",
    "restore": "释放用户"
}


def action(uid: str, arg: str, operator: str):
    serial = UserOperatorUtils.get_serial(uid)
    if isinstance(serial, Exception):
        return serial
    else:
        if arg != "search":
            rev = switch_actions[arg](serial)
            if not isinstance(rev, Exception) and rev:
                LogUtils.add(operator=operator,
                             type_nm="admin",
                             action=actions_name[arg],
                             object_nm=serial)
        else:
            rev = switch_actions[arg](serial)
        return rev

