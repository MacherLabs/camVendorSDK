
ALERT_TYPE_MAP={
    
    'motion':'motion',
    'VideoMotion': 'motion',
    "Video Loss": "Video Loss",
    "Tamper Detection": "Tamper Detection",
    'Line Crossing': 'Line Crossing',
    'Field Detection': 'Field Detection',
    'Disk Full': 'Disk Full',
    'Disk Error': 'Disk Error',
    'Net Interface Broken': 'Net Interface Broken',
    'P Conflict': 'IP Conflict',
    'Illegal Access': 'Illegal Access',
    'Video Mismatch': 'Video Mismatch',
    'Bad Video': 'Bad Video',
    'PIR Alarm': 'PIR Alarm',
    'Face Detection': 'Face Detection',
    'Scene Change Detection': 'Scene Change Detection',
    'I/O': 'I/O',
    'Unattended Baggage': 'Unattended Baggage',
    'Attended Baggage': 'Attended Baggage',
    'Recording Failure': 'Recording Failure',
    "Exiting Region": "Exiting Region",
    "Entering Region": "Entering Region",
    'VideoLoss': "Video Loss",
    'VideoBlind': "Tamper Detection",
    'StorageNotExist': 'Disk Error',
    'StorageFailure': 'Disk Error',
    'StorageLowSpace': 'Disk Full',
    'AlarmLocal': 'Alarm Local',
    'AlarmOutput': 'AlarmOutput'
}

IP_CAM_SNAP_TEMPLATES={
    'hikvision':"{}://{}:{}/ISAPI/Streaming/channels/{}01/picture",
    'dahua':"{}://{}:{}/cgi-bin/snapshot.cgi?channel={}"
}

IP_CAM_CHANNELS_TEMPLATE={
    'hikvision': "{}://{}:{}/ISAPI/System/Video/inputs/channels",
    'dahua':"{}://{}:{}/cgi-bin/configManager.cgi?action=getConfig&name=ChannelTitle"
}

IP_CAM_DEVICE_INFO_TEMPLATES={
    'hikvision': "{}://{}:{}/ISAPI/System/deviceInfo",
    'dahua':"{}://{}:{}/cgi-bin/configManager.cgi?action=getConfig&name=General"
}