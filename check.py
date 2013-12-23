#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Aurora Wu (wuxy91@gmail.com)'
__copyright__ = "Copyright (c) 2013 aurorawu.com"


import ujson as json
import ams
import tool
import re


#验证md5加密字符串,md5string 用户传的md5串 ,check_string 明文字符串
#返回说明 返回-1：两个字符串不匹配 1:验证成功
def check_key(md5string, check_string):
    # log.info("请求验证码错误：实际==%s 客户端==%s" % (check_key, md5string))
    return -1 if md5string != tool.md5_password(check_string) else 1


#密码校验
def check_uid_pwd(uid, md5pwd):
    _type = "mobile" if len(uid) == 11 and uid[0] == '1' else 'kc'
    _uid, phone, password = ams.getInfo(_type, str(uid))
    #print password
    if not password or check_key(md5pwd, password) == -1:
        return -1
    else:
        return {"uid": _uid, "mobile": phone, "password": password}


#检测是否是手机号 返回1：是手机号 -1：不是手机号
def is_mobile(phone):
    #取号码后11位
    #mobile = phone[-11:]
    if len(phone) != 11:
        return - 1
    else:
        regex = ur'(?:1|1|1)[0-9]{10}'
        return 1 if re.match(regex, phone) else -1


#获取用户绑定kc的手机号码
def get_bind_mobile(uid):
    if uid:
        _type = "mobile" if len(uid) == 11 and uid[0] == '1' else 'kc'
        res = ams.info(_type, str(uid))
        return res['number'] if res['code'] == '0' else ''