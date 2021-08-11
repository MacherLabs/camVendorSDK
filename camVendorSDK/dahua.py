import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("Loaded " + __name__)
from datetime import datetime, timezone
from dahuaDevice.dahuaEvent import DahuaEventThread

#logging.basicConfig(filename='out.log', filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
import time
import threading
import requests
import utils

class DahuaCamObject(object):
    """Representation of HIk camera."""

    def __init__(self, IP, port, user, passw,callBack,protocol="http",isNVR=True):
        """initalize camera"""

        # Establish camera
        camera = {}
        camera["host"] = IP
        camera["protocol"] = protocol
        camera["isNVR"] = isNVR
        camera["name"] = IP
        camera["port"] = port
        camera["user"] = user
        camera["pass"] = passw
        camera["channels"] = {}
        print('NAME: {}'.format(camera["name"]))
        self.dahua_event = DahuaEventThread([camera],callBack)
        self.user=user
        self.passw=passw
        self.ip=IP
        self.port=port
        self.protocol=protocol
        self.snapTemplate="{}://{}:{}/cgi-bin/snapshot.cgi?channel={}"
            
    def startListening(self):
        self.dahua_event.start()
        
    def stopListening(self):
        self.dahua_event.stopped.set()
        
    def getSnapshot(self,channel,authType,format):
        imgUrl=self.snapTemplate.format(self.protocol,self.ip,self.port,channel) 
        return utils.getImageByUrl(imgUrl,self.user,self.passw,authType,format=format)
            
            
def callBack(channel,msg,state,time=None):
    if time is None:
        dt_now = datetime.now(tz=timezone.utc)
        time= dt_now.strftime("%Y-%m-%d %H:%M:%S")
    logger.info("event {} received from channel-{}-at time-{} in state-{}".format(msg,channel,time,state))      
       
if __name__ == '__main__':
    cam = DahuaCamObject('122.169.114.214',port=1025,user='admin',passw='vct280620',callBack=callBack)
    cam.listenToAlerts()
    time.sleep(30)
    cam.stopListening()
    