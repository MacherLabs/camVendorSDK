"""
Attach event listener to Dahua devices
Borrowed code from https://github.com/johnnyletrois/dahua-watch
And https://github.com/SaWey/home-assistant-dahua-event
Author: PsycikNZ
"""
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("Loaded " + __name__)

import threading
import requests
import datetime
import re
import time
import logging
import os
import time
import traceback
from requests.auth import HTTPDigestAuth

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)
_LOGGER.addHandler(ch)

DEFAULT_HEADERS = {
    'Content-Type': "application/xml; charset='UTF-8'",
    'Accept': "*/*"
}

CONNECT_TIMEOUT = 5
READ_TIMEOUT = 60

def setup( config):
    """Set up Dahua event listener."""
    #config = config.get(DOMAIN)

    dahua_event = DahuaEventThread(
        None,
        None
    )

    def _start_dahua_event(_event):
        dahua_event.start()

    def _stop_dahua_event(_event):
        dahua_event.stopped.set()

    return True

class DahuaDevice():
    EVENT_TEMPLATE = "{protocol}://{host}:{port}/cgi-bin/eventManager.cgi?action=attach&codes=%5B{events}%5D"
    CHANNEL_TEMPLATE = "{protocol}://{host}:{port}/cgi-bin/configManager.cgi?action=getConfig&name=ChannelTitle"

    def __init__(self,  name, device_cfg,callBack):
        if device_cfg["channels"]:
            self.channels = device_cfg["channels"]
        else:
            self.channels = {}
        self.callBack=callBack
        self.lock = threading.Lock()
        self.Name = name
        self.CurlObj = None
        self.Connected = None
        self.Reconnect = None
        self.MQTTConnected = None
        self.user = device_cfg.get("user")
        self.password = device_cfg.get("pass")
        self.auth = device_cfg.get("auth")
        self.protocol  = device_cfg.get("protocol")
        self.host = device_cfg.get("host")
        self.port = device_cfg.get("port")
        self.alerts = device_cfg.get("alerts")
       
        self.snapshotoffset = device_cfg.get("snapshotoffset")
    

        #generate the event url
        self.url = self.EVENT_TEMPLATE.format(
            protocol=self.protocol,
            host=self.host,
            port=self.port,
            events='VideoMotion%2CCrossLineDetection%2CAlarmLocal%2CVideoLoss%2CVideoBlind%2CStorageNotExist%2CStorageFailure%2CStorageLowSpace%2CAlarmOutput'
        )
        
        self.isNVR = False
        try:
            # Get NVR parm, to get channel names if NVR
            self.isNVR = device_cfg.get("isNVR")

            if self.isNVR:
                #generate the channel url
                self.channelurl  = self.CHANNEL_TEMPLATE.format(
                    protocol=device_cfg.get("protocol"),
                    host=device_cfg.get("host"),
                    port=device_cfg.get("port")
                )
                
                _LOGGER.debug("Device " + name + " Getting channel ids: " + self.channelurl)
                response = requests.get(self.channelurl,auth=requests.auth.HTTPDigestAuth(self.user,self.password))
                logger.info("response-{}".format(response.text))
                for line in response.text.splitlines():
                    match = re.search(r'.\[(?P<index>[0-4])\]\..+\=(?P<channel>.+)',line)
                    if match:
                        _index = int(match.group("index"))
                        _channel = match.group("channel")
                        self.channels[_index] = _channel
                _LOGGER.info("channels-received-{}".format(self.channels))
            else:
                self.channels[0] = self.Name

            _LOGGER.info("Created Data Device: " + name)

        except Exception as e:
            _LOGGER.debug("Device " + name + " is not an NVR: " + str(e))
            _LOGGER.debug("Device " + name + " is not an NVR")
            
            
    def do_callBack(self,channel,msg,state,time=None):
        with self.lock:
            self.callBack(channel,msg,state,time)
        

    def channelIsMine(self,channelname="",channelid=-1):
        channelidInt = -1
        if isinstance(channelid,str):
            channelidInt = int(channelid)
        else:
            channelidInt = channelid
        for channel in self.channels:
            if channelname is not None and channelname == self.channels[channel]:
                return channel
            elif channelidInt > -1 and channel == channelidInt:
                return channel

        return -1

    # Connected to camera
    def OnConnect(self):
        _LOGGER.debug("[{0}] OnConnect()".format(self.Name))
        self.Connected = True
        self.do_callBack(-1,"status",True)

    #disconnected from camera
    def OnDisconnect(self, reason):
        _LOGGER.debug("[{0}] OnDisconnect({1})".format(self.Name, reason))
        self.Connected = False
        self.do_callBack(-1,"status",False)

    #on receive data from camera.
    def OnReceive(self, data):
        #self.client.loop_forever()
        try:
            Data = data.decode("utf-8", errors="ignore")    
            _LOGGER.debug("[{0}]: {1}".format(self.Name, Data))

            crossData = ""
            logger.info("data-{}".format(data))
            for Line in Data.split("\r\n"):
                if Line == "HTTP/1.1 200 OK":
                    self.OnConnect()

                if not Line.startswith("Code="):
                    continue
                
                Alarm = dict()
                Alarm["name"] = self.Name
                
                for KeyValue in Line.split(';'):
                    for keyValuePair in KeyValue.split(',',1):
                        logger.info("keyvalue-{}".format(keyValuePair))
                        Key, Value = keyValuePair.split('=')
                        Alarm[Key] = Value

                index =  int( Alarm["index"])
                if index in self.channels:
                    Alarm["channel"] = self.channels[index]+ ":" + str(index)
                else:
                    Alarm["channel"] = self.Name + ":" + str(index)

                eventStart = False
                camera = Alarm["channel"]

                if Alarm["Code"] == "VideoMotion":
                    _LOGGER.info("Video Motion received: "+  Alarm["name"] + " Index: " + Alarm["channel"] + " Code: " + Alarm["Code"])
                    
                    if Alarm["action"] == "Start":
                        eventStart = True
                        print(Alarm["Code"] + "/" + Alarm["channel"] +"ON")
                        self.do_callBack(Alarm["index"],Alarm["Code"],True)
    
                    else:
                        eventStart = False
                        print(Alarm["Code"] + "/" + Alarm["channel"] +"OFF")
                        self.do_callBack(Alarm["index"],Alarm["Code"],False)
                        
                    
                elif Alarm["Code"] == "AlarmLocal":
                    _LOGGER.info("Alarm Local received: "+  Alarm["name"] + " Index: " + str(index) + " Code: " + Alarm["Code"])
                    # Start action reveived, turn alarm on.
                    if Alarm["action"] == "Start":
                        self.do_callBack(Alarm["index"],Alarm["Code"],True)
                        eventStart = True
                    
                    else: 
                        self.do_callBack(Alarm["index"],Alarm["Code"],False)
                        eventStart = False

                else:
                    _LOGGER.info("dahua_event_received: "+  Alarm["name"] + " Index: " + Alarm["channel"] + " Code: " + Alarm["Code"])
                    if Alarm["action"] == "Start":
                        self.do_callBack(Alarm["index"],Alarm["Code"],True)
                        eventStart = True 
                    else:
                        self.do_callBack(Alarm["index"],Alarm["Code"],False)
                        eventStart = False
        except Exception as e:
            print(traceback.format_exc())


