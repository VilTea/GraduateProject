from foo.client.MongoClient import MongoClient

import foo.conf.config as config
import foo.service.user.BloomFilter4User as bf4user
import foo.utils.UUIDGeneratorUtils as uuid
import foo.utils.SnowFlakeGeneratorUtils as sf


def register(uid, serial_id, ip_addr):
    client = MongoClient()
    client.set_col(config.USER_TABLE)
    client.insert({"id": uid, "serial": serial_id, "ip": ip_addr, "is_del": False})
    bf4user.bloomFilter.add(serial_id)
    bf4user.upload()


def get():
    uid = uuid.get_uuid()
    serial_id = sf.SnowFlakeGenerator().get_snow_flake_id()
    return uid, serial_id
