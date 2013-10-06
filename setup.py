#!/usr/bin/env python2

from distutils.core import setup

setup(
    name='RPCDaemon',
    version='1.0',
    description='AMQP RPC daemon for Quantum Agent HA',
    author='Evan Callicoat',
    author_email='apsu@propter.net',
    url='http://github.com/Apsu/rpcdaemon',
    scripts=['rpcdaemon'],
    requires=[
        'daemon',
        'dateutil',
        'ConfigParser',
        'kombu',
        'quantumclient'
    ]
)
