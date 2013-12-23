#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Aurora Wu (wuxy91@gmail.com)'
__copyright__ = "Copyright (c) 2013 aurorawu.com"


import dbutils
import balance
import datetime
import time
import tool
import config
import ams
import check
import traceback


class Account:
    """tool_dict contains a query connection of the database connection pool, and a update connection of
    the database connection pool"""
    def __init__(self, logger, tool_dict):
        self.logger = logger
        self.tool_dict = tool_dict

    def get_bind_relation(self, uid):#获得绑定关系
        dbHandler = dbutils.DBHandler(self.logger, self.tool_dict['read_conn'])
        try:
            sql = 'SELECT uid, caller FROM KC_DB.`T_ImsiBindAccount` WHERE uid = %s'
            rs = dbHandler.query_one(sql, [uid])
            return rs if rs else ['', '']
        except:
            self.logger.error(u'Account.get_bind_mobile() 查询异常：%s' % traceback.format_exc())

    def remove_bind_relation(self, uid):#删除绑定关系
        dbHandler = dbutils.DBHandler(self.logger, self.tool_dict['read_conn'])
        try:
            sql = "DELETE FROM KC_DB.`T_ImsiBindAccount` WHERE uid = %s" % uid
            return dbHandler.single_update(sql, [uid])
        except:
            self.logger.error(u'Account.remove_bind_relation() 执行异常：%s' % traceback.format_exc())

    def login(self, account, md5psw, version_no, os_type, ip='', bid='kc', pform='', psystem='', ptype='', cversion='',
              callback=None):#登录
        self.logger.info(u"收到登录请求：帐号/手机号码==%s，版本==%s，版本号==%s，产品==%s" % (account, os_type, version_no, bid))
        result = {}
        try:
            if not callback:
                callback = tool.return_values
            if not account or len(md5psw) != 32:
                result['result'], result['reason'] = "100004", u'账号密码验证失败'
                return callback(result)
            #检查是用手机号码还是帐号登录的
            login_type = 'mobile' if check.is_mobile(account) == 1 else 'kc'
            # phone = account if login_type == 'mobile' else ''
            # res = ams.login(login_type, account, md5psw, 'mobile', ip, bid, pform, psystem, ptype, cversion)
            job = self.tool_dict['queue'].enqueue(ams.login, login_type, account, md5psw, 'mobile', ip, bid, pform,
                                                  psystem, ptype, cversion)
            #####################################################################################
            time.sleep(2)
            res = job.result
            if res['code'] == '2':
                self.logger.info(u"帐号不存在：%s" % account)
                result['result'], result['reason'] = "100008", u'帐号不存在'
                return callback(result)
            elif res['code'] == '10':
                self.logger.info(u"登录失败，账号密码错误：%s" % account)
                result['result'], result['reason'] = "100004", u'账号密码验证失败'
                return callback(result)
            elif res['code'] == '0':#登录成功
                uid, phone, password = ams.getInfo(login_type, account, bid)
                caller = self.get_bind_relation(account)[1]
                caller = phone if not caller else caller
                msg, uid_list, calltime = '', [], 0
                first_login = res.get('first', 0)
                if int(first_login) == 1 or uid in uid_list:
                    msg = config.FirstLoginMsg % (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                elif version_no >= '1.4.2':
                    balance_info = balance.Balance(self.logger, self.tool_dict).get_balance_2(uid, bid)
                    msg = config.NormalLoginMsg % balance_info
                    calltime = balance_info['calltime']
                self.logger.info(u"登录成功：KC号==%s，手机==%s，版本==%s，版本号==%s" % (uid, phone, os_type, version_no))
                result = {'result': '0', 'mobile': phone, 'kcid': uid, 'caller': caller, 'msg': msg, 'first': first_login,
                          'calltime': str(calltime), 'reason': u'登录成功'}
                return callback(result)
            else:
                self.logger.warn(u"%s登录失败，AMS返回码：%s" % (account, res['code']))
                result['result'], result['reason'] = '999998', u'未知错误，错误码：%s' % res['code']
                return callback(result)
        except:
            result["result"], result["reason"] = "999999", u"服务器繁忙，请稍后再试"
            self.logger.error(u'Account.login() 发生错误：%s' % traceback.format_exc())
        finally:
            self.logger.info(u'登录结果：%s' % result)