#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Aurora Wu (wuxy91@gmail.com)'
__copyright__ = "Copyright (c) 2013 aurorawu.com"


import MySQLdb.cursors


#生产环境
isDebug = True

#运行端口
server_port = 9999

#数据库连接配置
# KC_DB = {"host":"192.168.1.199","user":"root","passwd":"cnhawk.org","db":"KC_DB","charset":"utf8"}
# KC_DB_FIELD_DICT = {"host":"192.168.1.199","user":"root","passwd":"cnhawk.org","db":"KC_DB","charset":"utf8",'cursorclass':MySQLdb.cursors.DictCursor}
# KC_DB_BACK = {"host":"192.168.1.199","user":"root","passwd":"cnhawk.org","db":"KC_DB","charset":"utf8"}
DB_mobile = {"host": "192.168.1.199", "user": "root", "passwd": "cnhawk.org", "db": "mobile", "charset": "utf8",
             'cursorclass': MySQLdb.cursors.DictCursor}

#sentry client key
raven_client = 'http://a5fe8f10b9584cc9aadfa4859ff2b822:3d144177e4ed4b2cb878e1e327aa824f@sentry.shengqianliao.com/3'

#手机客户端http请求验证密钥
key = "hc_call@5tshow.com"
push_key = "6RxaD|-Vp=@w }j!PGsaD#7o-ecgroWN rt9>3JF7EY%|9YSxSPxx!jY,G;%r8-["

is_use_hu_gateway = True

#新回拨KEY
NEW_CB_KEY = 'keepc'

'''bc系统接口配置'''
#余额查询接口访问密码
kckey = "guoling!@#456"

#查询余额专用wallet
chkfee_server = "127.0.0.1:9998"

#AMS配置信息
AMS_KEY = "1bb762f7ce24ceee"
AMS_HOST = "hcsql.com"
# AMS_HOST = "localhost"
AMS_PORT = 8080
MAC_KEY = "0859db5b7b8ae8fe4b0d344af4d11199"
LOCALHOST = "113.11.199.87"

FirstLoginMsg = u"恭喜您，注册成功！您将获赠最长60分钟的免费通话时长，有效期至%s，快去体验吧！"
NormalLoginMsg = u"谢谢你再次使用！您还有通话时长%(calltime)s分钟，有效期至%(valid_date)s"

"""API URL"""
#新回拨接口URL
new_cb_url1 = "http://121.14.118.31:8888/callback?sn=%s&kcid=%s&caller=%s&called=%s&ref=%s&display=%s&resv=%s&sign=%s&brand=%s"
new_cb_url2 = "http://121.14.118.31:8888/callback?sn=%s&kcid=%s&caller=%s&called=%s&ref=%s&display=%s&resv=%s&sign=%s&brand=%s"
new_cb_url3 = "http://121.14.118.31:8888/callback?sn=%s&kcid=%s&caller=%s&called=%s&ref=%s&display=%s&resv=%s&sign=%s&brand=%s"
new_cb_url4 = "http://121.14.118.31:8888/callback?sn=%s&kcid=%s&caller=%s&called=%s&ref=%s&display=%s&resv=%s&sign=%s&brand=%s"
new_cb_url5 = "http://121.14.118.31:8888/callback?sn=%s&kcid=%s&caller=%s&called=%s&ref=%s&display=%s&resv=%s&sign=%s&brand=%s"

#查询余额
balance_url = "http://%s/can_call_2?uid=%s&sign=%s"
