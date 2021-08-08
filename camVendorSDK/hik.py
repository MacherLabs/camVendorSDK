import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("Loaded " + __name__)
from datetime import datetime, timezone
import hikvisionDevice.pyhik.hikvision as hikvision

#logging.basicConfig(filename='out.log', filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
import time
import threading
import utils

 

class HikCamObject(object):
    """Representation of HIk camera."""

    def __init__(self, IP, port, user, passw,callBack,protocol='http'):
        """initalize camera"""

        # Establish camera
        url = "{}://{}".format(protocol,IP)
        print(url)
        self.cam = hikvision.HikCamera(url, port, user, passw,callBack)
        self._name = self.cam.get_name
        self.motion = self.cam.current_motion_detection_state
        self.callBack=callBack
        self.snapTemplate="{}://{}:{}/ISAPI/Streaming/channels".format(protocol,IP,port)
        self.user=user
        self.passw=passw
        # Start event stream


    @property
    def sensors(self):
        """Return list of available sensors and their states."""
        return self.cam.current_event_states

    def get_attributes(self, sensor, channel):
        """Return attribute list for sensor/channel."""
        return self.cam.fetch_attributes(sensor, channel)

    def stopListening(self):
        """Shutdown Hikvision subscriptions and subscription thread on exit."""
        self.cam.disconnect()
        
    def startListening(self):
        self.cam.start_stream()
        self._event_states = self.cam.current_event_states
        self._id = self.cam.get_id
        print('NAME: {}'.format(self._name))
        print('ID: {}'.format(self._id))
        print('{}'.format(self._event_states))
        print('Motion Dectect State: {}'.format(self.motion))
        

    def flip_motion(self, value):
        """Toggle motion detection"""
        if value:
            self.cam.enable_motion_detection()
        else:
            self.cam.disable_motion_detection()
            
    def listenToAlerts(self):
        entities = []
        print("sensors-{}".format(self.sensors))
        
        if self.sensors and (len(self.sensors)>0):
            for sensor, channel_list in self.sensors.items():
                #logger.info("adding-{}-{}".format(sensor,channel_list))
                for channel in channel_list:
                    entities.append(HikSensor(sensor, channel[1], self))  
        else:
            logger.error("no sensor found to listen")
            
    def getSnapshot(self,channel,authType,format):
        imgUrl="{}/{}01/picture".format(self.snapTemplate,channel)
        return utils.getImageByUrl(imgUrl,self.user,self.passw,authType,format=format)
            
    

class HikSensor(object):
    """ Hik camera sensor."""

    def __init__(self, sensor, channel, cam):
        """Init"""
        self._cam = cam
        self._name = "{} {} {}".format(self._cam.cam.name, sensor, channel)
        self._id = "{}.{}.{}".format(self._cam.cam.cam_id, sensor, channel)
        self._sensor = sensor
        self._channel = channel
        self._cam.cam.add_update_callback(self.update_callback, self._id)
        self.lock = threading.Lock()

    def _sensor_state(self):
        """Extract sensor state."""
        return self._cam.get_attributes(self._sensor, self._channel)[0]

    def _sensor_last_update(self):
        """Extract sensor last update time."""
        return self._cam.get_attributes(self._sensor, self._channel)[3]

    @property
    def name(self):
        """Return the name of the Hikvision sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return an unique ID."""
        return '{}.{}'.format(self.__class__, self._id)

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._sensor_state()

    def update_callback(self, msg):
        """ get updates. """
        logger.info('Callback: {}'.format(msg))
        logger.info('{}:{}:{} @ {}'.format(self.name, self._sensor_state(),self._channel, self._sensor_last_update()))
        dt = self._sensor_last_update()
        dt = dt.replace(tzinfo=timezone.utc)
        datestring=dt.strftime("%Y-%m-%d %H:%M:%S")
        with self.lock:
            self._cam.callBack(self._channel,msg,datestring)
            

   
       
if __name__ == '__main__':
    cam = HikCamObject('182.74.195.106',port=81,user='admin',passw='admin@123',callBack=callBack)
    print("done")
    #cam.listenToAlerts()