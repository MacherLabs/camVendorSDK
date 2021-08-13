import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("Loaded " + __name__)
from datetime import datetime, timezone
import time
import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))
import hik
import dahua
import utils
from constants import IP_CAM_SNAP_TEMPLATES


def callBack(channel,alertType,state,time=None):
    if time is None:
        dt_now = datetime.now(tz=timezone.utc)
        time= dt_now.strftime("%Y-%m-%d %H:%M:%S")
    logger.info("event {} received from channel-{}-at time-{}".format(alertType,channel,state,time))
    
    

def getIpCamSnap(ip,port,user,passw,vendor,protocol='http',channel=1,authType='digest',format='jpeg'):
    
    snapTemplate= IP_CAM_SNAP_TEMPLATES.get(vendor,None)
    if snapTemplate:
        url = snapTemplate.format(protocol,ip,port,channel)
        return utils.getImageByUrl(url,user,passw,authType,format=format)
    else:
        logger.error("no snap template registered for the vendor-{}".format(vendor))
        return None
    
    

class Camera():
    def __init__(self,IP, port, user, passw,vendor,callBack=callBack,authTyoe='digest'):
        if vendor=='hikvision':
            self.cam= hik.HikCamObject(IP, port, user, passw,callBack)
        elif vendor=='dahua':
            self.cam = dahua.DahuaCamObject(IP, port, user, passw,callBack)
        self.authType=authTyoe
    
    def startEventListener(self):
        self.cam.startListening()
    
    def stopEventListener(self):
        self.cam.stopListening()
    
    def getSnapshot(self,channel,format='jpeg'):
        return self.cam.getSnapshot(channel,self.authType,format=format)
    

if __name__ == '__main__':
    #cam = Camera('192.168.1.250',port=80,user='admin',passw='VedaLabs',vendor='hikvision')
    #cam = Camera('122.169.114.214',port=1025,user='admin',passw='vct280620',vendor='dahua')
    #cam.startEventListener()
    # time.sleep(15)
    # cam.stopEventListener()
    import pdb;pdb.set_trace()
    snap = getIpCamSnap('122.169.114.214',port=1025,user='admin',passw='vct280620',vendor='dahua',format='numpy')
    print(snap.shape)
    snap2 = getIpCamSnap('192.168.1.85',port=80,user='admin',passw='VedaLabs',vendor='hikvision',format='numpy')
    print(snap2.shape)
    # snap2 = cam.getSnapshot(2,format='numpy')
    # print("done")