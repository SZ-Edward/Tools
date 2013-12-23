#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Aurora Wu (wuxy91@gmail.com)'
__copyright__ = "Copyright (c) 2013 aurorawu.com"


import urllib2
import traceback
import hashlib
import socket
socket.timeout = 10
import myLogger
import check
import base64
import urllib
import random, re
import config
import tornado.httpclient
import functools
import threading
import datetime, time
import logging
import logging.handlers,logging.config
#from Crypto.Cipher import ARC4


def return_values(v):
    return v


def number_deal(called):
    if called.isdigit() and (called[0] == '0' or called[0] == '1'):
        number = called
        if called[:5] in ['12593', '12580', '17909', '17951', '17950', '10193', '17911', '17910']:
            number = called[5:]
        elif called[:4] == '0086':
            number = called[4:]
        elif called[:3] == '+86' or called[:3] == ' 86':
            number = called[3:]
        elif called[:2] == '86':
            number = called[2:]
        elif called[:2] == '00':
            return called
        elif called[:1] == '+':
            return '00' + called[1:]
        return number if 10 <= len(number) <= 12 else '-1'
    else:
        return '-1'


def mylog(codeFile=''):
    return myLogger.Logger()


'''md5加密字符串'''
def md5_password(string):
    return hashlib.new("md5", string).hexdigest()


'''请求验证'''
def check_key(sign, check_string):
    return "-6" if cmp(sign, md5_password(check_string)) else 1


def http_get(url, timeout=10):
    f = None
    try:
        if (not timeout) or (not str(timeout).isdigit()):
            timeout = 10
        f = urllib2.urlopen(url, timeout=timeout)
        res = f.read()
        f.close()
        return res
    except Exception, e:
        mylog(__name__).error('URL:%s [TIMEOUT:%s] ERROR:%s errorMessage:%s'
                              % (url, timeout, traceback.format_exc(), e.message))
    finally:
        if f:
            f.close()
    return ''


def is_cmcc_number(mobile):
    return mobile[:3] in ['134', '135', '136', '137', '138', '139', '147', '150', '151', '152', '157', '158',
                          '159', '182', '183', '184', '187', '188'] and mobile[:4] not in ['1349']


def is_cu_number(mobile):
    return mobile[:3] in ['130', '131', '132', '145', '155', '156', '185', '186']


def is_ct_number(mobile):
    return mobile[:3] in ['133', '153', '180', '181', '189'] or mobile[:4] in ['1349']


#加密用户密码
def encrypt_passwd(passwd):
    encrypted = ''
    for i in range(0, len(passwd)):
        encrypted += '%02X' % (ord(passwd[i]) ^ 0x55)
    return encrypted


#手机号码验证处理
def mobile_process(mobile):
    #如果是以179**,125**开头
    if not cmp('179', mobile[:3]):
        return mobile[5:]
    if not cmp('125', mobile[:3]):
        return mobile[5:]
    if not cmp('0086', mobile[:4]):
        return mobile[4:]

    #截取号码前3位i
    profix_check, phone, profix = -1, mobile, '-1'
    #如果是以086,+86开头,将其去掉
    if not cmp('086', mobile[:3]):
        profix_check = 1
    if not cmp('+86', mobile[:3]):
        profix_check = 1
    if profix_check == 1:
        phone = mobile[3:]
    profix = mobile[:1]
    if profix == '0' and 6 <= len(mobile) <= 12:
        return mobile

    #验证手机号码
    check.is_mobile(phone)


def getPhoneByCMWap(uus):
    if not uus:
        return False, False, False
    else:
        values = "".join(["".join(x) for x in zip(uus[1::2], uus[::2])])
        _v = base64.decodestring(values).split('&')
        if len(_v) == 2:
            return True, _v[0], _v[1]
        return False, False, False

