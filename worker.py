#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Aurora Wu (wuxy91@gmail.com)'
__copyright__ = "Copyright (c) 2013 aurorawu.com"


import sys
import os
import redis
from rq import Worker, Queue, Connection

# listen = ['high', 'default', 'low', 'call_queue']

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        # worker = Worker(map(Queue, listen))
        # worker.work()
        qs = map(Queue, sys.argv[1:]) or [Queue()]
        worker = Worker(qs)
        worker.work()