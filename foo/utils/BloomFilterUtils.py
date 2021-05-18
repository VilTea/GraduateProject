import murmurhash as mmh

from foo.client.RedisClient import RedisClient
from bitarray import bitarray


class BloomFilterBuilder:

    def __init__(self, bit_size: int):
        bit_array = bitarray(bit_size)
        bit_array.setall(0)

        self.redis_client = RedisClient()
        self.bit_size = bit_size
        self.bit_array = bit_array

    def add(self, elem):
        point_list = self.get_positions(elem, 8)
        for bit in point_list:
            self.bit_array[bit] = 1

    def contains(self, elem):
        point_list = self.get_positions(elem, 8)
        result = True
        for bit in point_list:
            result = result and self.bit_array[bit]
        return result

    def get_positions(self, elem, size):
        points = [mmh.hash(elem, 41 + i) % self.bit_size for i in range(size)]
        return points

    def upload(self, key: str):
        self.redis_client.set_one(key, self.bit_array.tobytes())

    def initialize(self):
        bit_array = bitarray(self.bit_size)
        bit_array.setall(0)

        self.bit_array = bit_array


class BloomFilterReader:

    def __init__(self, key: str):
        try:
            redis_client = RedisClient()
            bits = redis_client.get(key)
            if bits is not None:
                self.key = key
                bit_array = bitarray()
                bit_array.frombytes(bits)
                self.redis_client = redis_client
                self.bit_array = bit_array
                self.bit_size = bit_array.length()
            else:
                raise Exception("There is not " + key)
        except Exception:
            raise Exception

    def add(self, elem):
        point_list = self.get_positions(elem, 8)
        for bit in point_list:
            self.bit_array[bit] = 1

    def contains(self, elem):
        point_list = self.get_positions(elem, 8)
        result = True
        for bit in point_list:
            result = result and self.bit_array[bit]
        return result

    def get_positions(self, elem, size):
        points = [mmh.hash(elem, 41 + i) % self.bit_size for i in range(size)]
        return points

    def upload(self):
        self.redis_client.set_one(self.key, self.bit_array.tobytes())

    def refresh(self):
        bit_array: bitarray = bitarray()
        bit_array.frombytes(self.redis_client.get(self.key))

        self.bit_size = len(bit_array)
        self.bit_array = bit_array

    def initialize(self):
        bit_array = bitarray(self.bit_size)
        bit_array.setall(0)

        self.bit_array = bit_array
