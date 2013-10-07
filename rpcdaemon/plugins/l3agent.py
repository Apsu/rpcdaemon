# General
from uuid import uuid4
from itertools import cycle

# Quantum Agent superclass
from rpcdaemon.lib.quantumagent import QuantumAgent

# RPC superclass
from rpcdaemon.lib.rpc import RPC

# Logger wrapper
from rpcdaemon.lib.logger import Logger

# Config parser
from rpcdaemon.lib.config import Config


# Specific L3 agent handler
class L3Agent(QuantumAgent, RPC):
    def __init__(self, connection, config, handler=None):
        # Grab a copy of our config section
        self.config = config.section('L3Agent')

        # Initialize logger
        self.logger = Logger(
            name='l3agent',
            level=self.config['loglevel'],
            handler=handler
        )

        # Parse quantum.conf
        self.qconfig = Config(self.config['conffile'], 'AGENT')

        # Initialize super
        QuantumAgent.__init__(self, self.qconfig, 'L3 agent')

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
                'name': 'rpcdaemon-l3_%s' % uuid4(),
                'auto_delete': True,
                'durable': False,
                'routing_key': 'q-plugin'
            }
        )

    # L3 specific handler
    def handle(self, host, agent, state):
        targets = [
            target for target in self.agents.values()
            if not target['host'] == host
            and target['alive']
        ] if not state else self.agents.values()
        routers = self.client.list_routers_on_l3_agent(agent['id'])['routers']

        # Any agents alive?
        if targets:
            # Map my routers to other agents
            mapping = zip(routers, cycle(targets))

            # And move them
            for router, target in mapping:
                self.logger.info(
                    'Rescheduling %s(%s) -> %s/%s.' % (
                        router['name'],
                        router['id'],
                        target['host'],
                        target['type']
                    )
                )
                self.client.remove_router_from_l3_agent(
                    agent['id'],
                    router['id']
                )
                self.client.add_router_to_l3_agent(
                    target['id'],
                    {'router_id': router['id']}
                )
        # No agents, any routers?
        elif routers:
            self.logger.warn(
                'No agents found to reschedule routers from %s/%s(%s).' % (
                    host,
                    agent['type']
                )
            )
