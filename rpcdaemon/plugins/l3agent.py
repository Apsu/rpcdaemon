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

        # Parse agent config
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
    def handle(self, agent, state):
        # All alive agents
        targets = [
            target for target in self.agents.values()
            if target['alive']
        ]

        # If agent is down, remove routers first
        if not state:
            for router in (
                self.client.list_routers_on_l3_agent(agent['id'])['routers']
            ):
                self.logger.info(
                    'Removing router %s from %s/%s [%s]' % (
                        router['id'],
                        agent['host'],
                        agent['agent_type'],
                        str(agent['id'])
                    )
                )
                self.client.remove_router_from_l3_agent(
                    agent['id'],
                    router['id']
                )

        self.logger.debug('Targets: %s' % targets)

        # Routers on agents
        binds = [
            router for target in targets
            for router in
            self.client.list_routers_on_l3_agent(target['id'])['routers']
        ]

        self.logger.debug('Bound Routers: %s' % binds)

        # Routers not on agents
        routers = [
            router
            for router in self.client.list_routers()['routers']
            if not router in binds
        ]

        self.logger.debug('Free Routers: %s' % routers)

        # Any agents alive?
        if targets:
            # Map routers to agents
            mapping = zip(routers, cycle(targets))

            # And schedule them
            for router, target in mapping:
                self.logger.info(
                    'Scheduling %s [%s] -> %s/%s [%s].' % (
                        router['name'],
                        str(router['id']),
                        target['host'],
                        target['agent_type'],
                        str(target['id'])
                    )
                )
                self.client.add_router_to_l3_agent(
                    target['id'],
                    {'router_id': router['id']}
                )
        # No agents, any routers?
        elif routers:
            self.logger.warn('No agents found to schedule routers to.')
