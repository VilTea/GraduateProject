from foo.client.MongoClient import MongoClient
from foo.conf.config import SECTION_TABLE

client = MongoClient()
client.set_col(SECTION_TABLE)
col = client.get_col()


def get_section_list():
    client.set_col(SECTION_TABLE)
    cursor = col.find({"is_hidden": False})
    res = dict()
    for items in cursor:
        if "notes" in items:
            res.setdefault(items['code'], {"name": items['name'], "notes": items['notes']})
        else:
            res.setdefault(items['code'], {"name": items['name']})
    return res