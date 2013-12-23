# -*- coding: utf-8 -*-
#!/usr/bin/env python
# coding: utf-8

__author__ = "Sokos Lee (cnhawkwing@gmail.com)"
__copyright__ = "Copyright (c) 2012 SokosLee.com"


''' API入口 '''
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import time
import os
import config
import MySQLdb
from DBUtils.PooledDB import PooledDB
from myLogger import Logger
from handlers import BaseHandler
from handlers import CallHandler
from handlers import LoginHandler
from handlers import BalanceHandler
from handlers.RegisterHandler import *
from raven import Client
import redis


class Application(tornado.web.Application):
    def __init__(self):
        startTime = time.time()
        self.sentry_client = Client(config.raven_client)
        handlers = [
            (r"/", HomeHandler),
            (r"/mobile/call", CallHandler),                                 #拨打
            (r"/mobile/reg", AutoRegHandler),                               #自动注册
            (r"/mobile/register", RegHandler),                              #手动注册
            (r"/auto_reg", WapRegHandler),                                  #WAP注册
            (r"/mobile/get_sms_reg_info", SmsRegInfoHandler),               #查询短信注册
            (r"/mobile/login", LoginHandler),                               #登录
            (r"/mobile/search_balance", BalanceHandler),                    #查询余额
        ]

        settings = dict(
            app_build=time.strftime("%Y%m%d-%H%M%S", time.localtime(os.stat(__file__).st_mtime)) ,
            autoescape=None,
            debug=config.isDebug,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.logger = Logger()
        self.read_pool = PooledDB(MySQLdb, 1, 20, 0, 0, 0, 0, **config.DB_mobile)
        self.write_pool = PooledDB(MySQLdb, 1, 20, 0, 0, 0, 0, **config.DB_mobile)
        self.redis_pool = redis.ConnectionPool(host='127.0.0.1', port=6379)
        timeSpent = time.time() - startTime
        print '\ninit:' + str(timeSpent) + 's' + "["+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"]\n"


class HomeHandler(BaseHandler):#主页面
    def get(self):
        raise tornado.web.HTTPError(403)

    def post(self):
        raise tornado.web.HTTPError(403)


def main():
    print "Server Start["+ time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"]"
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(config.server_port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()