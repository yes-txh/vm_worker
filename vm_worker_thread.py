# -*- coding:utf-8 -*-
import time
import threading
import string
import logging
from gen.executor.Executor import Client
from gen.executor.ttypes import *
from rpc import Rpc
from tool import Tool
from vm_worker_app import VMWorkerApp
from vm_worker_config import VMWorkerConfigI
from thrift.transport.TTransport import TTransportException

logger = logging.getLogger()
handler=logging.FileHandler("vm_worker.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.NOTSET)

def HeartbeatThread():
    while True:
	#print "yes world"
	vm_app = VMWorkerApp()
	hb_app_info = VM_HbAppInfo()
	hb_app_info = vm_app.GetHbAppState()
	if hb_app_info.state == AppState.APP_ONLINE:
		app_running = True
	else:
		app_running = False
	
	job_id_str = VMWorkerConfigI.Instance().Get('job_id')
	task_id_str = VMWorkerConfigI.Instance().Get('task_id')
	job_id = string.atoi(job_id_str)
	task_id = string.atoi(task_id_str)
	
	interface = VMWorkerConfigI.Instance().Get('interface')
	executor_endpoint = VMWorkerConfigI.Instance().Get('executor_endpoint')
	hb_interval_str = VMWorkerConfigI.Instance().Get('heartbeat_interval')
	hb_interval = string.atoi(hb_interval_str)
	
	hb_vm_info = VM_HbVMInfo()
	hb_vm_info.job_id = job_id
	hb_vm_info.task_id = task_id
        tool = Tool()
        hb_vm_info.cpu_usage = tool.GetCpuUsage()
        hb_vm_info.memory_usage = tool.GetMemoryUsage()
	hb_vm_info.bytes_in = tool.GetInNetUsage(interface) 
	hb_vm_info.bytes_out = tool.GetOutNetUsage(interface) 
        hb_vm_info.state = VMState.VM_SERVICE_ONLINE
        hb_vm_info.app_running = app_running 
	hb_vm_info.hb_app_info = hb_app_info
	try :
		executor_client = Rpc(T = Client).GetProxy(executor_endpoint) 
                executor_client.SendVMHeartbeat(hb_vm_info)
	except TTransportException, e:
		logger.error(e)
		time.sleep(2)
		continue
	time.sleep(hb_interval)

def HeartbeatProcessor():
    #create thread
    heartbeat_thread = threading.Thread(target=HeartbeatThread)
    heartbeat_thread.start()
    count_num = 0
    #daemon thread
    while True:
	if not heartbeat_thread.is_alive():
		 heartbeat_thread = threading.Thread(target=HeartbeatThread)
	         heartbeat_thread.start()
	print count_num
	count_num = count_num + 1
	time.sleep(10)

if __name__ == '__main__':
    print "yes"
    if not VMWorkerConfigI.Instance().Init('/root/work/vm_worker_master_test/vm_linux/conf'):
        logger.error('read vm worker config error')
        exit

    HeartbeatThread()
	
