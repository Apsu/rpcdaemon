# General
from uuid import uuid4
from itertools import product

# Quantum Agent superclass
from rpcdaemon.lib.quantumagent import QuantumAgent

# RPC superclass
from rpcdaemon.lib.rpc import RPC

# Logger wrapper
from rpcdaemon.lib.logger import Logger

# Config parser
from rpcdaemon.lib.config import Config


# Specific DHCP agent handler
class DHCPAgent(QuantumAgent, RPC):
    def __init__(self, connection, config, handler=None):
        # Grab a copy of our config section
        self.config = config.section('DHCPAgent')

        # Initialize logger
        self.logger = Logger(
            name='dhcpagent',
            level=self.config['loglevel'],
            handler=handler
        )

        # Parse quantum.conf
        self.qconfig = Config(self.config['conffile'], 'AGENT')

        # Initialize super
        QuantumAgent.__init__(self, self.qconfig, 'DHCP agent')

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
                'name': 'rpcdaemon-dhcp_%s' % uuid4(),
                'auto_delete': True,
                'durable': False,
                'routing_key': 'q-plugin'
            }
        )

    # DHCP specific handler
    def handle(self, host, agent, state):
        # All alive agents
        targets = [
            target for target in self.agents.values()
            if not target['host'] == host
            and target['alive']
        ] if not state else self.agents.values()

        # Map networks to all agents they're not already on
        mapping = [
            (network, target) for network in
            self.client.list_networks()['networks']
            for target in targets
            if not network in
            self.client.list_networks_on_dhcp_agent(target['id'])['networks']
        ]

        # Any agents alive?
        if targets:
            # And schedule them
            for network, target in mapping:
                self.logger.info(
                    'Scheduling %s(%s) -> %s/%s.' % (
                        network['name'],
                        network['id'],
                        target['host'],
                        target['agent_type']
                    )
                )
                self.client.add_network_to_dhcp_agent(
                    target['id'],
                    {'network_id': network['id']}
                )
        # No agents, any networks?
        elif networks:
            self.logger.warn('No agents found to schedule networks.')
