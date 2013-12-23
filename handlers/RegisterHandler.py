# -*- coding: utf-8 -*-
#!/usr/bin/env python
# coding: utf-8
#coding=utf-8

__author__ = "Sokos Lee (cnhawkwing@gmail.com)"
__copyright__ = "Copyright (c) 2012 SokosLee.com"

from handlers.BaseHandler import BaseHandler
import tornado
import tornado.web
import tornado.gen
import register
import ujson as json
import tool
from urllib2 import unquote
import traceback
import dbutils
import config


class RegHandler(BaseHandler): #手动注册
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        #phone, invite, v, pv, sign, **args
        result, phone, logger, query, update = {}, '', self.logger, self.query_conn, self.update_conn
        try:
            phone = self.get_argument('phone')
            invite = self.get_argument('invite', '')
            version_no = self.get_argument('v', '')
            os_type = self.get_argument('pv', '')
            sign = self.get_argument('sign', None)
            client = self.get_argument('client', '')
            imsi = self.get_argument('imsi', None)
            device_id = self.get_argument('device_id', None)
            inviteby = self.get_argument('inviteby', '1')
            if (not phone) or (not sign):
                result['result'], result['reason'] = '100001', u'参数缺失'
            else:
                if tool.check_key(sign, phone+config.key) != 1:
                    result['result'], result['reason'] = '100002', u'验证失败'
                else:
                    if invite.find("(") != -1:
                        invite = invite.replace('(', '').replace(')', '')
                    elif invite.find("[") != -1:
                        invite = invite.replace('[', '').replace(']', '')
                        #print(check_string)
                    phone = phone.replace('+860', '')
                    phone = phone.replace('+86', '')
                    phone = phone.replace('+', '')
                    #print(phone)
                    if not phone.isdigit() or tool.mobile_process(phone) == '-1':
                        result['result'], result['reason'] = '100003', u'手机号码格式错误'
                    else:
                        tool_dict = {'redis_conn': self.redis_conn, 'queue': self.make_queue('reg_queue'),
                                     'read_conn': query, 'write_conn': update}
                        result = yield tornado.gen.Task(register.Register(logger, tool_dict).register, phone, invite,
                                                        os_type, version_no, client, self.request.remote_ip, self.bid,
                                                        imsi=imsi, device_id=device_id, base_domain=self.base_domain)
        except:
            result["result"], result["reason"] = "999999", u"服务器繁忙，请稍后再试"
            logger.error(u"RegHandler发生错误 mobile==%s：%s" % (phone, traceback.format_exc()))
            yield tornado.gen.Task(self.captureException, exc_info=True)
        finally:
            dbutils.DBHandler(logger, query).close()
            dbutils.DBHandler(logger, update).close()
            logger.info(result)
            self.finish(json.dumps(result))

    def post(self):
        pass


class AutoRegHandler(BaseHandler): #自动注册
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        result, phone, logger, query, update = {}, '', self.logger, self.query_conn, self.update_conn
        try:
            phone = self.get_argument('phone', '')
            invite = self.get_argument('invite', '')
            v = self.get_argument('v', '')
            pv = self.get_argument('pv', '')
            sign = self.get_argument('sign')
            client = self.get_argument('client', '')
            sn = self.get_argument('sn', '')
            imsi = self.get_argument('imsi', None)
            device_id = self.get_argument('device_id', None)
            if (not phone) or (not sign):
                result['result'], result['reason'] = '100001', u'参数缺失'
            else:
                if tool.check_key(sign, sn+phone+config.key) != 1:
                    result['result'], result['reason'] = '100002', u'验证失败'
                else:
                    if invite.find("(") != -1:
                        invite = invite.split("(")[0]
                    elif invite.find("[") != -1:
                        invite = invite.split("[")[0]
                    tool_dict = {'redis_conn': self.redis_conn, 'queue': self.make_queue('reg_queue'),
                                 'read_conn': query, 'write_conn': update}
                    result = yield tornado.gen.Task(register.Register(logger, tool_dict).auto_register, phone, invite,
                                                    v, pv, client, bid=self.bid, imsi=imsi, device_id=device_id,
                                                    base_domain=self.base_domain)
                    # if pv in ['spread', 'mtk']:
                    #     pass
        except:
            result["result"], result["reason"] = "999999", u"服务器繁忙，请稍后再试"
            logger.error(u"AutoRegHandler发生错误 mobile==%s：%s" % (phone, traceback.format_exc()))
            yield tornado.gen.Task(self.captureException, exc_info=True)
        finally:
            dbutils.DBHandler(logger, query).close()
            dbutils.DBHandler(logger, update).close()
            logger.info(result)
            self.finish(json.dumps(result))

    def post(self):
        pass


