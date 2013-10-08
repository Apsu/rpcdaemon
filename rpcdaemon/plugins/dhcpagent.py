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

        # Parse agent conf
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
    def handle(self, agent, state):
        # All alive agents
        targets = [
            target for target in self.agents.values()
            if target['alive']
        ]

        # If agent is down, remove networks first
        if not state:
            for network in (
                self.client.list_networks_on_dhcp_agent(
                    agent['id']
                )['networks']
            ):
                self.logger.info(
                    'Removing network %s from %s/%s [%s]' % (
                        network['id'],
                        agent['host'],
                        agent['agent_type'],
                        str(agent['id'])
                    )
                )
                self.client.remove_network_from_dhcp_agent(
                    agent['id'],
                    network['id']
                )

        self.logger.debug(
            'Targets: %s' % [str(target['id']) for target in targets]
        )

        # Networks on agents
        binds = [
            network for target in targets
            for network in
            self.client.list_networks_on_dhcp_agent(target['id'])['networks']
        ]

        self.logger.debug(
            'Bound Networks: %s' % [str(bind['id']) for bind in binds]
        )

        # Networks not on agents
        networks = [
            network
            for network in self.client.list_networks()['networks']
            if not network in binds
        ]

        self.logger.debug(
            'Free Networks: %s' % [str(network['id']) for network in networks]
        )

        # Any agents alive?
        if targets:
            mapping = product(networks, targets)

            # And schedule them
            for network, target in mapping:
                self.logger.info(
                    'Scheduling %s [%s] -> %s/%s [%s].' % (
                        network['name'],
                        str(network['id']),
                        target['host'],
                        target['agent_type'],
                        str(target['id'])
                    )
                )
                self.client.add_network_to_dhcp_agent(
                    target['id'],
                    {'network_id': network['id']}
                )
        # No agents, any networks?
        elif networks:
            self.logger.warn('No agents found to schedule networks to.')
