import os
import json
import random

from PIL import Image
from foo.client.MongoClient import MongoClient

import matplotlib.pyplot as plt
import foo.conf.config as config
import foo.service.admin.Login as admin
import foo.utils.TimeStampUtils as TimeStampUtils
import foo.service.user.Stage as Post
import foo.service.user.BloomFilter4User as bf4user
import foo.utils.CaptchaUtils as CaptchaUtils
import foo.utils.StageUtils as Stage
import foo.utils.LogUtils as LogUtils
import foo.service.admin.User as admin_user
import foo.service.admin.Logger as admin_log
from foo.cache.normalQueue import normalCacheQueue, cache_NQ


def main():
    # mongo_client = MongoClient()
    # mongo_client.set_col('stage')
    # print(mongo_client.get_one('code', '00000026'))
    # tmp = dict(zip(['data', 'next', 'num', 'total'], admin_log.get_admin_log('admin')))
    # print(tmp.get('data'))
    # print(json.dumps(tmp))
    # replies = Stage.get_reply_all("00000018")
    # print([reply.get('code') for reply in replies])
    cache_NQ.refresh()
    # cache_NQ.add_stage("00000018")
    # data = cache_NQ.get_stage("00000000")
    # print(data.get('replies')[-5:])
    # tmp = cache_NQ
    # # tmp.push('00000018')
    # # r = tmp.get_stage('00000018')
    # # print(tmp.has_stage('00000018'), r)
    # # print(r.get('section_code'))
    # # print("_".join(['NQ', '00000018', str(0)]))
    # # print(tmp.get_queue_data(limit=5, skip=0))
    # # print(tmp.get_queue(limit=5, skip=0))
    # # print(int(tmp.conn.hget('NQ_Data_00000045', 'is_admin')) + 1)
    # tmp.refresh()

    # print(type(config.MONGODB_CONFIG), config.MONGODB_CONFIG)
    # client = MongoClient()
    # col_list = client.get_col_list()
    # print(col_list)
    # client.set_col("user")
    # # col = client.get_col()
    # rest = client.get_new_one()
    # print(rest)
    # client.set_col("stage")
    # gifts = client.get_new({"section_code": 0, "is_del": False})
    # positions = dict()
    # topics = list()
    # count = 0
    # for stage in gifts:
    #     # print(stage)
    #     if stage["prefix"] is not None:
    #         client.set_col('stage')
    #         if client.contains("code", stage["prefix"]):
    #             if stage["prefix"] not in positions:
    #                 topics.append(None)
    #                 positions.setdefault(stage["prefix"], count)
    #                 print(count, stage["prefix"], stage["code"])
    #                 count += 1
    #     else:
    #         if stage["code"] in positions:
    #             topics[positions[stage["code"]]] = stage
    #             print("get", stage["code"], positions[stage["code"]])
    #         else:
    #             topics.append(stage)
    #             count += 1
    #             print(stage["code"], len(topics) - 1)
    # for topic in topics:
    #     print(topic)
    # print(positions)
    # # bf4user.refresh()
    # # bf4user.upload()
    # print(bf4user.bloomFilter.contains("0392273800100001"))
    # print(admin_user.get_stages("0389537180100001"))
    # print(admin_user.get_stages("admin", is_admin=True))
    # print(admin_user.get_stages("God", is_admin=True))
    # print(admin_user.action("f61ef49090ab11eb92ceb4749f8f3873", "search"))
    # # img_list = os.listdir(config.ROOT_PATH + "\\static\\captcha")
    # # img = img_list[random.randint(0, len(img_list))]
    # # print(os.path.join(config.ROOT_PATH + "\\static\\captcha", img))
    # # image = Image.open(os.path.join(config.ROOT_PATH + "\\static\\captcha", img))
    # # plt.imshow(image)
    # # plt.show()
    # # Post.post("test", uid, "testtesttest", 0)
    # # code_str = client.get_new_one(query={}, keys=["code"])
    # # print(code_str)
    # # code = int(code_str["code"]) + 1 if code_str is not None else 0
    # # print(code)
    # # print(Stage.get_topics_with_time(0))
    # # bf4user.refresh()
    # # bf4user.upload()
    # # print(Post.post(serial="0392273800100001", title=None, author="f61ef49090ab11eb92ceb4749f8f3873",
    # #                 content="人， 是会思考的芦苇", section_code=0))
    # # Post.reply(serial="0392273800100001",
    # #            title=None,
    # #            author="f61ef49090ab11eb92ceb4749f8f3873",
    # #            content="——帕斯卡",
    # #            prefix="00000000")
    # # print(Stage.get_list_with_time(0))


if __name__ == "__main__":
    main()
