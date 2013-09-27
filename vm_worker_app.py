#-*- coding:utf8 -*-:
import sys
import os
import threading
import subprocess 
import time
import string
import logging

#sys.path.append('./gen')

# 导入thrift定义的模块
from gen.vm_worker import VMWorker  # vm service
from gen.vm_worker.ttypes import *  # vm struct

from gen.executor.Executor import Client
from gen.executor.ttypes import * # worker struct

from vm_worker_config import VMWorkerConfigI
from thrift.transport.TTransport import TTransportException

from rpc import Rpc
# 日志信息存入vm_worker.log
logger = logging.getLogger()
handler=logging.FileHandler("vm_worker.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.NOTSET)

#周期性运行应用
def IntervalRunWorker(id, name, install_dir, exe, argument, interval):
        #周期启动应用程序
        count = 0
        while(True):
            count = count + 1
            print count #记录应用轮询次数
            try:
                    state_file = open(install_dir + '/daemon', 'r')
                    content = state_file.read()
                    state_file.close()
                    if content == "stopped":
                        print "stop ok"
                        return True
            except OSError, e:
		logger.error(e)
                continue
            except IOError, e:
		logger.error(e)
                continue
            exe_path = install_dir + "/" + exe
            cmd = exe_path + ' ' + argument
            interval_p = subprocess.Popen(cmd, shell = True, cwd = install_dir)
            rtn = interval_p.wait()
	    if rtn != 0:
		vmworker_app = VMWorkerApp()
		vmworker_app.SetHbAppState(id, name, AppState.APP_FAILED, 2)	
		logger.error('app run error ' + str(rtn))
		continue
            time.sleep(interval)

class VMWorkerApp:
    """
    虚拟机应用类
    """
    #定义应用心跳类为成员对象
    global vm_hbapp_info
    vm_hbapp_info = VM_HbAppInfo()
    vm_hbapp_info.id = 0
    vm_hbapp_info.app_name = " "
    vm_hbapp_info.state = AppState.APP_NOTFOUND
    vm_hbapp_info.error_id = 0
    vm_hbapp_info.app_install = False
    
    #定义应用类为成员对象
    global vm_app_info
    vm_app_info = VM_AppInfo()	

    def __init__(self):        
	pass

    #设置应用心跳类信息
    def SetHbAppState(self, id, name, state, error_id):
	vm_hbapp_info.id = id
	vm_hbapp_info.name = name
	vm_hbapp_info.state = state
	vm_hbapp_info.error_id = error_id
	return True
    
    #获取应用心跳类信息
    def GetHbAppState(self):
  	return vm_hbapp_info

    #设置应用类信息
    def SetAppInfo(self,app_info):
	vm_app_info.id = app_info.id
	vm_app_info.name = app_info.name
	vm_app_info.source = app_info.app_source
	vm_app_info.install_dir = app_info.install_dir
	vm_app_info.exe = app_info.exe
	vm_app_info.argument = app_info.argument
	return True

    #安装应用
    def AppInstallWorker(self, app_id, source, install_dir):
	job_id_str = VMWorkerConfigI.Instance().Get('job_id')
        task_id_str = VMWorkerConfigI.Instance().Get('task_id')
        job_id = string.atoi(job_id_str)
        task_id = string.atoi(task_id_str)

	executor_endpoint = VMWorkerConfigI.Instance().Get('executor_endpoint')
	try :
                executor_client = Rpc(T = Client).GetProxy(executor_endpoint)
                executor_client.AppInstalled(job_id, task_id, app_id)
        except TTransportException, e:
                logger.error(e)
		return False
	return True

    #运行应用
    def AppRunWorker(self, id, name, install_dir, exe, argument, run_type, interval):
	self.SetHbAppState(id, name, AppState.APP_ONLINE, 0)
        if run_type == 'normal':
            exe_path = install_dir + "/" + exe
	    if not os.path.exists(exe_path):
		self.SetHbAppState(id, name, AppState.APP_FAILED, 1)
		logger.error('can not found app file')
		return False
            cmd = exe_path + ' ' + argument
            print "cmd: ", cmd
            p = subprocess.Popen(cmd, shell = True, cwd = install_dir)
            rtn = p.wait()
            ## 监控应用进程，异常则做相应的处理
	    if rtn != 0:
		self.SetHbAppState(id, name, AppState.APP_FAILED, 2)
		logger.error(name + ' app run error ' + str(rtn))
		return False
            ###
	    self.SetHbAppState(id, name, AppState.APP_FINISHED, 0)
            print "start running app over"
	    return True

        elif run_type == 'daemon':
            print "daemon"
	    exe_path = install_dir + "/" + exe
	    if not os.path.exists(exe_path):
                self.SetHbAppState(id, name, AppState.APP_FAILED, 1)
		logger.error('can not found app file')
                return False
            try:
                #写个文件表示应用正在运行
                state_file = open(source + '/daemon','w')
                state_file.write('running')
                state_file.close()
            except OSError, e:
                logger.error(e)
                return False
            except IOError, e:
                logger.error(e)
                return False
            #启动周期运行应用线程
            interval_run_worker = threading.Thread(target = IntervalRunWorker, args = (id, name, install_dir, exe, argument, interval))
            interval_run_worker.start()
            #守护周期运行线程
	    while(True):
                if not interval_run_worker.is_alive():
                    try:
                        state_file = open(source + '/daemon', 'r')
                        content = state_file.read()
                        state_file.close()
                        if content == 'stopped':
                            return True
                    except OSError, e:
                        logger.error(e)
                        #return False
                        continue
                    except IOError, e:
                        logger.error(e)
                        #return False
                        continue
                    interval_run_worker = threading.Thread(target = IntervalRunWorker, args = (id, name, install_dir, exe, argument, interval))
                    interval_run_worker.start()
                time.sleep(interval)
            return True

        else:
            print "unknown type " + run_type
	    logger.error('unknown type ' + run_type)
            return False

    #停止daemon应用
    def AppStopWorker4Daemon(self, id, args):
	if id != vm_app_info.id:
                self.SetHbAppState(id, " ", AppState.APP_FAILED, 3)
                logger.error("the app id is %d but can not found %d app" %(vm_app_info.id, id))
                return False
	name = vm_app_info.name
	install_dir = vm_app_info.install_dir
        try:
                #写个文件表示应用正在运行
                state_file = open(install_dir + '/daemon','w')
                state_file.write('stopped')
                state_file.close()
        except OSError, e:
                logger.error(e)
                return False
        except IOError, e:
                logger.error(e)
                return False
        print"stop app ok"
	self.SetHbAppState(id, name, AppState.APP_FINISHED, 0)
        return True

    #停止normal应用
    def AppStopWorker(self, id, stop):
	if id != vm_app_info.id:
		self.SetHbAppState(id, " ", AppState.APP_FAILED, 3)
		logger.error("the id can not found app")
		return False
	name = vm_app_info.name
        install_dir = vm_app_info.install_dir
	# argument = vm_app_info.argument
        exe_path = install_dir + "/" + stop
        cmd = exe_path # + ' ' + argument
        print "cmd: ", cmd
        logger.error("cmd: " + cmd) 
        p = subprocess.Popen(cmd, shell = True, cwd = install_dir)
        rtn = p.wait()
	if rtn != 0:
		self.SetHbAppState(id, name, AppState.APP_FAILED, 2)
		logger.error(name + ' app stop error ' + str(rtn))
                return False
	self.SetHbAppState(id, name, AppState.APP_FINISHED, 0)
	print"stop app ok"
        return True

