#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Aurora Wu (wuxy91@gmail.com)'
__copyright__ = "Copyright (c) 2013 aurorawu.com"


from handlers.BaseHandler import BaseHandler
import tornado
import tornado.web
import tornado.gen
import tool
import ujson as json
import config
import traceback
import account
import dbutils


class LoginHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        result, logger, query, update = {}, self.logger, self.query_conn, self.update_conn
        try:
            account_id = self.get_argument('account', '')
            pwd = self.get_argument('pwd', '')
            version_no = self.get_argument('v', '')
            os_type = self.get_argument('pv', '')
            sign = self.get_argument('sign', None)
            if sign and account_id and pwd and version_no and os_type:
                if tool.check_key(sign, account_id+config.key) == 1:
                    tool_dict = {'redis_conn': self.redis_conn, 'queue': self.make_queue('login_queue'),
                                 'read_conn': query, 'write_conn': update}
                    result = yield tornado.gen.Task(account.Account(logger, tool_dict).login, account_id, pwd,
                                                    version_no, os_type, self.request.remote_ip, self.bid, 'mobile',
                                                    os_type, '', version_no)
                else:
                    result['result'], result['reason'] = '100002', u'验证失败'
            else:
                result['result'], result['reason'] = '100001', u'参数缺失'
        except:
            result["result"], result["reason"] = "999999", u"服务器繁忙，请稍后再试"
            logger.error(u"LoginHandler发生错误：%s" % traceback.format_exc())
            yield tornado.gen.Task(self.captureException, exc_info=True)
        finally:
            dbutils.DBHandler(logger, query).close()
            dbutils.DBHandler(logger, update).close()
            logger.info(result)
            self.finish(json.dumps(result))