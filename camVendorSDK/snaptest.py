import requests
import numpy as np
import cv2
from requests.auth import HTTPDigestAuth
i=0

url = "http://182.74.195.106:81/ISAPI/Streaming/channels/201/picture"
url ="http://122.169.114.214:1025/cgi-bin/snapshot.cgi?channel=1"
while (i<100):
    i+=1
    payload=""
    response = requests.get(url,auth=HTTPDigestAuth('admin', 'vct280620') )
    
    #import pdb;pdb.set_trace()

    data=response.content
    arr = np.asarray(bytearray(data), dtype=np.uint8)
    img = cv2.imdecode(arr, -1)
    cv2.imshow("frame",img)
    cv2.waitKey(1)
        

   