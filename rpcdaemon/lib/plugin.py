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
        self.sublower = subclass.lower()

        # Grab a copy of our config section
        self.config = config.section(subclass)

        self.pconfig = Config(self.config['conffile'], 'DEFAULT')

        # Initialize logger
        self.logger = Logger(
            name=sublower,
            level=self.config['loglevel'],
            handler=handler
        )

        # Initialize RPC bits
        RPC.__init__(
            self,
            connection,
            exopts={
                'name': self.config['exchange_name']
                if 'exchange_name' in self.config else self.sublower,
                'durable': self.config['exchange_durable']
                if 'exchange_durable' in self.config else False,
                'type': self.config['exchange_type']
                if 'exchange_type' in self.config else 'topic'
            },
            qopts={
                'name': self.config['queue_name']
                if 'queue_name' in self.config else
                'rpcdaemon-%s_%s' % (self.sublower, uuid4()),
                'auto_delete': self.config['queue_auto_delete']
                if 'queue_auto_delete' in self.config else True,
                'durable': self.config['queue_durable']
                if 'queue_durable' in self.config else False,
                'routing_key': self.config['queue_routing_key']
                if 'queue_routing_key' in self.config else
                'glance_notifications.info'
            }
        )
