# -*- coding: utf-8 -*-
#!/usr/bin/env python
# coding: utf-8

__author__ = "Sokos Lee (cnhawkwing@gmail.com)"
__copyright__ = "Copyright (c) 2013 SokosLee.com"

import sys
sys.path.append("../")

import eventsocket
from twisted.python import log
from twisted.internet import defer, reactor, protocol
import functools
import threading
import config
import redis
import time
import ujson

unique_uuid = {}
fs_ip = '211.155.86.239'
#fs_ip = 'hcsql.com'
#fs_ip = '127.0.0.1'
fs_password = "sokoslee.com"
fs_port = 8021

redisConn = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

def async_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        my_thread.start()
    return wrapper

class MyProtocol(eventsocket.EventProtocol):
    def __init__(self):
        self.job_uuid = {}
        eventsocket.EventProtocol.__init__(self)

    @defer.inlineCallbacks
    def authRequest(self, ev):
        # Try to authenticate in the eventsocket (Inbound)
        # Please refer to http://wiki.freeswitch.org/wiki/Mod_event_socket#auth
        # for more information.
        try:
            yield self.auth(self.factory.password)
        except eventsocket.AuthError, e:
            self.factory.continueTrying = False
            self.factory.ready.errback(e)

        # Set the events we want to get.
        yield self.eventplain("BACKGROUND_JOB CHANNEL_HANGUP CHANNEL_HANGUP")

        # Tell the factory that we're ready. Pass the protocol
        # instance as argument.
        self.factory.ready.callback(self)

    def make_call(self, ext, context):
        def _success(ev, data):
            print('ev : data')
            print(ev, data)
            self.job_uuid[ev.Job_UUID] = data

        def _failure(error, deferred):
            print(redisConn.get('call_count'))
            print('error : deferred')
            print(error, deferred)
            deferred.errback(error)

        deferred = defer.Deferred()
        d = self.bgapi("originate %s %s" % (ext, context))
        d.addCallback(_success, (deferred, ext, context))
        d.addErrback(_failure, deferred)

        return deferred

    def show_channels_count(self):
        def _success(ev, data):
            self.job_uuid[ev.Job_UUID] = data
            print(ev, data)

        def _failure(error, deferred):
            print(redisConn.get('call_count'))
            deferred.errback(error)

        deferred = defer.Deferred()
        d = self.bgapi("show channels count as json")
        d.addCallback(_success, (deferred, '', ''))
        d.addErrback(_failure, deferred)

        return deferred

    def onChannelHangup(self, ev):#CHANNEL_HANGUP
        # if redisConn:
        #     call_count = redisConn.get('call_count')
        #     if not call_count or call_count < 1:
        #         call_count = 0
        #     else:
        #         call_count -= 1
        #     redisConn.set('call_count',int(call_count))
        pass

    def onBackgroundJob(self, ev):
        data = self.job_uuid.pop(ev.Job_UUID, None)
        if data:
            print(data)
            print(ev)
            if 'row' not in ev.rawresponse:
                response, content = ev.rawresponse.split()
                if response == "+OK":
                    unique_uuid[content] = data
                else:
                    d, ext, context = data
                    d.errback(Exception("cannot make call to %s: %s" % (ext, content)))
            else:
                unique_uuid[ev.Job_UUID] = data
                if redisConn:
                    _ev = ujson.loads(str(ev.rawresponse))

                    redisConn.set('call_count',int(_ev['row_count']) * 2)
                    print(redisConn.get('call_count'))
                    d, ext, context = data
                    d.errback(Exception(redisConn.get('call_count')))
                    #raise Exception(redisConn.get('call_count'))

    def onChannelHangup(self, ev):
        data = unique_uuid.pop(ev.Unique_ID, None)
        if data:
            print(redisConn.get('call_count'))
            d, ext, context = data
            start_usec = float(ev.Caller_Channel_Answered_Time)
            end_usec = float(ev.Event_Date_Timestamp)
            duration = (end_usec - start_usec) / 1000000.0
            d.callback("%s hang up: %s (call duration: %0.2f)" % \
                (ext, ev.Hangup_Cause, duration))


class MyFactory(protocol.ReconnectingClientFactory):
    maxDelay = 15
    protocol = MyProtocol

    def __init__(self, password):
        self.ready = defer.Deferred()
        self.password = password


