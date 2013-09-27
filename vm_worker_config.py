# -*- coding: utf-8 -*-

import ConfigParser
import os
from singleton import Singleton
import logging
from tool import Tool
import time

logger = logging.getLogger()
handler=logging.FileHandler("vm_worker.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.NOTSET)

class VMWorkerConfig:
    def __init__(self):
        self.attributes = {}
        
    def Init(self, config_file_name):
	count = 0
        while not os.path.exists(config_file_name):
	    logger.error('can not find config file from cdrom: %d' %(count))
            count = count + 1
	    #if count == 6:
	    #	return False
	    time.sleep(2)
        
        cf = ConfigParser.ConfigParser()
        cf.read(config_file_name)
        value = cf.get('vm_worker', 'executor_endpoint')
        if(value == ''):
            logger.error('no executor_endpoint specified')
            return False
        self.attributes['executor_endpoint'] = value

        value = cf.get('vm_worker', 'port')
        if(value == ''):
            logger.error('no port specified')
            return False
        self.attributes['port'] = value

        value = cf.get('vm_worker', 'heartbeat_interval')
        if(value == ''):
            logger.error('no port specified')
            return False
        self.attributes['heartbeat_interval'] = value

        value = cf.get('vm_worker', 'ip')
        if(value == ''):
            logger.error('no ip specified')
            return False
        self.attributes['ip'] = value
        '''tool = Tool()
        if not tool.SetIP(value):
            logger.error('can not set ip')
            return False'''
        
        value = cf.get('vm_worker', 'job_id')
        if(value == ''):
            logger.error('no job_id specified')
            return False
        self.attributes['job_id'] = value

	value = cf.get('vm_worker', 'task_id')
        if(value == ''):
            logger.error('no task_id specified')
            return False
        self.attributes['task_id'] = value

	value = cf.get('vm_worker', 'interface')
        if(value == ''):
            logger.error('no interface specified')
            return False
        self.attributes['interface'] = value

	tool = Tool()
	ip = self.Get('ip')
	interface = self.Get('interface')
        if not tool.SetIP(ip, interface):
            logger.error('can not set ip')
            return False

        '''try:
            vfile = open('/root/vminfo.ini','w')
            vfile.write(value)
            vfile.close
        except OSError, e:
            logger.error(e)
            return False
        except IOError, e:
            logger.error(e)
            return False'''
        
        return True
        
    def Get(self, key):
        return self.attributes[key]

VMWorkerConfigI = Singleton(T=VMWorkerConfig)

if __name__ == '__main__':
    print "yes"
    VMWorkerConfigI.Instance().Init('/media/CDROM/conf')
    #VMWorkerConfigI.Instance().Init('conf')
    print 'vmworkerconfigI'
    print VMWorkerConfigI.Instance().Get('executor_endpoint')
    print VMWorkerConfigI.Instance().Get('ip')
    print VMWorkerConfigI.Instance().Get('port')
    print VMWorkerConfigI.Instance().Get('job_id')
    print VMWorkerConfigI.Instance().Get('heartbeat_interval')
    print VMWorkerConfigI.Instance().Get('task_id')
    print VMWorkerConfigI.Instance().Get('interface')
