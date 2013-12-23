#coding=UTF-8
from datetime import datetime
import tool
import config
import ujson as json


class Recharge:
    def __init__(self, logger, redis_conn, recharge_queue):
        self.logger = logger
        self.redis_conn = redis_conn
        self.queue = recharge_queue

    def pay(self, src, uid, paytype, goodstype, money, cardno, cardpwd, pv, v, buynum=1, callback=None):
        if not callback:
            callback = tool.return_values
        if paytype in ['203']:
            paytype='215'
        #if paytype in ['36','213']:
        #    paytype='10'
        #elif paytype in ['29','211']:
        #    paytype='8'
        #elif paytype in ['203','215']:
        #    paytype='12'
        result = {"result": "500", "reason": u"server error"}
        goodstype = '2'
        self.logger.info(u"收到充值请求：kc==%s，产品类型==%s，金额==%s，卡号==%s，密码==%s，版本==%s，版本号==%s" %(uid, goodstype, money, cardno, cardpwd,pv,v))
        ordersn = datetime.now().strftime('%Y%m%d%H%M%S') + uid
        #money = "100"
        sign = tool.md5_password('src=%s&ordersn=%s&uid=%s&key=%s' % (src, ordersn, uid, config.chargekey))
        url = config.pay_addr % (src, ordersn, uid, paytype, goodstype, money, cardno, cardpwd, sign, buynum)
        #res = tool.http_get(url, timeout=50)
        res = self.queue.enqueue(tool.http_get, url, 50)
        self.logger.info(u"调充值接口:%s,返回结果:%s" % (url, res))

        if paytype not in ['16']:
            res = json.loads(res)
            len_res = len(res)
            i = 1
            resp = r'{'
            for s in res:
                resp += r'"' + s + '"' + ' : "' + str(res[s]) + '"'
                if i < len_res:
                    resp += ','
                i += 1
            resp += r'}'
            result = json.loads(resp)
            result["orderid"] = str(result.get("orderid", ""))
        else:
            result = res
        return callback(result)

