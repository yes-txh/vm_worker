#-*- coding:utf8 -*-
import sys
import os
import threading
import subprocess
import time

from thrift.transport.TTransport import TTransportException

# 导入thrift定义的模块
from gen.vm_worker import VMWorker  # service
from gen.vm_worker.ttypes import *  # struct
from gen.executor.ttypes import * # worker struct

#导入app类
from  vm_worker_app import VMWorkerApp

class VMWorkerHandler:
    """
    负责处理rpc相关
    """
    def __init__(self):
        pass
    
    #初始化app类
    global vm_worker_app
    vm_worker_app = VMWorkerApp()

    # To test
    def test(self, test_id, test_str):
	if(test_id == 1):
		print test_str
	else:
		print "hello world"
	return 1
    
    #install app file to VM
    def InstallApp(self, app_info):
        print "install app"
	app_install_worker = threading.Thread(target = vm_worker_app.AppInstallWorker, args =(app_info.id, app_info.app_source, app_info.install_dir))
        app_install_worker.start()
	return True

    #start running app on VM
    def StartApp(self, app_info):	
	print "start app"
	#初始化vm_app_info
	rtn = vm_worker_app.SetAppInfo(app_info)
	if rtn != True:
		print "set app info error"
		return False
	#使用线程启动应用程序，防止executor阻塞
	app_run_worker = threading.Thread(target = vm_worker_app.AppRunWorker, args =(app_info.id, app_info.name, app_info.install_dir, app_info.exe, app_info.argument, app_info.run_type, app_info.interval)) 
	app_run_worker.start()
	return True	

    #stop normal running app on VM
    def StopApp(self, id, stop):
        print "stop normal app"
        #使用线程启动应用程序，防止executor阻塞
        app_stop_worker = threading.Thread(target = vm_worker_app.AppStopWorker, args =(id, stop))
        app_stop_worker.start()
        return True
	
    #stop normal running app on VM
    def StopApp4Daemon(self, id):
	print "stop daemon app"
	args = " "
        #使用线程启动应用程序，防止executor阻塞
        app_stop_worker_daemon = threading.Thread(target = vm_worker_app.AppStopWorker4Daemon, args =(id, args))
        app_stop_worker_daemon.start()
        return True
