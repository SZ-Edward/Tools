# -*- coding: utf-8 -*-
#!/usr/bin/env python
# coding: utf-8

__author__ = "Sokos Lee (cnhawkwing@gmail.com)"
__copyright__ = "Copyright (c) 2012 SokosLee.com"

import tornado
import tornado.web
import tornado.gen
from handlers.BaseHandler import BaseHandler
import traceback
import tool
import ujson as json
import balance
import config
import dbutils


class BalanceHandler(BaseHandler):#账户
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        # kcid , pwd, sign, newclient
        result, logger, query, update = {}, self.logger, self.query_conn, self.update_conn
        try:
            uid = self.get_argument('kcid', None)
            pwd = self.get_argument('pwd', None)
            newclient = self.get_argument('newclient', '')
            sign = self.get_argument('sign', None)
            if uid and pwd and sign:
                if tool.check_key(sign, uid+config.key) != 1:
                    result['result'], result['reason'] = '100002', u'验证失败'
                else:
                    tool_dict = {'redis_conn': self.redis_conn, 'queue': self.make_queue('balance_queue'),
                                 'read_conn': query, 'write_conn': update}
                    result = yield tornado.gen.Task(balance.Balance(logger, tool_dict).query_balance, uid, pwd, newclient, self.bid)
            else:
                result['result'], result['reason'] = '100001', u'参数缺失'

        except:
            result["result"], result["reason"] = "999999", u"服务器繁忙，请稍后再试"
            logger.error(u"BalanceHandler发生错误：%s" % (traceback.format_exc()))
            yield tornado.gen.Task(self.captureException, exc_info=True)
        finally:
            dbutils.DBHandler(logger, query).close()
            dbutils.DBHandler(logger, update).close()
            logger.info(result)
            self.finish(json.dumps(result))

    def post(self):
        pass