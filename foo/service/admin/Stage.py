import foo.utils.StageUtils as StageUtils
import foo.utils.LogUtils as LogUtils
import foo.service.admin.BloomFilter4Admin as bf4admin


action_switch = {
    "sage": StageUtils.sage,
    "de_sage": StageUtils.de_sage,
    "delete": StageUtils.delete,
    "restore": StageUtils.restore
}

action_name = {
    "sage": "sage",
    "de_sage": "取消sage",
    "delete": "删串",
    "restore": "恢复串"
}


def post(admin: str, title: str, author: str, content: str, section_code: int):
    if bf4admin.bloomFilter.contains(admin):
        title = None if not title.strip() else title.strip()
        rev = StageUtils.new_admin(title=title, author=author, prefix=None, content=content, section_code=section_code)
        if isinstance(rev, Exception):
            return rev
        else:
            return True
    else:
        return False


def reply(admin, title, author, content, prefix):
    if bf4admin.bloomFilter.contains(admin):
        section = StageUtils.get_value(prefix, "section_code")
        title = None if not title.strip() else title.strip()
        rev = StageUtils.new_admin(title=title, author=author, prefix=prefix, content=content, section_code=section)
        if isinstance(rev, Exception):
            return rev
        return True
    else:
        return False


def action(arg: str, code: str, operator: str, **kwargs):
    if arg is None or code is None:
        raise Exception("参数为空。")
    else:
        action_switch[arg](code, **kwargs)
        LogUtils.add(operator=operator,
                     type_nm="admin",
                     action=action_name[arg],
                     object_nm=code)


def note(code: str, content: str, operator: str):
    print("admin_stage")
    if content is None:
        return Exception("内容为空。")
    else:
        StageUtils.notes(code, content)
        LogUtils.add(operator=operator,
                     type_nm="admin",
                     action="备注:" + content,
                     object_nm=code)

