# -*- coding: utf-8 -*-
#!/usr/bin/env python
# coding: utf-8

__author__ = "Sokos Lee (cnhawkwing@gmail.com)"
__copyright__ = "Copyright (c) 2012 SokosLee.com"


from handlers.BaseHandler import BaseHandler
import tornado.web
import tornado.gen
import ujson as json
import tool
import traceback
import callshow
import mobile_binder
import config


class CallShowHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self): #uid,pwd,operate,sign
        logger, result = self.logger, {"result": "500", "reason": u"server error"}
        try:
            uid = self.get_argument('uid', None)
            pwd = self.get_argument('pwd', None)
            operate = self.get_argument('operate', None)
            sign = self.get_argument('sign', None)
            if (not uid) or (not pwd) or (not operate) or (not sign):
                result['result'], result['reason'] = '403', u'验证失败'
            else:
                logger.info(u'收到去电显号操作请求：uid==%s，operate==%s' % (uid, operate))
                #验证url请求
                if sign != tool.md5_password(uid+pwd+operate+config.key):
                    result['result'], result['reason'] = '403', u'验证失败'
                else:
                    callshow_obj = callshow.call_show(logger, self.make_queue)
                    result = yield tornado.gen.Task(callshow_obj.open, uid, pwd, operate)
        except:
            logger.error(u" proc exception: %s" % traceback.format_exc())
            yield tornado.gen.Task(self.captureException, exc_info=True)
        logger.info(result)
        self.finish(json.dumps(result))

    def post(self, kcid, md5psw, called, phone_version, version):
        pass


class VIPHandler(BaseHandler):#VIP
    def get(self):
        pass
    def post(self):
        pass


class SysMsgHandler(BaseHandler):#系统公告
    def get(self):
        # queue = self.application.queue
        # job = queue.enqueue_call(func=None, args=(), timeout=300)
        # time.sleep(1)
        # print job.result
        pass

    def post(self):
        pass


class BindHandler(BaseHandler): #帐号绑定
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):# kcid, pwd, code, sign
        logger, result = self.logger, {"result": "500", "reason": u"server error"}
        try:
            uid = self.get_argument('kcid')
            pwd = self.get_argument('pwd')
            code = self.get_argument('code', '')
            sign = self.get_argument('sign')
            if tool.check_key(sign, uid+config.key) != 1:
                result['result'], result['reason'] = '-6', u'验证失败'
            else:
                bind_obj = mobile_binder.binder(logger, self.make_queue)
                result = yield tornado.gen.Task(bind_obj.submit_bind_relations, uid, pwd, code, self.bid)
        except:
            logger.error(u"\n proc exception: \n%s" % traceback.format_exc())
            yield tornado.gen.Task(self.captureException, exc_info=True)
        logger.info(result)
        self.finish(json.dumps(result))


    def post(self):
        pass