from setuptools import setup

setup(
    name='camVendorSDK',
    version='1.0.0',
    description='vendor camera sdk import functions',
    url='http://demo.vedalabs.in/',
    license='MIT',
    packages=['camVendorSDK','camVendorSDK.dahuaDevice','camVendorSDK.hikvisionDevice','camVendorSDK.hikvisionDevice.pyhik'],
    install_requires=['pyhik'],
    zip_safe=False
    )