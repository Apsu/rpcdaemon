# General
from uuid import uuid4

# RPC superclass
from rpcdaemon.lib.rpc import RPC

# Logger wrapper
from rpcdaemon.lib.logger import Logger

# Config parser
from rpcdaemon.lib.config import Config


# Plugin base class
class Plugin(RPC):
    def __init__(self, connection, config, handler=None):
        self.subclass = self.__class__.__name__
        self.sublower = self.subclass.lower()

        # Grab a copy of our config section
        self.config = config.section(self.subclass)

        self.pconfig = Config(self.config['conffile'], 'DEFAULT')

        # Initialize logger
        self.logger = Logger(
            name=self.sublower,
            level=self.config['loglevel'],
            handler=handler
        )

        # Initialize RPC bits
        RPC.__init__(
            self,
            connection,
            exopts={
                'name': self.config.get('exchange_name', None),
                'durable': self.config.get('exchange_durable', False),
                'type': self.config.get('exchange_type', 'topic')
            },
            qopts={
                'name': self.config.get(
                    'queue_name',
                    'rpcdaemon-%s_%s' % (
                        self.sublower,
                        uuid4()
                    )
                ),
                'auto_delete': self.config.get('queue_auto_delete', True),
                'durable': self.config.get('queue_durable', False),
                'routing_key': self.config.get('queue_routing_key', None)
            }
        )