class WapRegHandler(BaseHandler): #WAP注册
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        result, phone, logger, query, update = {}, '', self.logger, self.query_conn, self.update_conn
        try:
            self.brandid = self.get_argument('_b', None) #品牌
            #phone = self.get_argument('phone',None)#phone
            invite = self.get_argument('_p', None)#项目ID
            target = self.get_argument('_t', '')#跳转目标
            timestamp = self.get_argument('_tm', None)#unix时间戳
            sign = self.get_argument('_s', None)#验证串
            uus = self.get_argument('uus', None)

            if (not uus) or (not self.brandid) or (not invite) or (not target) or (not timestamp) or (not sign):
                result['result'], result['reason'] = '100001', u'参数缺失'
            else:
                isTrue, phone, ua = tool.getPhoneByCMWap(uus)
                if (not isTrue) or (not phone):
                    if 'HTTP_X_UP_CALLING_LINE_ID' in self.httpHeaders:#联通手机访问
                        phone = self.httpHeaders['HTTP_X_UP_CALLING_LINE_ID']
                        isTrue = True
                    elif 'HTTP_X_UP_SUBNO' in self.httpHeaders:
                        phone = self.httpHeaders['HTTP_X_UP_SUBNO']
                        isTrue = True
                if (not isTrue) or (not phone) or (not phone.isdigit()):#手机号码获取失败
                    result['result'], result['reason'] = '100001', u'参数缺失'
                else:
                    phone = tool.number_deal(phone)
                    v, pv, client, imsi, device_id = '', '', '', '', ''
                    _target = unquote(target).split('_')
                    if len(_target) >= 5:
                        v = _target[0]
                        pv = _target[1]
                        client = _target[2]
                        imsi = _target[3]
                        device_id = _target[4]
                    if tool.check_key(sign, self.brandid+invite+target+timestamp+config.key) != 1:
                        result['result'], result['reason'] = '100002', u'验证失败'
                    else:
                        self.brandid = 'kc' if self.brandid in ['1'] else 'uu'
                        tool_dict = {'redis_conn': self.redis_conn, 'queue': self.make_queue('reg_queue'),
                                     'read_conn': query, 'write_conn': update}
                        result = yield tornado.gen.Task(register.Register(logger, tool_dict).auto_register, phone,
                                                        invite, v, pv, client, brandid=self.bid, imsi=imsi,
                                                        device_id=device_id, base_domain=self.base_domain)
        except:
            result["result"], result["reason"] = "999999", u"服务器繁忙，请稍后再试"
            logger.error(u"WapRegHandler发生错误 mobile==%s：%s" % (phone, traceback.format_exc()))
            yield tornado.gen.Task(self.captureException, exc_info=True)
        finally:
            dbutils.DBHandler(logger, query).close()
            dbutils.DBHandler(logger, update).close()
            logger.info(result)
            self.finish(json.dumps(result))

    def post(self):
        pass


#查询短信注册
class SmsRegInfoHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        result, phone, logger, query, update = {}, '', self.logger, self.query_conn, self.update_conn
        try:
            invite = self.get_argument('invite', None)
            imsi = self.get_argument('imsi', None)
            sign = self.get_argument('sign', None)
            v = self.get_argument('v', '')
            pv = self.get_argument('pv', '')

            if (not invite) or (not imsi) or (not sign):
                result['result'], result['reason'] = '100001', u'参数缺失'
            else:
                logger.info(u"查询短信注册信息：invite==%s，imsi==%s，v==%s，pv==%s，sign==%s" % (invite, imsi, v, pv, sign))
                if tool.check_key(sign, imsi+config.key) != 1:
                    result['result'], result['reason'] = '100002', u'验证失败'
                else:
                    tool_dict = {'redis_conn': self.redis_conn, 'queue': self.make_queue('reg_queue'),
                                 'read_conn': query, 'write_conn': update}
                    result = yield tornado.gen.Task(register.Register(logger, tool_dict).sms_reg_info, imsi, invite, self.bid)
        except:
            result["result"], result["reason"] = "999999", u"服务器繁忙，请稍后再试"
            logger.error(u"SmsRegInfoHandler发生错误 mobile==%s：%s" % (phone, traceback.format_exc()))
            yield tornado.gen.Task(self.captureException, exc_info=True)
        finally:
            dbutils.DBHandler(logger, query).close()
            dbutils.DBHandler(logger, update).close()
            logger.info(result)
            self.finish(json.dumps(result))

    def post(self):
        pass