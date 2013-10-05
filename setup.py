#!/usr/bin/env python2

from distutils.core import setup

setup(name='RPC-Daemon',
      version='1.0',
      description='AMQP RPC daemon for Quantum Agent HA',
      author='Evan Callicoat',
      author_email='apsu@propter.net',
      url='http://github.com/Apsu/rpc-daemon',
      scripts=['rpc-daemon'],
      requires=[
          'daemon',
          'dateutil',
          'ConfigParser',
          'kombu',
          'quantumclient'
      ]
     )
