import os
import sqlite3


class Database():
    table_name = "pairs"

    def __init__(self):
        self.con = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'hash.db'), detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cur = self.con.cursor()
        self.create_database()

    def drop_database(self):
        sql = f"""DROP TABLE {self.table_name};"""
        self.cur.execute(sql)
        self.con.commit()

    def create_database(self):
        sql = f"""create table if not exists {self.table_name} (
            pair_id primary key,
            pair_fee text,
            pair_dex text,
            token0_id text,
            token0_symbol text,
            token0_decimals text,
            token1_id text,
            token1_symbol text,
            token1_decimals text
        );"""
        self.cur.execute(sql)
        self.con.commit()

        sql = f"""CREATE UNIQUE INDEX IF NOT EXISTS id_UNIQUE ON {self.table_name} (
            pair_id ASC
        );"""
        self.cur.execute(sql)
        self.con.commit()

    def update(self, pair_id, pair_dex, token0_id, token0_symbol, token0_decimals, token1_id, token1_symbol, token1_decimals, pair_fee=None):
        sql = f"""insert or replace into {self.table_name} (
            pair_id,
            pair_fee,
            pair_dex,
            token0_id,
            token0_symbol,
            token0_decimals,
            token1_id,
            token1_symbol,
            token1_decimals
        ) values (
            '{pair_id}',
            '{pair_fee}',
            '{pair_dex}',
            '{token0_id}',
            '{token0_symbol}',
            '{token0_decimals}',
            '{token1_id}',
            '{token1_symbol}',
            '{token1_decimals}'
        )"""
        self.cur.execute(sql)
        self.con.commit()

    def get_all(self):
        sql = f"select * from {self.table_name}"
        res = self.cur.execute(sql)
        return res.fetchall()
