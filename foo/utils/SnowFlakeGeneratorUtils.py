import time


class SnowFlakeGenerator:

    def __init__(self, data_id=1):
        self.start = int(time.mktime(time.strptime('2020-01-01 00:00:00', "%Y-%m-%d %H:%M:%S")))
        self.last = int(time.time())
        self.count_id = 0
        self.data_id = data_id

    def get_snow_flake_id(self):
        now = int(time.time())
        temp = now - self.start
        # 时间差补零
        if len(str(temp)) < 9:
            supply = '0' * (9 - len(str(temp)))
            temp = supply + str(temp)
        # 序列号
        if now == self.last:
            self.count_id += 1
        else:
            self.count_id = 0
            self.last = now
        # 标识id补零
        if len(str(self.data_id)) < 2:
            supply = '0' * (2 - len(str(self.data_id)))
            self.data_id = supply + str(self.data_id)
        # 序列号已满五位，睡眠1秒
        if self.count_id == 99999:
            time.sleep(1)
        count_id_to_str = str(self.count_id)
        if len(count_id_to_str) < 5:
            supply = "0" * (5 - len(count_id_to_str))
            count_id_to_str = supply + count_id_to_str
        id = str(temp) + str(self.data_id) + count_id_to_str
        return id