# def async_function(func):
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         my_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
#         my_thread.start()
#     return wrapper
#
# def encrypt(str):
#     '''http传输密码加密 '''
#     enstr = ''
#     encrypt_key = '1234567890abcdefghijklmnopqrstuvwxyz'
#     decrypt_key = 'ngzqtcobmuhelkpdawxfyivrsj2468071359'
#     if len(str) == 0 :
#         return False
#     for i in range(len(str)):
#         changed = False
#         for j in range(len(encrypt_key)):
#             if str[i] == encrypt_key[j]:
#                 enstr += decrypt_key[j]
#                 changed = True
#         if not changed:
#             enstr += str[i]
#     return enstr
#
# def decrypt(str):
#     '''http传输密码解密'''
#     enstr = ''
#     encrypt_key = '1234567890abcdefghijklmnopqrstuvwxyz'
#     decrypt_key = 'ngzqtcobmuhelkpdawxfyivrsj2468071359'
#     if len(str) == 0:
#         return False
#     for i in range(len(str)):
#         changed = False
#         for j in range(len(decrypt_key)):
#             if str[i] == decrypt_key[j]:
#                 enstr += encrypt_key[j]
#                 changed = True
#         if not changed:
#             enstr += str[i]
#     return enstr
#
#
# #解密用户密码
# def dencrypt_passwd(passwd):
#     dencrypt = ''
#     if len(passwd) % 2:
#         return dencrypt
#     for i in range(0, len(passwd) / 2):
#         dencrypt += chr(int(passwd[i * 2:i * 2 + 2], 16) ^ 0x55)
#     return dencrypt
#
# #随机生成6位数字的密码
# def rand_kcpass():
#     password = ''
#     for i in range(0, 6):
#         password += '%s' % random.randint(2, 8)
#     return password
#
# #发送短信消息
# def send_sm_message(phone, message):
#     message = message.decode('utf8').encode('gbk')
#     url = "http://%s:%s/sms/sms_http.php?act=send&username=%s&passwd=%s&subuser=100001&phone=%s&content=%s"\
#      % (config.sm_ip, config.sm_port, config.sm_user, config.sm_psw, phone, urllib2.quote(message))
#     #logger.info('发送短信请求:%s' % url)
#     f = urllib2.urlopen(url,timeout=10)
#     f.close()
#
#
#
#
# def http_post(url, data):
#     try:
#         f = urllib2.urlopen(url, urllib.urlencode(data))
#         res = f.read()
#         #f.close()
#         return res
#     except:
#         mylog(__name__).error('URL:%s Post访问失败:%s' % (url, traceback.format_exc()))
#         return '{"result":"-10"}'
#
#
# def check_update(phone_version, version, partner,invite):
#     pv = phone_version.lower()
#     #currReleaseVersion = 1508
#     try:
#         version = int(str(version).replace(".",""))
#     except:
#         version = config.android_currReleaseVersion
#     if (invite is None) or (invite == '') or (invite in ['10252', '10224', '10244']):
#         return  '',''
#     if 'android' in pv:
#         #if (int(invite) > 5999 and version < currReleaseVersion) or (int(invite) < 5999 and version < 1501):
#         if version < config.android_currReleaseVersion:
#             #return "http://d.shengqianliao.com/?i=%s&v=%s&p=%s" % (str(invite),str(version),partner)
#             #return "http://d.shengqianliao.com/ShengQianLiao-i%s.apk" % str(invite)
#             return config.UPDATE_INFO, config.android_url % str(invite)
#     elif 's602' in pv:
#         if version < config.s602:
#             return '',config.s602_url
#     elif 's60' in pv:
#         if version < config.s60:
#             return '',config.s60_url
#     elif 'iphone' in pv:
#         if version < config.iphone:
#             return '',''#config.iphone_url
#     elif 'java' in pv:
#         if version < config.java:
#             return '',config.java_url
#     return  '',''
#
# def getPhone(sid):
#     if config.PHONE_DICT.has_key(sid):
#         return config.PHONE_DICT[sid]['mo']
#     return None
#
# def pin_deal(pin):
#     try:
#         pin = base64.decodestring(str(pin))
#         return dict(x.split('=') for x in pin.split('&'))
#     except:
#         print traceback.format_exc()
#         return False
#
# def clear_cache():
#     while True:
#         t = (datetime.datetime.now() - datetime.timedelta(seconds=300)).strftime('%Y%m%d%H%M%S')
#         for k, v in config.PHONE_DICT.iteritems():
#             if v['time'] < t:
#                 del config.PHONE_DICT[k]
#         time.sleep(60)
#
# def formatPhoneVersion(info):
#     info = info.strip().lower()
#     if 'iphone' in info:
#         info = 'iphone'
#     elif 'android' in info:
#         info = 'android'
#     elif 's60' in info:
#         if '5' in info:
#             info = 's605'
#         elif '2' in info:
#             info = 's602'
#         else:
#             info = 's603'
#     elif 'java' in info:
#         info = 'java'
#     elif 'wm' in info or 'windows' in info:
#         info = 'wm'
#     return info
#
#
#
# def asyncHTTPClient(url, method='GET'):
#     def __handle_request(response):
#         if response.error:
#             raise response.error
#         else:
#             return response.body
#
#     http_client = tornado.httpclient.AsyncHTTPClient()
#     http_client.fetch(url, __handle_request, method=method)
#
# if __name__ == '__main__':
#     #print(getPhoneByCMWap("DOxYzM4QDMxcDOwYCMEZWY2xWa=s"))
#     print(is_cmcc_number('13761075152'))
#     #print(getPhoneByCMWap("Wdr53budkJQ91VtY0ULRFIQVkLyJ3bzdXZ=I"))
#     #print getPhoneByCMWap("Wdr53budkJv1meslGbvECNw4CIjh2bw1XYpRmYlxyONB0UFlDIuYDMgs2VulGZ39ycOBCV2AjL7EHIopWLuNSKPBGcyVSY4AjL0U")
#     #print(getPhoneByCMWap("Wdr53budkJv1meslGbvECNw4CIjh2bw1XYpRmYlxyONB0UFlDIugDMgs2VulGZ39ycOBCV2AjL7EFIPdzV0YyOUBmcklWZ05zLuQDMgs0UDxzQ7ICIO5VRgQ0QSxDIuICM14DMyczNgskLF5CVDBFTgIyM14jLwMzN5IyOuAkTUVEIMNiUzAjLuAzM3AjM7kEIl1GZhlEIlNnblRicQByQ2AjL7ACIO5VR0QjLDByOuAkTUVCNw4SR=k"))
