# -*- coding: utf-8 -*-
#!/usr/bin/env python
# coding: utf-8

__author__ = "Sokos Lee (cnhawkwing@gmail.com)"
__copyright__ = "Copyright (c) 2012 SokosLee.com"


import traceback
from raven.contrib.tornado import SentryMixin
import tornado
import tornado.web
import redis
import rq


class BaseHandler(SentryMixin, tornado.web.RequestHandler):
    def prepare(self):
        try:
            brand_id = self.get_argument('brandid', 'kc')
            self.bid = 'kc' if brand_id == 'ld' else brand_id
            self.httpHeaders = self.request.headers
        except:
            self.bid = 'kc'
        finally:
            self.base_domain = self.request.protocol + '://' + self.request.host

    @property
    def redis_conn(self):
        return redis.Redis(connection_pool=self.application.redis_pool)

    def make_queue(self, queue_name='default'):
        conn = self.redis_conn
        queue = rq.Queue(queue_name, connection=conn)
        return queue.from_queue_key(queue_key=queue.key, connection=conn)

    @property
    def query_conn(self):
        return self.application.read_pool.connection()

    @property
    def update_conn(self):
        return self.application.write_pool.connection()

    @property
    def logger(self):
        return self.application.logger

    def write_error(self, status_code, **kwargs):
        if self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["%s<br/>" % line for line in traceback.format_exception(*exc_info)])
            request_info = ''.join(["<strong>%s</strong>: %s<br/>" %
                                    (k, self.request.__dict__[k]) for k in self.request.__dict__.keys()])
            error = exc_info[1]

            self.set_header('Content-Type', 'text/html')
            self.finish("""<html>
                             <title>%s</title>
                             <body>
                                <h2>Error</h2>
                                <p>%s</p>
                                <h2>Traceback</h2>
                                <p>%s</p>
                                <h2>Request Info</h2>
                                <p>%s</p>
                             </body>
                           </html>""" % (error, error,
                                         trace_info, request_info))
