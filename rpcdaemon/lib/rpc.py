# Kombu
from kombu import Exchange, Queue


class RPC():
    def __init__(self, connection, exopts={}, qopts={}):
        # Store RPC connection
        self.connection = connection

        # Initialize RPC bindings
        exopts.setdefault(None)
        qopts.setdefault(None)
        exopts['channel'] = self.connection.channel()
        self.exchange = Exchange(**exopts)
        qopts['exchange'] = self.exchange
        self.queue = Queue(**qopts)
