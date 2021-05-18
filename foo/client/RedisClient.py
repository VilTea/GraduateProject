import redis
import foo.conf.config as config


class RedisClient:

    def __init__(self):
        pool = redis.ConnectionPool(host=config.REDIS_HOST,
                                    port=config.REDIS_PORT,
                                    decode_responses=False)
        r = redis.StrictRedis(connection_pool=pool)
        # r = redis.Redis(connection_pool=pool)
        self._client = r
        self._pool = pool

    def __new__(cls, *args, **kwargs):
        """
        单例模式
        """
        if not hasattr(cls, "_instance"):
            cls.__instance = super(RedisClient, cls).__new__(cls)
        return cls.__instance

    def get(self, key: str):
        return self._client.get(key)

    def set_one(self, key, value):
        self._client.set(key, value)

    def set(self, query: dict):
        for key, value in query.items():
            self._client.set(key, value)

    def delete(self, key: str):
        self._client.delete(key)

    def get_client(self):
        """
        特殊业务场景
        :return: redis.StrictRedis
        """
        return self._client

    # def close(self):
    #     self._client.close()
    #
    # def open(self):
    #     self._client = redis.StrictRedis(connection_pool=self._pool)
