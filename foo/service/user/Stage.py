import foo.utils.StageUtils as Stage
import foo.service.user.BloomFilter4User as bf4user
from foo.client.MongoClient import MongoClient
from foo.conf.config import USER_TABLE


mongo_client = MongoClient()


def report(serial: str, code: str):
    if bf4user.bloomFilter.contains(serial):
        rev = Stage.report(serial, code)
        if isinstance(rev, Exception):
            return rev
        else:
            return True
    else:
        return False


def post(serial, title, author, content, section_code):
    if bf4user.bloomFilter.contains(serial):
        mongo_client.set_col(USER_TABLE)
        if mongo_client.contains('serial', serial):
            title = None if not title.strip() else title.strip()
            rev = Stage.new(title=title, author=author, prefix=None, content=content, section_code=section_code)
        else:
            rev = Exception("你已被清退，如有疑问，请联系管理员。")
        if isinstance(rev, Exception):
            return rev
        return True
    else:
        return False


def reply(serial, title, author, content, prefix):
    if bf4user.bloomFilter.contains(serial):
        mongo_client.set_col(USER_TABLE)
        if mongo_client.contains('serial', serial):
            section = Stage.get_value(prefix, "section_code")
            title = None if not title.strip() else title.strip()
            rev = Stage.new(title=title, author=author, prefix=prefix, content=content, section_code=section)
        else:
            rev = Exception("你已被清退，如有疑问，请联系管理员。")
        if isinstance(rev, Exception):
            return rev
        return True
    else:
        return False


def search(key: str):
    return Stage.get_stage_by_content(key)
