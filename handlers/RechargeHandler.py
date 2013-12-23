# -*- coding: utf-8 -*-
#!/usr/bin/env python
# coding: utf-8

__author__ = "Sokos Lee (cnhawkwing@gmail.com)"
__copyright__ = "Copyright (c) 2012 SokosLee.com"

from handlers.BaseHandler import BaseHandler
import tornado
import tornado.web
import tornado.gen
import tool
import recharge
import traceback
import ujson as json
import config


class RechargeHandler(BaseHandler):#充值
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        result, logger = {"result": "500", "reason": u"server error"}, self.logger
        # src, kcid, paytype, goodstype, money, cardno, cardpwd, sign, pv, v, buynum
        try:
            src, uid = self.get_argument('src', ''), self.get_argument('kcid', None)
            paytype, money = self.get_argument('paytype', ''), self.get_argument('money', '100')
            cardno, cardpwd = self.get_argument('cardno', ''), self.get_argument('cardpwd', '')
            sign, buynum = self.get_argument('sign', None), self.get_argument('buynum', '')
            pv, v = self.get_argument('pv', ''), self.get_argument('v', '')
            goodstype = 2

            if (not uid) or sign != tool.md5_password(uid+config.key):
                result['result'], result['reason'] = '-6', u'验证失败'
            buynum = 1 if not buynum else buynum
            recharge_obj = recharge.Recharge(logger, self.redis_conn, self.make_queue)
            result = yield tornado.gen.Task(recharge_obj.pay, src, uid, paytype, goodstype, money, cardno, cardpwd, pv, v, buynum)
        except:
            logger.error(u" proc exception: %s" % traceback.format_exc())
            yield tornado.gen.Task(self.captureException, exc_info=True)
        logger.info(result)
        self.finish(json.dumps(result))

    def post(self):
        pass