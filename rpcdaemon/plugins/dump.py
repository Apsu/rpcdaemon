# General
import json

# RPC superclass
from rpcdaemon.lib.rpc import RPC

# Logger wrapper
from rpcdaemon.lib.logger import Logger

# Config parser
from rpcdaemon.lib.config import Config


# Dump agent handler
class Dump(RPC):
    def __init__(self, connection, config, handler=None):
        # Grab a copy of our config section
        self.config = config.section('Dump')

        # Initialize logger
        self.logger = Logger(
            name='dump',
            level=self.config['loglevel'],
            handler=handler
        )

        # Initialize RPC bits
        RPC.__init__(
            self,
            connection,
            exopts={
                'name': 'quantum',
                'durable': False,
                'type': 'topic'
            },
            qopts={
                'name': 'rpcdaemon-dump_%s' % uuid4(),
                'auto_delete': True,
                'durable': False,
                'routing_key': 'q-plugin'
            }
        )

    def update(self, body, message):
        self.logger.debug(json.dumps(body, indent=2, sort_keys=True))
        message.ack()
