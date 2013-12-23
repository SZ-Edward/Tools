#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Aurora Wu (wuxy91@gmail.com)'
__copyright__ = "Copyright (c) 2013 aurorawu.com"


import traceback


class DBHandler:

    def __init__(self, logger, db_conn):
        self.conn = db_conn
        self.cursor = db_conn.cursor()
        self.logger = logger

    #查询唯一记录
    def query_one(self, sql, param=None):
        conn, cursor = self.conn, self.cursor
        try:
            if conn and cursor and sql:
                self.logger.info(sql % tuple(param)) if param else self.logger.info(sql)
                cursor.execute(sql, param) if param else cursor.execute(sql)
                return cursor.fetchone()
            else:
                self.logger.info(u'数据库连接或为sql语句空，或参数错误')
        except:
            self.logger.error(u'dbHandler.query_one() 查询异常：%s' % traceback.format_exc())

    #查询指定数量的记录
    def query_many(self, sql, num, param=None):
        conn, cursor = self.conn, self.cursor
        try:
            if conn and cursor and sql:
                self.logger.info(sql % tuple(param)) if param else self.logger.info(sql)
                cursor.execute(sql, param) if param else cursor.execute(sql)
                return cursor.fetchmany(num)
            else:
                print(u'数据库连接或为sql语句空，或参数错误')
        except:
            print(u'dbHandler.query_many() 查询异常：%s' % traceback.format_exc())

    #查询所有记录
    def query_all(self, sql, param=None):
        conn, cursor = self.conn, self.cursor
        try:
            if conn and cursor and sql:
                self.logger.info(sql % tuple(param)) if param else self.logger.info(sql)
                cursor.execute(sql, param) if param else cursor.execute(sql)
                return cursor.fetchall()
            else:
                print(u'数据库连接或为sql语句空，或参数错误')
        except:
            print(u'dbHandler.query_all() 查询异常：%s' % traceback.format_exc())

    #执行单条insert、update、delete语句
    def single_update(self, sql, param):
        conn, cursor = self.conn, self.cursor
        try:
            if conn and cursor and sql and param:
                conn.begin()
                self.logger.info(sql % tuple(param)) if param else self.logger.info(sql)
                return cursor.execute(sql, param)
            else:
                print(u'数据库连接或为sql语句空，或参数错误')
        except:
            print(u'dbHandler.single_update() sql语句执行发生异常：%s' % traceback.format_exc())

    #执行批量insert、update、delete语句
    def batch_update(self, sql, param):
        conn, cursor = self.conn, self.cursor
        try:
            if conn and cursor and sql and isinstance(param, list):
                conn.begin()
                self.logger.info(sql % tuple(param)) if param else self.logger.info(sql)
                return cursor.executemany(sql, param)
            else:
                print(u'数据库连接或为sql语句空，或参数错误')
        except:
            print(u'dbHandler.batch_update() sql语句执行发生异常：%s' % traceback.format_exc())

    #关闭游标，释放连接
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    #提交事务
    def commit(self):
        if self.conn:
            self.conn.commit()

    #事务回滚
    def rollback(self):
        if self.conn:
            self.conn.rollback()