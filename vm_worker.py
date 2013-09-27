#-*- coding:utf8 -*-
import sys
import os
import string
#python不支持gen-py 中的特殊字符,所以将文件夹的名字改为gen
#主要是我想取文件名字为vm_worker.py，这个与自动生成的文件名冲突了
#sys.path.append('/root/vm_worker_linux/')
sys.path.append('./gen')

import logging

#文件名不能起跟vm_worker一样的
from gen.vm_worker import VMWorker
from gen.vm_worker.ttypes import *
# TODO
from gen.executor import Executor
from gen.executor.ttypes import *

from thrift.transport.TTransport import TTransportException

from rpc import Rpc
from vm_worker_config import VMWorkerConfigI
from vm_worker_service import VMWorkerHandler
from vm_worker_thread import HeartbeatProcessor
import threading

#global state
if __name__ == '__main__':
    #初始化日志
    logger = logging.getLogger('vm_worker')
    hdlr = logging.FileHandler('vm_worker.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.NOTSET)
    ##TODO
    #初始化vm worker的配置
    #if not VMWorkerConfigI.Instance().Init('conf'):
    if not VMWorkerConfigI.Instance().Init('/media/CDROM/conf'):
        logger.error('read vm worker config error')
        exit
    port_str = VMWorkerConfigI.Instance().Get('port')    
    port = string.atoi(port_str)
    #启动心跳线程
    heartbeat_t = threading.Thread(target=HeartbeatProcessor)
    heartbeat_t.start()
    #print "yes"
    #启动自身的rpc服务器
    Rpc(T = VMWorkerHandler, P = VMWorker.Processor).Listen(port)
