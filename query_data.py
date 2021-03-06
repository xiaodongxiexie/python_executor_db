# -*- coding: utf-8 -*-
# @Author: xiaodong
# @Date  : 2020/4/3


from sqlalchemy import Table
from sqlalchemy import MetaData
from sqlalchemy.orm import Session, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import PrimaryKeyConstraint


_s = sessionmaker(bind="<your-engine-url>", autocommit=False, autoflush=True, expire_on_commit=True, )
_session = scoped_session(_s)

"""
from pprint import pprint

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

Base     = declarative_base()
metadata = Base.metadata
engine   = create_engine("<your-engine-url>")
session  = scoped_session(sessionmaker(engine, autocommit=False, autoflush=True))

Base.query = session.query_property()
Base.to_dict = lambda self: {obj: getattr(self, obj) for obj in self.__class__.__table__.columns.keys()}
Base.show = lambda self: pprint(self.to_dict())
"""


class ModelMixin(object):

    query = _session.query_property()

    def delete(self):
        _session.delete(self)
        _session.comimt()

    def save(self):
        _session.add(self)
        _session.commit()

    def to_dict(self):
        return {
            obj: getattr(self, obj)
            for obj in self.__class__.__table__.columns.keys()
        }

    
class Query(object):

    def __init__(self, url: str):
        """
        :param url: 符合sqlalchemy 中create_engine 即可
        """

        self.engine = create_engine(url)
        self.session = Session(self.engine, autocommit=False, autoflush=False)

    def build_query(self, table_name: str, schema: str = None):
        """

        :param table_name: 需要操作的表名
        :param schema:  比如表名需要层级选择==> schema.table_name
        :return:
        """
        table = Table(table_name,
                      MetaData(self.engine),
                      schema=schema,
                      autoload=True,
                      autoload_with=self.engine)
        return table

    def build_crud(self, table_name: str, primary_keys: list, schema: str = None):
        """
        当读入数据中无主键时可以通过此种方式伪造一个，支持crud操作，如果仅需要查数据，
        使用上面的build_query 即可，
        不过，如果伪造的主键在实际表中并不起到主键作用时，查询结果为多个时会异常返回为单个！
        :param table_name:
        :param primary_keys: 可迭代即可，当伪主键一个时，也需要放到列表中
        :param schema:
        :return:
        """
        engine = self.engine
        Base = declarative_base(engine)

        primary_keys = ",".join([f"__table__.c.{k}" for k in primary_keys])
        code = f"""
class {table_name}(Base):
        __table__ = Table("{table_name}", MetaData(engine), autoload=True, schema={schema})
        __mapper_args__ = {{"primary_key": [{primary_keys}]}}
                    """
        print(code)
        r = {}
        exec(code, {"engine": engine, "Table": Table, "Base": Base, "MetaData": MetaData}, r)
        r = r.pop(table_name)

        return r

    def _build_crud(self, table_name: str, schema: str = None):
        """
        当查询的表有定义主键时，可以用这个~
        :param table_name:
        :param schema:
        :return:
        """
        Base = declarative_base(self.engine)

        table = type(table_name,
                     (Base,),
                     {"__table__": Table(table_name,
                                         MetaData(self.engine),
                                         autoload=True,
                                         schema=schema)}
                     )

        """table.__table__.column.keys()"""
        return table

    def __build_crud(self, table_name: str, schema: str = None):
        """

        :param table_name: 需要操作的表名
        :param schema:  比如表名需要层级选择==> schema.table_name
        :return:
        """
        base = automap_base()
        base.prepare(self.engine, reflect=True, schema=schema)
        table = getattr(base.classes, table_name)
        return table

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()



if __name__ == '__main__':
    sqlite_url = "sqlite:///data/dbs/movies.db"

    with Query(sqlite_url) as q:
        session = q.session
        table = q.build_crud("links", ["movieId", "imdbId"])
        table2 = q.build_query("links")

        # 由于将movieId， imdbId 设置为伪主键，因此，如表中有此两个值相同的，将只查出一个来。。。
        print(session.query(table).filter(table.movieId == 1).all())

        session.add(table(movieId=1, imdbId=2, tmdbId=3))
        session.commit()

        print(session.query(table).filter(table.movieId == 1).all())

        session.add(table(movieId=1, imdbId=2, tmdbId=3))
        session.commit()
        # 虽然查表成功，但是查表时会发现数目不对，就是因为被视为主键组的缘故。。坑
        print(session.query(table).filter(table.movieId == 1).all())

        # 因此，建议只是查数据时，用build_query 方式~
        print(session.query(table2).filter(table2.c.movieId == 1).all())



