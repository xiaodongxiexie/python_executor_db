# -*- coding: utf-8 -*-
# @Author: xiaodong
# @Date  : 2020/4/3

import os

import pymysql

from python_executor_db.utils import (csv_reader,
                                      links_sql,
                                      tags_sql,
                                      movies_sql,
                                      ratings_sql)


def connect(config):
    con = pymysql.connect(**config)
    return con


def execute_sql(conn, sql):
    with conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()


def create_database(conn, db_name):
    sql = f"CREATE DATABASE if not exists {db_name}"
    execute_sql(conn, sql)


def create_table(conn, create_table_sql):
    execute_sql(conn, create_table_sql)


def insert_one(conn, insert_table_sql):
    execute_sql(conn, insert_table_sql)


def insert_many(conn, template_insert_table_sql, values):
    with conn:
        cursor = conn.cursor()
        cursor.executemany(template_insert_table_sql, values)
        conn.commit()



def select(conn, select_table_sql, just_one=True):
    with conn:
        cursor = conn.cursor()
        cursor.execute(select_table_sql)
        # 查看列信息
        # print(cursor.description)
        if just_one:
            return cursor.fetchone()
        return cursor.fetchall()


def update(conn, update_table_sql):
    execute_sql(conn, update_table_sql)


def delete(conn, delete_table_sql):
    execute(conn, delete_table_sql)


if __name__ == '__main__':
    config = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "charset": "utf8",
    }
    db_name = "movies"

    config_with_db = config.copy()
    config_with_db.update(database=db_name)


    create_db_con = connect(config)

    create_database(create_db_con, db_name)

    use_db_con = connect(config_with_db)


    for create_table_sql in (links_sql, tags_sql, movies_sql):
        create_table_sql = create_table_sql.replace("INTEGER", "INT")
        create_table(use_db_con, create_table_sql)


    dataset_path = "data/dataset"
    for table_name in ("links", "movies"):
        values = []
        for v in csv_reader.read_csv(os.path.join(dataset_path, f"{table_name}.csv")):
            values.append(list(v.values()))
        placeholder = "({})".format(",".join(["%s"]*len(v)))
        insert_many(use_db_con, f"insert into {table_name} values {placeholder}", values)
