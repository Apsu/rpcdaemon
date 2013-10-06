#!/usr/bin/env python2

from setuptools import setup, find_packages


setup(
    name='RPCDaemon',
    version='1.0',
    description='AMQP RPC daemon for Quantum Agent HA',
    license='MIT',
    author='Evan Callicoat',
    author_email='apsu@propter.net',
    url='http://github.com/Apsu/rpcdaemon',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'rpcdaemon = rpcdaemon:main'
        ]
    },
    install_requires=[
        'lockfile>=0.9',
        'python-daemon==1.5.5',
        'python-dateutil',
        'ConfigParser',
        'kombu',
        'python-quantumclient'
    ]
)
