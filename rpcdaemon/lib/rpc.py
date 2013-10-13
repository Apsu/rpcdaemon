# Kombu
from kombu import Exchange, Queue, Connection


class RPC():
    def __init__(self, connection, config):
        # Store RPC connection
        self.connection = connection

        # Initialize RPC bindings
        self.exchange = Exchange(
            {
                'name': config['exchange_name'],
                'durable': config['exchange_durable'],
                'type': config['exchange_type'],
                'channel': connection.channel()
            }
        )

        self.queue = Queue(
            {
                'name': config['queue_name'],
                'auto_delete': config['queue_auto_delete'],
                'durable': config['queue_durable'],
                'routing_key': config['queue_routing_key'],
                'arguments': {'x-expires': 5000},
                'exchange': self.exchange
            }
        )
