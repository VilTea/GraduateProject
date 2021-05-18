from foo.service.admin.BloomFilter4Admin import bloomFilter as bf4admin

import foo.utils.LogUtils as LogUtils


def get_report(reader: str, operator: str = None, page_size: int = 15, page_no: int = 1):
    if bf4admin.contains(reader):
        return LogUtils.get_report_pagination(operator=operator, page_size=page_size, page_no=page_no)
    else:
        raise Exception("非法操作。")


def get_admin_log(reader: str, operator: str = None, action: str = None, page_size: int = 15, page_no: int = 1):
    if bf4admin.contains(reader):
        return LogUtils.get_admin_pagination(operator=operator, action=action, page_size=page_size, page_no=page_no)
    else:
        raise Exception("非法操作。")


def delete_report_log(reader: str, operator: str = None, object_str: str = None):
    if bf4admin.contains(reader):
        return LogUtils.delete_one({'operator': operator, 'object': object_str})
    else:
        raise Exception("非法操作。")