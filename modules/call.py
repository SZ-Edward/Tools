#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Aurora Wu (wuxy91@gmail.com)'
__copyright__ = "Copyright (c) 2013 aurorawu.com"


'''手机软件打电话接口'''
import traceback
import balance
import check
import tool
import config
import account
from fs_client import make_call


class Call:
    """tool_dict contains a connection of the redis connection pool, a call queue, a query connection of
    the database connection pool, and a update connection of the database connection pool"""
    def __init__(self, logger, tool_dict):
        self.logger = logger
        self.tool_dict = tool_dict

    def call_back(self, uid, md5_passwd, callee, os_type, version, bid, base_domain=None, callback=None):
        logger, redis_conn, res = self.logger, self.tool_dict['redis_conn'], {}
        if not callback:
            callback = tool.return_values
        logger.info(u'收到回拨请求：uid==%s，被叫号码==%s，手机操作系统==%s，产品==%s，版本号==%s' % (uid, callee, os_type, bid, version))
        '''检测该uid是否已经在呼叫队列里'''
        if redis_conn and redis_conn.get(uid) == '1':
            logger.info(u'当前呼叫已存在队列中，故丢弃。uid==%s' % uid)
            res['result'], res['calltime'], res['reason'] = '100010', '0', u'呼叫请求重复提交'
            return callback(res)
        if redis_conn:#该uid不在呼叫队列里，添加该uid的呼叫到队列里
            redis_conn.setex(uid, '1', 10)
        '''当前呼叫队列里没有该uid'''
        # 1、检测被叫号码格式是否有效
        can_call = tool.number_deal(callee)
        if can_call == '-1':
            logger.info(u'uid==%s：呼叫%s被叫号格式验证失败' % (uid, callee))
            res['result'], res['calltime'], res['reason'] = '100003', '0', u'被叫号码格式错误'
            return callback(res)
        # 2、验证用户密码是否正确
        user = check.check_uid_pwd(uid, md5_passwd)
        if user == '-1':
            logger.info(u'uid==%s：呼叫%s用户密码验证失败' % (uid, callee))
            res['result'], res['calltime'], res['reason'] = '100004', '0', u'账号密码验证失败'
            return callback(res)
        # 3、查询该uid的余额是否可以打电话
        balance_obj = balance.Balance(self.logger, self.tool_dict)
        can_call = balance_obj.can_call(uid)
        if int(can_call['result']) != 1:
            logger.info(u"uid==%s：余额不足，呼叫%s失败" % (uid, callee))
            res['result'], res['calltime'], res['reason'] = '100005', '0', u'余额不足'
            return callback(res)
        # 4、设置是否显号的参数
        is_show = '1' if int(can_call['show_number']) == 1 else '0'
        # 5、查询用户绑定的手机号码
        account_obj = account.Account(self.logger, self.tool_dict)
        caller = account_obj.get_bind_relation(uid)[1]
        caller = user['mobile'] if not caller else caller
        if not caller:
            logger.info(u"呼叫%s失败：uid==%s没有绑定手机号" % (callee, uid))
            res['result'], res['calltime'], res['reason'] = '100006', '0', u'该账号未绑定手机号'
            return callback(res)
        '''回拨'''
        if caller == callee:
            res['result'], res['calltime'], res['reason'] = '100007', '0', u'该账号绑定的手机号与被叫号码相同'
            return callback(res)
        try:
            if redis_conn:
                if redis_conn.get('call_count'):
                    print('call_count  %s' % redis_conn.get('call_count'))
                else:
                    redis_conn['call_count'] = 0
            if config.is_use_hu_gateway and (redis_conn and int(redis_conn.get('call_count')) < 60) and \
                    tool.is_cmcc_number(caller) and tool.is_cmcc_number(callee):
                fee = 0.15 if bid == 'kc' else 0.12
                logger.info(u'new_cb_info：uid==%s，主叫号码==%s，被叫号码==%s，费用==%s元' % (uid, caller, callee, fee))
                self.tool_dict['queue'].enqueue(make_call, '0'+caller, '0'+callee, uid, 'gwhu', fee)
                result = '0'
            else:
                logger.info(u"根据uid==%s分配回拨地址" % uid)
                if int(uid) % 100 <= 30:
                    cb_url = config.new_cb_url1
                elif 30 < int(uid) % 100 <= 50:
                    cb_url = config.new_cb_url2
                elif 50 < int(uid) % 100 <= 70:
                    cb_url = config.new_cb_url3
                elif 70 < int(uid) % 100 <= 90:
                    cb_url = config.new_cb_url4
                else:
                    cb_url = config.new_cb_url5
                sign = tool.md5_password('kcid=%s&key=%s' % (uid, config.NEW_CB_KEY))
                url = cb_url % (uid, uid, caller, callee, '2', is_show, '', sign, bid)
                logger.info(url)
                result = tool.http_get(url)
        except:
            logger.error(" proc exception: %s by %s " % (traceback.format_exc(), uid))
            res['result'], res['calltime'], res['reason'] = '999999', '0', u'服务器错误'
            return callback(res)
        if result == '0':
            logger.info(u"uid==%s呼叫成功：%s ===> %s" % (uid, caller, callee))
            try:# 异步更新用户属性
                if base_domain:
                    url = base_domain + '/mobile/update_user_properties?uid=%s&action_name=%s&sign=%s' \
                          % (uid, 'call', tool.md5_password(str(uid) + 'call' + config.key))
            except Exception, e:
                logger.error(e)
            res['result'], res['calltime'], res['reason'] = '0', '0', u'拨打成功'
            return callback(res)
        elif result == '3':
            logger.info(u"uid==%s，caller==%s 主叫方号码验证失败" % (uid, caller))
            res['result'], res['calltime'], res['reason'] = '100008', '0', u'主叫方号码验证失败'
            return callback(res)
        elif result == '4':
            logger.info(u"uid==%s，callee==%s 被叫方号码验证失败" % (uid, callee))
            res['result'], res['calltime'], res['reason'] = '100003', '0', u'被叫号码格式错误'
            return callback(res)
        elif result == '1' or result == '2':
            logger.warn(u"uid==%s，%s ===> %s Error(%s)" % (uid, caller, callee, result))
            res['result'], res['calltime'], res['reason'] = '100009', '0', u'接口调用发生错误(1/2)'
            return callback(res)
        else:
            logger.warn(u"uid==%s，%s ===> %s Error" % (uid, caller, callee))
            res['result'], res['calltime'], res['reason'] = '100009', '0', u'接口调用发生错误(%s)' % result
            return callback(res)
