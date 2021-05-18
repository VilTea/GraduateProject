import time


offset = 8 * 3600


def get_from_objectid(objectid):
    result = 0
    try:
        result = time.mktime(objectid.generation_time.timetuple())
    except Exception:
        pass
    return result


def get_from_objectid_to_datetime(obcjectid):
    result = get_from_objectid(obcjectid)
    result = time.localtime(result + offset)
    # result = time.gmtime(result)
    result = time.strftime("%Y-%m-%d %H:%M:%S", result)
    return result