class DahuaEventThread(threading.Thread):
    """Connects to device and subscribes to events"""	

    def __init__(self,dvr,callBack):
        """Construct a thread listening for events."""
        self.device = DahuaDevice(dvr.get("name"),dvr,callBack)
        _LOGGER.info("Device %s created on Url %s.  Alert Status: %s" % (self.device.Name, self.device.host, self.device.alerts))
        
        # Create request session 
        self.dahua_request = requests.Session()
        self.dahua_request.verify = True
        self.dahua_request.auth = HTTPDigestAuth(self.device.user, self.device.password)
        self.dahua_request.headers.update(DEFAULT_HEADERS)
        _LOGGER.debug("Added Dahua device at: %s", self.device.url)

        threading.Thread.__init__(self)
        self.stopped = threading.Event() 


    def run(self):
        heartbeat = 0
        """Fetch events"""
        while not self.stopped.isSet():
            try:
                # Sleeps to ease load on processor
                time.sleep(1)
                
                # Monitor the Dahua event stream
                stream = self.dahua_request.get(self.device.url, stream=True,timeout=(CONNECT_TIMEOUT,READ_TIMEOUT))
                
                # If unsuccessful, send offline status alert
                if stream.status_code == requests.codes.not_found or stream.status_code != requests.codes.ok:
                    raise ValueError('Connection unsucessful.')
                else:
                    # Device is connected successfully
                    self.device.OnConnect()
                
                # Process the stream data received  
                for line in stream.iter_lines():
                    if line:
                        self.device.OnReceive(line)

            except Exception as e:
                self.dahua_request.close()
                # Device got disconnected
                self.device.OnDisconnect(str(e))
                _LOGGER.error("some error occurred -{}-{}".format(str(e),self.device.url))
                time.sleep(30)
  
