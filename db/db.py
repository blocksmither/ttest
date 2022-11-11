import sqlite3
import os
import datetime


class Database():
    table_name = "prices"

    def __init__(self):
        self.con = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'arb.db'), detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cur = self.con.cursor()

    def drop_database(self):
        sql = f"""DROP TABLE {self.table_name};"""
        self.cur.execute(sql)
        self.con.commit()

    def create_database(self):
        sql = f"""create table if not exists {self.table_name} (
            address text primary key,
            date TIMESTAMP,
            reserves0 text,
            reserves1 text,
            sqrtprice text
        );"""
        self.cur.execute(sql)
        self.con.commit()

        sql = f"""CREATE UNIQUE INDEX IF NOT EXISTS id_UNIQUE ON {self.table_name} (
            address ASC
        );"""
        self.cur.execute(sql)
        self.con.commit()

    def update(self, address, reserves0=None, reserves1=None, sqrtprice=None):
        now = datetime.datetime.now()
        sql = f"""insert or replace into {self.table_name} (
            address,
            date,
            reserves0,
            reserves1,
            sqrtprice
        ) values (
            '{address}',
            '{now}',
            '{reserves0}',
            '{reserves1}',
            '{sqrtprice}'
        )"""
        self.cur.execute(sql)
        self.con.commit()

    def get(self, address):
        sql = f"""select * from {self.table_name} where address='{address}'"""
        res = self.cur.execute(sql)
        return res.fetchone()
