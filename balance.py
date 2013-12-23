#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Aurora Wu (wuxy91@gmail.com)'
__copyright__ = "Copyright (c) 2013 aurorawu.com"


import random
import ujson as json
import config
import tool
import check


class Balance:
    """tool_dict contains a connection of the database connection pool"""
    def __init__(self, logger, tool_dict):
        self.logger = logger
        self.tool_dict = tool_dict

    def can_call(self, uid):
        sign = tool.md5_password("%s%s" % (uid, config.kckey))
        url = config.balance_url % (config.chkfee_server, uid, sign)
        self.logger.info(u"查询用户余额url：%s" % url)
        return json.loads(tool.http_get(url))

    #查询余额
    def get_balance(self, uid, newclient=False, bid='kc'):
        ordersn = ''
        result = {'result': '-11'}
        #results = '{"result" : "-1","reason":"%s"}' % u'获取失败，请稍后重试'
        reason= u'获取失败，请稍后重试'
        results = {"result": "-1", "reason": reason}
        for i in range(0, 18):
            ordersn += '%s' % random.randint(1, 9)
        sign = tool.md5_password("ordersn=%s&uid=%s&key=%s" %(ordersn,uid,config.kckey))
        url = "http://%s/user_wallet?ordersn=%s&uid=%s&sign=%s&bid=%s" %(config.chkfee_server,ordersn,uid,sign,bid)
        self.logger.info("balance: %s" % url)
        #print url
        result = tool.http_get(url,timeout=20)
        #log.info(result)

        if result:
            results = json.loads(result)
            if int(results['result']) == 0:
                del results['willactive']
                results['valid_date'] = results['valid_date'][:10]
                results['calltime'] = int(results['balance'])/10
                results['balance'] = '%.2f' % (float(results['balance'])/100)
                results['display_vaild_date'] = '%s' % (results.get('display_vaild_date',''))
            else:
                return '{"result":"%s"}' % results['result']

            if newclient:
                results['return_string'] = u"账号:%s\\n" % uid
                results['return_string'] += u"总账户余额:%s元\\n" % results['balance']
                results['return_string'] += u"账户有效期:%s\\n" % results['valid_date']

                if results['display_vaild_date']:
                    results['return_string'] += u"去电显号有效期:%s\\n" % results['display_vaild_date']
                else:
                    results['return_string'] += u"去电显号有效期:您没有开通此项业务\\n"
            results['phone'] = check.get_bind_mobile(uid)
            results['packagelist'] = []
        return results

    def get_balance_2(self, uid, bid='kc', callback=None):
        results = {'result': '500', 'reason': 'server error'}
        if not callback:
            callback = tool.return_values
        try:
            ordersn = ''

            for i in range(0, 18):
                ordersn += '%s' % random.randint(1, 9)
            sign = tool.md5_password("ordersn=%s&uid=%s&key=%s" % (ordersn, uid, config.kckey))
            url = "http://%s/user_wallet?ordersn=%s&uid=%s&sign=%s" % (config.chkfee_server, ordersn, uid, sign)
            #log.info(u"balance: %s" % url)
            #log.info(url)
            result = tool.http_get(url,timeout=20)
            results = json.loads(result)
            #log.info(results)
            if 'result' in results and int(results['result']) == 0:
                if int(results['balance']) <= 0:
                    results['calltime'] =  0
                else:
                    if bid in ['uu']:
                        results['calltime'] = int(results['balance'])/12
                    else:
                        results['calltime'] = int(results['balance'])/8

                results['valid_date'] = results['valid_date'][:10]
                results['balance'] = '%.2f' % (float(results['balance']) / 100)
                results['balance_info'] = u"账户余额%(balance)s元，可通话%(calltime)s分钟" % results
            else:
                results['balance_info'] = u"余额为0"
                results['valid_date'] = ''
                results['calltime'] = 0
                results['result'] = 0
            #balance_info = u"账户余额%(balance)s元，可通话%(calltime)s分钟" % results

            if uid in TESTCALLTIME:
                results['calltime'] = TESTCALLTIME[uid]
        except:
            pass
        return callback(results)

    #查询余额
    def query_balance(self, uid, md5psw, newclient, bid, callback=None):
        if not callback:
            callback = tool.return_values
        res = {}
        #验证用户名密码
        uid = check.check_uid_pwd(str(uid), md5psw)
        if uid == -1:
            res['result'], res['reason'] = '-2', u'号码或者密码错误'
            return callback(res)
        #查询用户余额 res = self.get_balance(uid, newclient, bid)
        job = self.tool_dict['queue'].enqueue(self.get_balance, uid, newclient, bid)
        res = job.result
        return callback(res)
