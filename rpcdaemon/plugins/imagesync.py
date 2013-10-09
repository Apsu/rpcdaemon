# General
import json
from uuid import uuid4

# RPC superclass
from rpcdaemon.lib.rpc import RPC

# Logger wrapper
from rpcdaemon.lib.logger import Logger

# Config parser
from rpcdaemon.lib.config import Config


# Glance image sync handler
class ImageSync(RPC):
    def __init__(self, connection, config, handler=None):
        # Grab a copy of our config section
        self.config = config.section('ImageSync')

        # Initialize logger
        self.logger = Logger(
            name='imagesync',
            level=self.config['loglevel'],
            handler=handler
        )

        # Initialize RPC bits
        RPC.__init__(
            self,
            connection,
            exopts={
                'name': 'glance',
                'durable': False,
                'type': 'topic'
            },
            qopts={
                'name': 'rpcdaemon-imagesync_%s' % uuid4(),
                'auto_delete': True,
                'durable': False,
                'routing_key': 'glance_notifications.info'
            }
        )

    def update(self, body, message):
        self.logger.debug(json.dumps(body, indent=2, sort_keys=True))
        message.ack()
