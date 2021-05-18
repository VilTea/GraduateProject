from typing import Optional, List

import pymongo
import logging
import foo.conf.config as config


class MongoClient:
    def __init__(self):
        self.logger = logging.getLogger("client.mongo")
        try:
            client = pymongo.MongoClient(host=config.MONGODB_HOST,
                                         port=config.MONGODB_PORT,
                                         username=config.MONGODB_USERNAME,
                                         password=config.MONGODB_PASSWORD,
                                         authSource="admin")
            self._client = client
            db = client[config.MONGODB_DBNAME]
            self._db = db
            self.col: pymongo.collection.Collection = None
        except Exception:
            self.logger.info(Exception)
            raise Exception

    def __new__(cls, *args, **kwargs):
        """
        单例模式
        """
        if not hasattr(cls, "_instance"):
            cls.__instance = super(MongoClient, cls).__new__(cls)
        return cls.__instance

    def set_col(self, col: str):
        if col in self._db.collection_names():
            self.col = self._db.get_collection(col)
        else:
            self.col = None
            context = "[MongoClient]There is not " + col
            self.logger.info(context)
            raise Exception(context)

    def get_col(self) -> pymongo.collection.Collection:
        return self.col

    def get_col_list(self) -> list:
        return self._db.collection_names()

    def get_new(self, query: dict = None, keys: list = None, sorts: List[tuple] = None, is_reverser=True) -> pymongo.cursor.Cursor:
        if self.col is None:
            raise Exception("[MongoClient]col is None")
        filter_dict = {key: 1 for key in keys} if keys is not None else None
        sorts = list() if sorts is None else sorts
        if is_reverser:
            sorts.append(('_id', pymongo.DESCENDING))
        else:
            sorts.append(('_id', pymongo.ASCENDING))
        return self.col.find(query, filter_dict, sort=[('_id', pymongo.DESCENDING)]) \
            if sorts is None else self.col.find(query, filter_dict, sort=sorts)

    def get_new_pagination(self, query: dict = None, keys: list = None, sorts: dict = None,
                           limit: int = 10, skip: int = 1, is_descending: bool = False) -> pymongo.cursor.Cursor:
        """
        is_descending: 是否倒序
        """
        if self.col is None:
            raise Exception("[MongoClient]col is None")
        query_list = list()
        for key, value in query.items():
            query_list.append({key: value})
        match = {"$match": {"$and": query_list}}
        project = None
        if keys is not None:
            filter_dict = {key: 1 for key in keys}
            project = {"$project": filter_dict}
        sorts = dict() if sorts is None else sorts
        if is_descending:
            sorts.setdefault('_id', pymongo.DESCENDING)
        else:
            sorts.setdefault('_id', pymongo.ASCENDING)
        sorts = {"$sort": sorts}
        facet = {"$facet": {
            "total": [{"$count": "total"}],
            "data": [
                {"$skip": skip},
                {"$limit": limit}
            ]
        }}
        if project is not None:
            pipeline = [match, sorts, project, facet]
        else:
            pipeline = [match, sorts, facet]
        return self.col.aggregate(pipeline=pipeline)

    def get_new_one(self, query: dict = None, keys: list = None) -> Optional[pymongo.cursor.Cursor]:
        if self.col is None:
            raise Exception("[MongoClient]col is None")
        filter_dict = {key: 1 for key in keys} if keys is not None else None
        return self.col.find_one(query, filter_dict, sort=[('_id', pymongo.DESCENDING)])

    def get_one(self, key, value):
        if self.col is None:
            raise Exception("[MongoClient]col is None")
        return self.col.find_one({key: value})

    def contains(self, key, value) -> bool:
        if self.col is None:
            raise Exception("[MongoClient]col is None")
        tmp = self.col.find({"is_del": {"$exists": True}})
        if tmp.count() > 0:
            if self.col.find({key: value, "is_del": False}).count() > 0:
                return True
        elif self.col.find_one({key: value}) is not None:
            return True
        return False

    def contains_physic(self, key, value) -> bool:
        if self.col is None:
            raise Exception("[MongoClient]col is None")
        tmp = self.col.find({"is_del": {"$exists": True}})
        if tmp.count() > 0:
            if self.col.find({key: value}).count() > 0:
                return True
        elif self.col.find_one({key: value}) is not None:
            return True
        return False

    def insert(self, insert_dict: dict):
        if self.col is None:
            self.logger.info("[MongoClient]col is None")
            raise Exception("[MongoClient]col is None")
        if isinstance(insert_dict, dict):
            try:
                self.col.insert(insert_dict)
            except Exception:
                self.logger.info(Exception)
                raise Exception
        else:
            self.logger.info("[MongoClient]Error param insert_dict. It should be a dict.")
            raise Exception("[MongoClient]Error param insert_dict. It should be a dict.")
