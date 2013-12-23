#!/usr/local/bin/python
#coding=utf-8
import urllib2, httplib, urllib
import logging, traceback, datetime, random
import config, tool

logger = tool.mylog(__name__)


def rc4(data, key):
    x = 0
    box = range(256)
    for i in range(256):
        x = (x + box[i] + ord(key[i % len(key)])) % 256
        box[i], box[x] = box[x], box[i]
    x = 0
    y = 0
    out = []
    for char in data:
        x = (x + 1) % 256
        y = (y + box[x]) % 256
        box[x], box[y] = box[y], box[x]
        out.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))
    return ''.join(out)


def hex2str(s):
    '''16进制转字符串'''
    if s[:2] == '0x' or s[:2] == '0X':
        s = s[2:]
    res = ""
    for i in range(0, len(s), 2):
        hex_dig = s[i:i + 2]
        res += (chr(int(hex_dig, base=16)))
    return res


def str2hex(string):
    '''字符串转16进制'''
    res = ""
    for s in string:
        hex_dig = hex(ord(s))[2:]
        if len(hex_dig) == 1:
            hex_dig = "0" + hex_dig
        res += hex_dig
    return res


def getAmsResp(amsFunc, params,timeout=10):
    try:
        #httpConn = httplib.HTTPConnection(AMS_HOST, AMS_PORT)
        #httpConn.request("POST", amsFunc, params + "&" + getAmsSign(),{"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"})
        #f = httpConn.getresponse()
        url = "http://" + config.AMS_HOST + ":" + str(config.AMS_PORT) + amsFunc + "?" + params + "&" + getAmsSign()
        res = tool.http_get(url,timeout)
        # f = urllib2.urlopen(url)
        # res = f.read()
        # f.close()
        logger.info(u"AMS URL:%s;结果:%s" % (url, res))
        return urlCode2Dict(res)
    except:
        logger.error("getAmsResp Fail: %s %s" % (url, traceback.format_exc()))
        return {"code": "9999"}


def urlCode2Dict(result):
    '''ams返回url串转换成dict'''
    return dict(x.split('=') for x in result.split('&'))


def getRand():
    n = datetime.datetime.now().strftime("%H%M%S")
    m = str(random.randint(1000, 9999))
    return n + m


def getAmsSign():
    macdate = datetime.datetime.now().strftime("%Y%m%d")
    macrand = getRand()
    mac = tool.md5_password(config.LOCALHOST + macdate + macrand + config.MAC_KEY)
    mac_dict = {"macip": config.LOCALHOST, \
                "macdate": macdate, \
                "macrand": macrand, \
                "mac": mac}
    return urllib.urlencode(mac_dict)


def info(accounttype, account, brandid='kc'):
    '''查询kc/手机/密码'''
    param = urllib.urlencode({"accounttype": accounttype, \
                              "account": account, "bid": brandid})
    return getAmsResp("/ams2/info.act", param,timeout=40)


def login(loginType, account, password, loginfrom, ip, brandid='kc', pform='', psystem='', ptype='', cversion=''):
    '''登录认证'''
    param = urllib.urlencode({"loginType": loginType, \
                              "account": account, \
                              "password": password, \
                              "from": loginfrom, \
                              "ip": ip, \
                              "bid": brandid, \
                              "pform": pform, \
                              "psystem": psystem, \
                              "ptype": ptype, \
                              "cversion": cversion
    })
    return getAmsResp("/ams2/login.act", param,timeout=30)


def choose(ip):
    '''选号'''
    return getAmsResp("/ams2/choose.act", "ip=%s" % ip)


def kcreg(uid, password, random, invitedby, invitedflag, regfrom):
    '''注册'''
    return getAmsResp("/ams2/kcreg.act", "uid=%s&password=%s&random=%s&invitedby=%s&invitedflag=%s&from=%s" % uid,
                      password, random, invitedby, invitedflag, regfrom)


def automobilereg(number, invitedby, invitedflag, regfrom, ip, ext='', brandid='kc'):
    '''自动注册'''
    return getAmsResp("/ams2/automobilereg.act", "number=%s&invitedby=%s&invitedflag=%s&from=%s&ip=%s&ext=%s&bid=%s"
                                                 % (number, invitedby, invitedflag, regfrom, ip, ext, brandid),timeout=40)


def mobilereg(number, invitedby, invitedflag, regfrom, ip, ext='', brandid='kc'):
    '''短信注册'''
    return getAmsResp("/ams2/mobilereg.act", "number=%s&invitedby=%s&invitedflag=%s&from=%s&ip=%s&ext=%s&bid=%s"
                                             % (number, invitedby, invitedflag, regfrom, ip, ext, brandid),timeout=40)


def unbind(number, uid, password):
    '''绑定请求'''
    return getAmsResp("/ams2/unbind.act", "number=%s&uid=%s&password=%s" % (number, uid, password),timeout=40)


def bindapply(number, uid, password, brandid='kc'):
    '''绑定请求'''
    return getAmsResp("/ams2/bindapply.act", "number=%s&uid=%s&password=%s&bid=%s" %
                                             (number, uid, password, brandid),timeout=40)


def bindsubmit(uid, number, verifyCode, brandid='kc'):
    '''提交绑定'''
    return getAmsResp("/ams2/bindsubmit.act", "number=%s&uid=%s&verifyCode=%s&bid=%s" %
                                              (number, uid, verifyCode, brandid),timeout=40)


def delacctnotify(accounts):
    '''APS删除账户通知'''
    return getAmsResp("/ams2/delacctnotify.act", "from=APS&accounts=%s" % accounts)


def changepwd(uid, oldpwd, newpwd):
    '''修改密码'''
    return getAmsResp("/ams2/changepassword.act", "uid=%s&oldpassword=%s&newpassword=%s" % (uid, oldpwd, newpwd))


def check_pwd(type, account, md5pwd):
    if not account or account == 'null' or not account.isdigit():
        return {"result": 1}
    if len(str(account)) == 11 and str(account)[0] == '1':
        type = 'mobile'
    res = info(type, account)
    if 'code' in res and str(res['code']) == '0':
        pwd = res['password']
        phone = res['number']
        uid = res['uid']
        if tool.md5_password(rc4(hex2str(pwd), config.AMS_KEY)) == md5pwd:
            return {"result": 0, "kcid": uid, "phone": phone}
        else:
            return {"result": 2}
    return {"result": 1}


def getInfo(account_type, account, brandid='kc'):
    kcid, mobile, password = '', '', ''
    if not account or account == 'null' or not str(account).isdigit():
        return kcid, mobile, password
    if len(str(account)) == 11 and str(account)[0] == '1':
        account_type = 'mobile'
    res = info(account_type, account, brandid)
    if 'code' in res and str(res['code']) == '0':
        kcid = res['uid']
        mobile = res['number']
        password = rc4(hex2str(res['password']), config.AMS_KEY)
    return kcid, mobile, password


if __name__ == '__main__':
    #print automobilereg('13430789767', '9646', '1', 'mobile', '1.1.1.1')
    pass

