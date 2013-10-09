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
        targets = {
            target['id']: target for target in self.agents.values()
            if target['alive']
        }

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

        self.logger.debug('Targets: %s' % targets.keys())

        # Get all networks
        networks = {
            network['id']: network for network in
            self.client.list_networks()['networks']
        }

        self.logger.debug('All Networks: %s' % networks.keys())

        # Map agents to missing networks
        mapping = {
            target: [
                missing for missing in networks
                if missing not in [
                    network['id'] for network in
                    self.client.list_networks_on_dhcp_agent(target)
                    ['networks']
                ]
            ]
            for target in targets
        }

        self.logger.debug('Mapping: %s' % mapping)

        # Any agents alive?
        if targets:
            # Schedule networks to them
            for target in mapping:
                for network in mapping[target]:
                    self.logger.info(
                        'Scheduling %s [%s] -> %s/%s [%s].' % (
                            networks[network]['name'],
                            str(network),
                            targets[target]['host'],
                            targets[target]['agent_type'],
                            str(target)
                        )
                    )
                    self.client.add_network_to_dhcp_agent(
                        target,
                        {'network_id': network}
                    )
        # No agents, any networks?
        elif networks:
            self.logger.warn('No agents found to schedule networks to.')