factory = MyFactory(password=fs_password)
reactor.connectTCP(fs_ip, fs_port, factory)

#@async_function
def make_call(caller, called, caller_uid, gateway, fee=0.12):
    try:
        @defer.inlineCallbacks
        def run(caller, called, caller_uid, gateway):
            # Wait for the connection to be established
            try:
                client = yield factory.ready
            except Exception, e:
                log.err("cannot connect: %s" % e)
                defer.returnValue(None)

            # Place the call
            try:
                # Don't forget to replace ext with your own destination number.
                # You may also place the call to an eventsocket (Outbound) server,
                # like our server.tac using:
                #  context="'&socket(127.0.0.1:8888 async full)'")
                log.msg('Begin Make Call')

                ext = "{uid=%s,cdr_caller=%s,cdr_called=%s,billing_reason=common,mynibble_rate=%s," \
                      "mynibble_increment=60,mynibble_account=%s,call_timeout=40," \
                      "nibble_selfrate=%s,mynibble_extension=%s,bill_destination=%s,instant_ringback=true," \
                      "domain_name=%s,origination_caller_id_number=%s,sched_hangup='+4500 allotted_timeout'," \
                      "continue_on_fail=false,transfer_ringback=/usr/local/freeswitch/sounds/calling.wav," \
                      "hangup_after_bridge=true,bridge_early_media=true," \
                      "origination_caller_id_name=%s,origi*_caller_id_number=1111," \
                      "effective_caller_id_number=222,ignore_early_media=true}sofia/gateway/%s/%s " \
                      " " \
                      % (caller_uid, caller, called, fee, caller_uid, fee, caller_uid, fee, fs_ip,
                         caller_uid, caller_uid,gateway , caller)
                #ringback=/usr/local/freeswitch/sounds/calling.wav,

                log.msg('before_bridge: %s %s %s %s %s' % (caller, called, caller_uid, gateway, fee))

                context = " &bridge([originate_timeout=40]" \
                          "sofia/gateway/%s/%s)" % (gateway, called)

                if context:
                    result = yield client.make_call(
                        ext=ext,
                        context=context)
                else:
                    result = yield client.make_call(ext=ext)
                log.msg(result)
                log.msg('After Make Call')
            except Exception, e:
                #print(e)
                log.err(e)

        run(caller, called, caller_uid, gateway).addCallback(lambda ign: reactor.stop())
        reactor.run()

    except Exception, e:
        log.err(e)
    finally:
        pass
        # if redisConn:
        #     call_count = redisConn.get('call_count')
        #     if not call_count or call_count < 1:
        #         call_count = 0
        #     else:
        #         call_count -= 2
        #     redisConn.set('call_count',int(call_count))

def show_channels_count():
    try:
        @defer.inlineCallbacks
        def run():
            client = None
            # Wait for the connection to be established
            try:
                client = yield factory.ready
            except Exception, e:
                log.err("cannot connect: %s" % e)
                defer.returnValue(None)

            # Place the call
            try:
                if client:
                    result = yield client.show_channels_count()
                    print(result)
            except Exception, e:
                print(e)
                log.err(e)

        run().addCallback(lambda ign: reactor.stop())
        reactor.run()

    except Exception, e:
        log.err(e)
    finally:
        pass



# {billing_reason=common,mynibble_rate=100,mynibble_increment=60,mynibble_account=5001,nibble_selfrate=100,mynibble_extension=5001,bill_destination=1000,domain_name=192.168.1.199,origination_caller_id_number=1000,origination_caller_id_name=1000}user/1000 &bridge(user/1002)
# {origi*_caller_id_number=1111,effective_caller_id_number=222,ignore_early_media=true}sofia/gateway/gw1/0153XXXXXX
if __name__ == "__main__":
    log.startLogging(sys.stdout)
    caller = '013480718600' # 015889631135(壮欧)     013530980182（晓阳）  015875555285（阿东） 015914090951（周礼）
    called = '013719183834' # 013798390704（世忠）   013480718600（卫斌）  015815568412（小谢） 013502869446（孙总）
    caller_uid = '546605'
    gateway = 'gwhu'#h323   gwhu
    print(len(sys.argv))
    if len(sys.argv) < 2:
        #make_call(caller, called, caller_uid, gateway)
        #pass
        show_channels_count()
    else:
        #make_call('013719183834', '013530980182', caller_uid, gateway)
        pass