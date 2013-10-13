# General
from kombu.utils import uuid

# RPC superclass
from rpcdaemon.lib.rpc import RPC

# Logger wrapper
from rpcdaemon.lib.logger import Logger

# Config parser
from rpcdaemon.lib.config import Config


# Plugin base class
class Plugin(RPC):
    def __init__(self, connection, config, handler=None):
        # Store classname helpers
        self.subclass = self.__class__.__name__
        self.sublower = self.subclass.lower()

        # Set config section to ours
        self.config = config.section(self.subclass)

        # Set uniqueid option for config
        self.config.set(
            self.subclass,
            'plugin_id',
            '%s_%s' % (self.sublower, uuid())
        )

        # Initialize logger
        self.logger = Logger(
            self.sublower,
            self.config['loglevel'],
            handler=handler
        )

        self.logger.info('Initializing...')
        self.pconfig = Config(self.config['conffile'])

        # Initialize RPC bits
        RPC.__init__(self, connection, config)

        self.logger.info(self.queue)

        self.logger.info('Initialized.')
