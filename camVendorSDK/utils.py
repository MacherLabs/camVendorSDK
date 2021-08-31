import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from constants import IP_CAM_CHANNELS_TEMPLATE
from constants import IP_CAM_DEVICE_INFO_TEMPLATES
import socket
import requests
from requests.auth import HTTPDigestAuth
from requests.auth import HTTPBasicAuth
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Loaded " + __name__)
import cv2
import numpy as np
import xml.etree.cElementTree as ET
import re

def is_connected():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        pass
    return False

def getImageByUrl(url,user,passwd,authType='digest',format='jpeg'):
    auth=None
    if authType=='basic':
        auth=HTTPBasicAuth(user,passwd)
    elif authType=='digest':
        auth=HTTPDigestAuth(user,passwd)
    
    try:
        response = requests.get(url,auth=auth,timeout=5)
        response.raise_for_status()
        data = response.content
        if format=='numpy':
            arr = np.asarray(bytearray(data), dtype=np.uint8)
            img = cv2.imdecode(arr, -1)
            return img
        else:
            return response.content
 
    except Exception as e:
        logger.error("failed to fetch snapshot-{}".format(str(e)))
        return None
    
  
    
def getChannels(ip,port,user,passwd,vendor,authType='digest'):
    auth=None
    if authType=='basic':
        auth=HTTPBasicAuth(user,passwd)
    elif authType=='digest':
        auth=HTTPDigestAuth(user,passwd)
    url = IP_CAM_CHANNELS_TEMPLATE[vendor]
    url=url.format("http",ip,port)
    try:
        device_info=get_device_info(ip=ip,port=port,user=user,passwd=passwd,vendor=vendor,authType=authType)
        response = requests.get(url,auth=auth,timeout=5)
        response.raise_for_status()
        out={"deviceInfo":device_info,"channelList":[]}
        channelList=[]
        if vendor =='hikvision':
            xmlstring = re.sub(' xmlns="[^"]+"', '', response.text, count=1000)
            tree = ET.fromstring(xmlstring)
            for node in tree.getchildren():
                channelObj={}
                for subnode in node.getchildren():
                    if subnode.tag=='name':
                        channelObj['name']=subnode.text
                    elif subnode.tag=='id':
                        channelObj['channel']=subnode.text
                    else:
                        channelObj[subnode.tag]=subnode.text
                if channelObj:
                    channelList.append(channelObj)
                    
        elif vendor == 'dahua':
            channels=response.text.split()
            for idx,item in enumerate(channels):
                [id,name]=item.split('=')
                channelObj={}
                channelObj["name"]=name
                channelObj["channel"]=idx+1
                channelList.append(channelObj)
        else:
            logger.error("Not supported Vendor")
            return False,"Not supported vendor"
        out['channelList']=channelList
        return True,out
          
    except Exception as e :
        err_msg=str(e)
        try:
            err_msg=response.text
        except:
            pass
        
        logger.error("failed to fetch channels-{}".format(err_msg))
        return False,err_msg
    
    
    
def get_device_info(ip,port,user,passwd,vendor,authType='digest'):
    auth=None
    if authType=='basic':
        auth=HTTPBasicAuth(user,passwd)
    elif authType=='digest':
        auth=HTTPDigestAuth(user,passwd)
    url = IP_CAM_DEVICE_INFO_TEMPLATES[vendor]
    url=url.format("http",ip,port)
    device_info={}
    try:
        response = requests.get(url,auth=auth,timeout=5)
        response.raise_for_status()
        if vendor =='hikvision':
            xmlstring = re.sub(' xmlns="[^"]+"', '', response.text, count=1000)
            tree = ET.fromstring(xmlstring)
            for node in tree.getchildren():
                device_info[node.tag]=node.text
        elif vendor =='dahua':
            
            data=[t for t in response.text.split() if 'table.General.MachineName' in t ]
            if len(data)>0:
                [_,name]=data[0].split('=')
                device_info["deviceName"]=name
        return device_info            
    except Exception as e:
        logger.error("error occurred fetching-{}".format(device_info))
        return {}
        pass
            
            
        
        
    
    
    
        
        
        
        
        
        
        
    
    