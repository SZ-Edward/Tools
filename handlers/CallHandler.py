# -*- coding: utf-8 -*-
#!/usr/bin/env python
# coding: utf-8

__author__ = "Sokos Lee (cnhawkwing@gmail.com)"
__copyright__ = "Copyright (c) 2012 SokosLee.com"


import tornado
import tornado.web
import tornado.gen
from modules import call
from handlers.BaseHandler import BaseHandler
import ujson as json
import traceback
import dbutils
import config
import tool


class CallHandler(BaseHandler):#拨打
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        # kcid, pwd, called_number, v, pv, sign
        res, logger, query, update = {}, self.logger, self.query_conn, self.update_conn
        try:
            uid, passwd = self.get_argument('kcid', None), self.get_argument('pwd', None)
            version_no, os_type = self.get_argument('v', None), self.get_argument('pv', None)
            callee_no, sign = self.get_argument('called_number', None), self.get_argument('sign', None)
            if uid and passwd and version_no and os_type and callee_no and sign:
                check = tool.check_key(sign, uid+config.key)
                if check != 1:
                    res["result"], res["reason"] = "100002", u"验证失败"
                elif not callee_no.isdigit():
                    res["result"], res["reason"] = "100003", u"手机号码格式错误"
                else:
                    tool_dict = {'redis_conn': self.redis_conn, 'queue': self.make_queue('call_queue'),
                                 'read_conn': query, 'write_conn': update}
                    res = yield tornado.gen.Task(call.Call(logger, tool_dict).call_back, uid, passwd, callee_no,
                                                 os_type, version_no, self.bid, self.base_domain)
            else:
                res["result"], res["reason"] = "100001", u"参数缺失"
        except:
            res["result"], res["reason"] = "999999", u"服务器繁忙，请稍后再试"
            logger.error(u'CallHandler发生错误：%s' % traceback.format_exc())
            yield tornado.gen.Task(self.captureException, exc_info=True)
        finally:
            dbutils.DBHandler(logger, query).close()
            dbutils.DBHandler(logger, update).close()
            logger.info(res)
            self.finish(json.dumps(res))

    def post(self, kcid, md5psw, called, phone_version, version):
        pass




