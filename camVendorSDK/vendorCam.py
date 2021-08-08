import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("Loaded " + __name__)
from datetime import datetime, timezone
import time
import hik
import dahua

def callBack(channel,alertType,state,time=None):
    if time is None:
        dt_now = datetime.now(tz=timezone.utc)
        time= dt_now.strftime("%Y-%m-%d %H:%M:%S")
    logger.info("event {} received from channel-{}-at time-{}".format(alertType,channel,state,time))
    

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
    #cam = Camera('182.74.195.106',port=81,user='admin',passw='admin@123',vendor='hikvision')
    cam = Camera('122.169.114.214',port=1025,user='admin',passw='vct280620',vendor='dahua')
    cam.startEventListener()
    time.sleep(15)
    cam.stopEventListener()
    snap = cam.getSnapshot(1,format='numpy')
    print(snap.shape)
    snap2 = cam.getSnapshot(2,format='numpy')
    print("done")