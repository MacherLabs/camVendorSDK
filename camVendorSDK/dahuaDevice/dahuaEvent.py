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

REQUIREMENTS = ['pycurl>=7']

import threading
import requests
import datetime
import re
import time


#from slacker import Slacker
try:
    #python 3+
    from configparser import ConfigParser
except:
    # Python 2.7
    from ConfigParser import ConfigParser
import logging
import os
import socket
import pycurl
import json
import time
import base64
import traceback

#Version String must be in this format (with o to replace 0) = versi0n = "<version>"
#for travis to find it.
version = "0.2.3"
#ImageFile.LOAD_TRUNCATED_IMAGES = True
#mqttc = paho.Client("CameraEvents-" + socket.gethostname(), clean_session=True)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)
_LOGGER.addHandler(ch)



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
    Devices = []
    NumActivePlayers = 0

    CurlMultiObj = pycurl.CurlMulti()
    NumCurlObjs = 0
	

    def __init__(self,cameras,callBack):
        """Construct a thread listening for events."""
        for device_cfg in cameras:

            device = DahuaDevice(device_cfg.get("name"), device_cfg,callBack)

            _LOGGER.info("Device %s created on Url %s.  Alert Status: %s" % (device.Name, device.host, device.alerts))

            self.Devices.append(device)

            #could look at this method: https://github.com/tchellomello/python-amcrest/blob/master/src/amcrest/event.py
            CurlObj = pycurl.Curl()
            device.CurlObj = CurlObj

            CurlObj.setopt(pycurl.URL, device.url)
            
            CurlObj.setopt(pycurl.CONNECTTIMEOUT, 30)
            CurlObj.setopt(pycurl.TCP_KEEPALIVE, 1)
            CurlObj.setopt(pycurl.TCP_KEEPIDLE, 30)
            CurlObj.setopt(pycurl.TCP_KEEPINTVL, 15)
            if device.auth == 'digest':
                CurlObj.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
                CurlObj.setopt(pycurl.USERPWD, "%s:%s" % (device.user, device.password))
            else:
                CurlObj.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH)
                CurlObj.setopt(pycurl.USERPWD, "%s:%s" % (device.user, device.password))
            CurlObj.setopt(pycurl.WRITEFUNCTION, device.OnReceive)

            self.CurlMultiObj.add_handle(CurlObj)
            self.NumCurlObjs += 1

            _LOGGER.debug("Added Dahua device at: %s", device.url)

        threading.Thread.__init__(self)
        self.stopped = threading.Event() 


    def run(self):
        heartbeat = 0
        """Fetch events"""
        while 1:
            Ret, NumHandles = self.CurlMultiObj.perform()
            if Ret != pycurl.E_CALL_MULTI_PERFORM:
                break

        Ret = self.CurlMultiObj.select(1.0)
        while not self.stopped.isSet():
            # Sleeps to ease load on processor
            time.sleep(1)
            Ret, NumHandles = self.CurlMultiObj.perform()

            if NumHandles != self.NumCurlObjs:
                _, Success, Error = self.CurlMultiObj.info_read()

                for CurlObj in Success:
                    DahuaDevice = next(iter(filter(lambda x: x.CurlObj == CurlObj, self.Devices)), None)
                    if DahuaDevice.Reconnect:
                        _LOGGER.debug("Dahua Reconnect: %s", DahuaDevice.Name)
                        continue

                    DahuaDevice.OnDisconnect("Success")
                    DahuaDevice.Reconnect = time.time() + 5

                for CurlObj, ErrorNo, ErrorStr in Error:
                    DahuaDevice = next(iter(filter(lambda x: x.CurlObj == CurlObj, self.Devices)), None)
                    if DahuaDevice.Reconnect:
                        continue

                    DahuaDevice.OnDisconnect("{0} ({1})".format(ErrorStr, ErrorNo))
                    DahuaDevice.Reconnect = time.time() + 5

                for DahuaDevice in self.Devices:
                    if DahuaDevice.Reconnect and DahuaDevice.Reconnect < time.time():
                        self.CurlMultiObj.remove_handle(DahuaDevice.CurlObj)
                        self.CurlMultiObj.add_handle(DahuaDevice.CurlObj)
                        DahuaDevice.Reconnect = None
            #if Ret != pycurl.E_CALL_MULTI_PERFORM: break
            
            
            


if __name__ == '__main__':

    cameras = []
    cp = ConfigParser()
    _LOGGER.info("Loading config")
    filename = {"config.ini"}
    dataset = cp.read(filename)

    try:
        if len(dataset) != 1:
            raise ValueError( "Failed to open/find all files")
        camera_items = cp.items( "Cameras" )
        for key, camera_key in camera_items:
            #do something with path
            camera_cp = cp.items(camera_key)
            camera = {}
            camera["host"] = cp.get(camera_key,'host')
            camera["protocol"] = cp.get(camera_key,'protocol')
            camera["isNVR"] = cp.getboolean(camera_key,'isNVR',fallback=False)
            camera["name"] = cp.get(camera_key,'name')
            camera["port"] = cp.getint(camera_key,'port')
            camera["user"] = cp.get(camera_key,'user')
            camera["pass"] = cp.get(camera_key,'pass')
            camera["auth"] = cp.get(camera_key,'auth')
            camera["events"] = cp.get(camera_key,'events')
            camera["alerts"] = cp.getboolean(camera_key,"alerts",fallback=True)
            channels = {}
            if cp.has_option(camera_key,'channels'):
                try:
                    channellist = cp.get(camera_key,'channels').split('|')
                    for channel in channellist:
                        channelIndex = channel.split(':')[0]
                        channelName = channel.split(':')[1]
                        channels[int(channelIndex)] = channelName
                        
                except Exception as e:
                    _LOGGER.warning("Warning, No channel list in config (may be obtained from NVR):" + str(e))
                    channels = {}

            camera["channels"] = channels
            cameras.append(camera)

        dahua_event = DahuaEventThread(cameras)

        dahua_event.start()
    except Exception as ex:
        _LOGGER.error("Error starting:" + str(ex))
