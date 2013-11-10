#!/usr/bin/env python2

# General
import sys
import getopt
import logging
from time import sleep
from signal import signal, getsignal, SIGTERM, SIGINT

# Daemonizing
from daemon import DaemonContext

# Threading
from threading import Thread

# Kombu
try:
    from kombu.mixins import ConsumerMixin
except ImportError:
    from rpcdaemon.lib.mixins import ConsumerMixin

from kombu import Connection

# My libs
from rpcdaemon.lib.logger import Logger
from rpcdaemon.lib.config import Config
from rpcdaemon.lib.pidfile import PIDFile


# Consumer worker
class Worker(ConsumerMixin, Thread):
    def __init__(self, connection, plugins=[]):
        Thread.__init__(self, target=self.run)  # MRO picks mixin.run
        self.connection = connection
        self.plugins = plugins
        self.queues = [plugin.queue for plugin in plugins]
        self.callbacks = [plugin.update for plugin in plugins]

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(queues=[queue], callbacks=[callback])
            for (queue, callback) in zip(self.queues, self.callbacks)
        ]


# State monitor
class Monitor(DaemonContext):
    def __init__(self, args=None):
        # Parse args
        if args is None:
            args = {}

        options, _ = getopt.getopt(sys.argv[1:], 'c:d')
        options = dict(options)

        config_file = options.get('-c', '/usr/local/etc/rpcdaemon.conf')
        daemonize = '-d' not in options

        # Parse config
        self.config = Config(config_file, 'Daemon')

        # Initialize logger
        self.logger = Logger(
            name='rpcdaemon',
            level = self.config['loglevel'],
            path = self.config['logfile'] if daemonize else None,
            handler = None if daemonize else logging.StreamHandler()
        )

        self.pidfile = PIDFile(self.config['pidfile']) if daemonize else None;

        # TOOD: plugin.check thread pool?
        self.timeout = 1

        # Clamp in case we exit before worker exists
        self.worker = None

        # Initialize daemon
        DaemonContext.__init__(
            self,
            detach_process=daemonize,
            files_preserve=[self.logger.handler.stream.fileno()],
            pidfile=self.pidfile,
            stdout=self.logger.handler.stream,
            stderr=self.logger.handler.stream
        )

    def open(self):
        # Call super
        DaemonContext.open(self)

        # Needfuls.doit()
        self.logger.info('Initializing...')

        # RPC connection
        self.connection = Connection(self.config['rpchost'])

        self.logger.info('Loading plugins...')
        # Import and create plugin objects
        self.plugins = [
            plugin(self.connection, self.config, self.logger.handler)
            for plugin in [
                getattr(
                    __import__(
                        'rpcdaemon.plugins.' + module.lower(),
                        fromlist=[module]
                    ),
                    module)
                for module in self.config['plugins'].split(',')
            ]
        ]

        # Setup worker with plugins and crank it up
        self.logger.info('Starting worker...')
        self.worker = Worker(self.connection, self.plugins)
        self.worker.daemon = True  # Daemon thread
        self.worker.start()
        self.logger.info('Started.')

    def check(self):
        for plugin in self.plugins:
            plugin.check()

    def close(self):
        # We might get called more than once, or before worker exists
        if self.is_open and self.worker and self.worker.is_alive():
            self.logger.info('Stopping worker...')
            self.worker.should_stop = True
            self.worker.join(5)  # Wait up to 5 seconds
            if self.worker.is_alive():
                self.logger.warn(
                    'Error stopping worker. Shutting down uncleanly.'
                )
            self.logger.info('Stopped.')

        DaemonContext.close(self)


# Entry point
def main():
    with Monitor(sys.argv[1:]) as monitor:
        while monitor.worker.is_alive():
            monitor.logger.debug('Dispatching plugin checks...')
            monitor.check()
            # TODO: plugin.check thread pool?
            sleep(monitor.timeout)


# If called directly
if __name__ == '__main__':
    main()
