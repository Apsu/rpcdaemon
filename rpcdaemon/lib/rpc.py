# Kombu
from kombu import Exchange, Queue, Connection


class RPC():
    def __init__(self, connection, exopts={}, qopts={}):
        # Store RPC connection
        self.connection = connection

        # Initialize RPC bindings
        exopts['channel'] = self.connection.channel()
        self.exchange = Exchange(**exopts)
        qopts['exchange'] = self.exchange
        self.queue = Queue(**qopts)

    # Empty default handler
    def handle(self, agent, state):
        pass
