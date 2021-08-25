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
        
        
        
        
    
    