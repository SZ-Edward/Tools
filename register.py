#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Aurora Wu (wuxy91@gmail.com)'
__copyright__ = "Copyright (c) 2013 aurorawu.com"

import traceback
import dbutils
import time
import check
import ams
import account
import datetime
import tool
import ujson as json
import config
import dbutils


class Register:
    """tool_dict contains a connection of the redis connection pool, a register queue, a query connection of
    the database connection pool, and a update connection of the database connection pool"""
    def __init__(self, logger, tool_dict):
        self.logger = logger
        self.tool_dict = tool_dict

    #从号码池里取一个KC号，返回''表明号码池中无号
    def get_uid(self):
        dbHandler = dbutils.DBHandler(self.logger, self.tool_dict['read_conn'])
        try: #取得一个最后时间为当前时间两小时的KC号
            sql = "SELECT UID FROM KC_DB.T_AvaNum WHERE LastTime < (NOW()-INTERVAL 2 HOUR) ORDER BY RandType LIMIT 10"
            for row in dbHandler.query_all(sql):
                sql = "DELETE FROM KC_DB.T_AvaNum WHERE UID = %d AND LastTime < (NOW()-INTERVAL 2 HOUR)"
                if dbHandler.single_update(sql, (row[0])) == 1:
                    return row[0]
        except:
            self.logger.error(u'Register.get_uid() 执行异常：%s' % traceback.format_exc())

    # def handle_request(self, response):
    #     if response.error:
    #         self.logger.error(response.error)
    #     else:
    #         self.logger.info(response.body)

    #1分钟内重复请求判断
    def is_registered(self, phone, invite, bid='kc'):
        dbHandler = dbutils.DBHandler(self.logger, self.tool_dict['read_conn'])
        try:
            last_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - 1 * 60))
            sql = 'SELECT 1 FROM KC_DB.`temp_reg_process` WHERE createtime>%s AND phone=%s AND bid=%s '
            rs = dbHandler.query_one(sql, (last_time, phone, bid))
            if rs:
                return True
            else:
                sql = 'INSERT INTO KC_DB.`temp_reg_process`(phone,invite,bid) VALUES(%s,%s,%s)'
                dbHandler.single_update(sql, (phone, invite, bid))
                return False
        except:
            self.logger.error(u'Register.is_registered() 执行异常：%s' % traceback.format_exc())

    #保存每天注册数据
    def register_by_day(self, mobile, invite, pv, auto_reg, ip, bid='kc'):
        dbHandler = dbutils.DBHandler(self.logger, self.tool_dict['read_conn'])
        try:
            dt = datetime.datetime.today().strftime("%Y-%m-%d 00:00:00")
            sql = 'SELECT 1 FROM KC_DB.`day_reg` WHERE regtime >= %s AND mobile = %s AND bid = %s'
            if not dbHandler.query_one(sql, (dt, mobile, bid)):
                sql = 'INSERT INTO KC_DB.`day_reg`(mobile,invite,pv,auto_reg,ip,bid) VALUES(%s,%s,%s,%s,%s,%s)'
                dbHandler.single_update(sql, (mobile, invite, pv, auto_reg, ip, bid))
        except:
            self.logger.error(u'Register.register_by_day() 执行异常：%s' % traceback.format_exc())

    #插入临时注册表
    def temp_register(self, phone, uid, password, invitedby):
        dbHandler = dbutils.DBHandler(self.logger, self.tool_dict['write_conn'])
        try:
            sql = 'INSERT INTO KC_DB.`temp_register`(uid, password, mphone, invitedby, invitedflag, regfrom, regtime) '\
                  'VALUES(%s,%s,%s,%s,1,mobile,now())'
            return dbHandler.single_update(sql, (uid, tool.encrypt_passwd(password), phone, invitedby))
        except:
            self.logger.error(u'Register.temp_register() 执行异常：%s' % traceback.format_exc())

    #获得注册信息
    def get_sms_reg_info(self, imsi, invite=None, bid='kc', callback=None):
        if not callback:
            callback = tool.return_values
        dbHandler, result = dbutils.DBHandler(self.logger, self.tool_dict['write_conn']), {}
        try:
            sql = "SELECT `reginfo` FROM `KC_DB`.`reg_by_sms` WHERE `status`=0 AND `bid`='%s' AND `imsi`='%s' " \
                  "ORDER BY `id` DESC LIMIT 1 "
            rs = dbHandler.query_one(sql, (bid, imsi))
            # self.logger.info('sms_reg_info COUNT:%s' % len(rs))
            if rs:
                result = rs['reginfo']
                # for row in rs:
                #     result = row['reginfo']
                #     try:
                #         sql = "UPDATE KC_DB.`reg_by_sms` SET `status` = 1 WHERE `imsi` = '%s' AND bid='%s'" % (imsi, bid)
                #         self.logger.info('sms_reg_info_2 %s' % sql)
                #         #mysql_facade.change_record(sql,config.KC_DB)
                #     except:
                #         self.logger.error('sms_reg_info_update_error %s' % traceback.format_exc())
                #     break
            else:
                result = {"result": "1", "reason": u''}
        except:
            self.logger.error(u'Register.update_sms_reg_info() 执行异常：%s' % traceback.format_exc())
        finally:
            return callback(result)

    #保存注册信息
    def save_sms_reg_info(self, imsi, phone, reg_info, bid='kc', callback=None):
        if not callback:
            callback = tool.return_values
        dbHandler, count = dbutils.DBHandler(self.logger, self.tool_dict['write_conn']), -1
        try:
            sql = "INSERT INTO KC_DB.`reg_by_sms`(imsi,phone,reginfo,bid) VALUES('%s','%s','%s','%s')"
            count = dbHandler.single_update(sql, (imsi, phone, str(reg_info).replace("'", "\""), bid))
        except:
            self.logger.error(u'Register.save_sms_reg_info() 执行异常：%s' % traceback.format_exc())
        finally:
            return callback(count)

    #保存安装信息
    def save_install_record(self, ip, v, pv, brandid, device_id, channel_id, imsi, callback=None):
        if (not imsi) and (not device_id):
            return False
        if not callback:
            callback = tool.return_values
        dbHandler, res = dbutils.DBHandler(self.logger, self.tool_dict['write_conn']), -1
        try:
            if not imsi and device_id.isdigit():
                imsi = device_id
            sql = "INSERT INTO KC_DB.`install_log`(ip, v, pv, brandid, imsi, device_id, channel_id, add_time) " \
                  "VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
            res = dbHandler.single_update(sql, (ip, v, pv, brandid, imsi, device_id, channel_id,
                                          time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
        except:
            self.logger.error(u'Register.save_install_record() 执行异常：%s' % traceback.format_exc())
        finally:
            return callback(res)

    #保存imsi和uid映射信息
    def save_imsi_uid_mapping_record(self, uid, imsi, device_id):
        if (not imsi) and (not device_id):
            return False
        dbHandler, res = dbutils.DBHandler(self.logger, self.tool_dict['write_conn']), -1
        try:
            sql = "INSERT INTO KC_DB.`imsi_uid_mapping`(uid, imsi, device_id, add_time) VALUES('%s', '%s', '%s', '%s')"
            res = dbHandler.single_update(sql, (uid, imsi, device_id, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
        except:
            self.logger.error(u'Register.save_imsi_uid_mapping_record() 执行异常：%s' % traceback.format_exc())
        finally:
            return res

    #手动注册
    def register(self, phone, invitedby, pv, v, client='kc', ip='', bid='kc', invite_flag='1', imsi=None, device_id=None,
                 base_domain=None, callback=None):
        logger, result = self.logger, {}
        logger.info(u'收到注册请求:手机号码==%s，推广号码==%s，版本==%s，版本号==%s，产品==%s' % (phone, invitedby, pv, v, bid))
        if not callback:
            callback = tool.return_values
        try:
            #手机号码格式验证
            if check.is_mobile(phone) == -1:
                logger.info(u'注册手机号码%s格式错误' % phone)
                result['result'], result['reason'] = '100003', u'手机号码格式错误'
                return callback(result)
            invitedby = '1' if not invitedby.isdigit() else invitedby
            if self.is_registered(phone, invitedby, bid):
                logger.info(u'手机号%s在1分钟内连续请求，稍后再试' % phone)
                result['result'], result['reason'] = '100011', u'手机号码==%s在1分钟内连续请求，请稍后再试' % phone
                return callback(result)
            #####################################################################################
            job = self.tool_dict['queue'].enqueue(ams.mobilereg, phone, invitedby, invite_flag, 'mobile', ip, pv+"|"+v, bid)
            self.register_by_day(phone, invitedby, pv, 0, ip, bid)
            time.sleep(2)
            res = job.result
            logger.info(u'手动注册结果：%s' % res)
            if res['code'] == '0':
                if 'uid' in res and res['uid']:
                    uid = res['uid']
                    try:# 异步更新用户属性
                        res = self.save_imsi_uid_mapping_record(uid, imsi, device_id)
                        if base_domain:
                            url = base_domain + '/mobile/update_user_properties?uid=%s&action_name=%s&sign=%s' \
                                  % (uid, 'reg', tool.md5_password(str(uid)+'reg'+config.key))
                            #tool.asyncHTTPClient(url)
                    except:
                        logger.error(u'register:%s' + traceback.format_exc())
                #注册成功，给手机客户端返回值
                logger.info(u"注册成功：手机号码==%s，版本==%s，版本号==%s，invite==%s，bid==%s" % (phone, pv, v, invitedby, bid))
                result['result'], result['reason'] = '0', u'注册成功'
                return callback(result)
            elif res['code'] == '4':
                logger.error(u"号码池中无可用的uid")
                result['result'], result['reason'] = '100012', u'号码池中无可用的帐号'
                return callback(result)
            else:
                if res['code'] not in ['1', '7', '5']:
                    logger.error(u"手机号码==%s注册失败，AMS返回码==%s" % (phone, res['code']))
                else:
                    logger.warn(u"手机号码==%s注册失败，AMS返回码==%s" % (phone, res['code']))
                result['result'], result['reason'] = '100013', u'注册失败，错误码：%s' % res['code']
                return callback(result)
        except:
            result["result"], result["reason"] = "999999", u"服务器繁忙，请稍后再试"
            logger.error(u'Register.register() 注册失败：%s' + traceback.format_exc())
        finally:
            logger.info(u'手动注册结果：%s' % result)

    #自动注册
    def auto_register(self, phone, invitedby, version, phone_version, client='kc', ip='', bid='kc', imsi=None,
                      device_id=None, base_domain=None, callback=None):
        result = {}
        self.logger.info(u'收到自动注册请求：手机号码==%s，推广号码==%s，版本==%s，版本号==%s，brandid==%s' %
                         (phone, invitedby, phone_version, version, bid))
        if not callback:
            callback = tool.return_values
        #手机号码格式验证
        if check.is_mobile(phone) == -1:
            self.logger.info(u'注册手机号码%s格式错误' % phone)
            result['result'], result['reason'] = '100003', u'手机号码格式错误'
            return callback(result)
        if not invitedby.isdigit():
            invitedby = '1'
        self.is_registered(phone, invitedby, bid)
        invitedflag = '1'
        job = self.tool_dict['queue'].enqueue(ams.automobilereg, phone, invitedby, invitedflag, 'mobile', ip,
                                              phone_version+"|"+version, bid)
        #####################################################################################
        print('%s, res=========%s' % (datetime.datetime.now(), job.result))
        time.sleep(2)
        res = job.result
        print('%s, res=========%s' % (datetime.datetime.now(), res))
        code, uid, password = res['code'], res['uid'], res['password']
        if code == '0' and uid and password:
            password = ams.rc4(ams.hex2str(password), config.AMS_KEY)
            self.register_by_day(phone, invitedby, phone_version, 1, ip, bid)
            self.logger.info(u'自动注册成功：phone==%s，uid==%s，passwd==%s，版本==%s，版本号==%s，invite==%s，bid==%s' %
                             (phone, uid, password, phone_version, version, invitedby, bid))
            account_obj = account.Account(self.logger, self.tool_dict)
            # caller = account_obj.get_bind_relation(uid)[1]
            # caller = caller if caller else phone
            login_res = account_obj.login(uid, tool.md5_password(password), version, phone_version, bid, ip)
            self.logger.info(login_res)
            login_res = json.dumps(login_res)
            try:
                if login_res and 'first' in login_res and (not isinstance(login_res, basestring)):
                    first = login_res.get('first', 0)
                    if 'uid' in res and res['uid']:
                        uid = res['uid']
                        try:# 异步更新用户属性
                            self.save_imsi_uid_mapping_record(uid, imsi, device_id)
                            if base_domain:
                                url = base_domain + '/mobile/update_user_properties?uid=%s&action_name=%s&sign=%s' \
                                      % (uid, 'reg', tool.md5_password(str(uid) + 'reg' + config.key))
                                #tool.asyncHTTPClient(url)
                                #log.info(res)
                        except:
                            result["result"], result["reason"] = "999999", u"服务器繁忙，请稍后再试"
                            self.logger.error(traceback.format_exc())
                    else:
                        first = 0
            except:
                self.logger.info(traceback.format_exc())
            msg = login_res['msg'] if not isinstance(login_res, basestring) else ''
            result = {'result': '0', 'uid': uid, 'pwd': password, 'caller': ams.str2hex(ams.rc4(phone, config.key)),
                      'bind_phone': ams.str2hex(ams.rc4(phone, config.key)), 'reason': msg, 'msg': msg, 'kcid': uid}
            if imsi and len(imsi) > 0:
                self.save_sms_reg_info(imsi, phone, result, bid)
            return callback(result)
        else:
            self.logger.warn(u"手机号码%s注册失败：AMS返回码==%s" % (phone, code))
            result['result'], result['reason'] = '100013', u'注册失败，错误码：%s' % code
            # result['result'], result['reason'] = code, code
            return callback(result)

    #查询短信注册信息
    def sms_reg_info(self, imsi, invite=None, bid='kc', callback=None):
        if not callback:
            callback = tool.return_values
        dbHandler, logger, result = dbutils.DBHandler(self.logger, self.tool_dict['read_conn']), self.logger, {}
        try:
            sql = "SELECT `reginfo` FROM `KC_DB`.`reg_by_sms` WHERE `status`=0 AND `bid`='%s' AND `imsi`='%s' " \
                  "ORDER BY `id` DESC LIMIT 1 "
            logger.info(u'Register.sms_reg_info()：%s' % sql)
            rs = dbHandler.query_one(sql, [bid, imsi])
            # logger.info(u'Register.sms_reg_info()：COUNT==%s' % len(rows))
            if rs:
                result = rs['reginfo']
                # for row in rows:
                #     result = row['reginfo']
                #     try:
                #         sql = "UPDATE KC_DB.`reg_by_sms` SET `status` =1 WHERE `imsi` = '%s' AND bid='%s'" % (imsi, bid)
                #         logger.info(u'Register.sms_reg_info()：%s' % sql)
                #     except:
                #         logger.error(u'Register.sms_reg_info() 执行异常' % traceback.format_exc())
                #     break
            else:
                result = {"result": "1", "reason": u''}
        except:
            logger.error(u'Register.sms_reg_info() 查询失败：%s' % traceback.format_exc())
        finally:
            logger.info(u'查询短信注册信息结果：%s' % result)
            return callback(result)


