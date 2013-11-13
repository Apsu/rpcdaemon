# General
from uuid import uuid4
from itertools import product

# Neutron Agent superclass
from rpcdaemon.lib.neutronagent import NeutronAgent, NeutronAgentException



# RPC superclass
from rpcdaemon.lib.rpc import RPC

# Logger wrapper
from rpcdaemon.lib.logger import Logger

# Config parser
from rpcdaemon.lib.config import Config


# Specific DHCP agent handler
class DHCPAgent(NeutronAgent, RPC):
    def __init__(self, connection, config, handler=None):
        # Grab a copy of our config section
        self.config = config.section('DHCPAgent')

        # grab relevant settings
        queue_expire = self.config.get('queue_expire', 60)

        # Initialize logger
        self.logger = Logger(
            name='dhcpagent',
            level=self.config['loglevel'],
            handler=handler
        )

        # Parse agent conf
        self.qconfig = Config(self.config['conffile'], 'AGENT')

        # Initialize super
        NeutronAgent.__init__(self, self.qconfig, 'DHCP agent')

        # Initialize RPC bits
        RPC.__init__(
            self,
            connection,
            exopts={
                'name': 'neutron',
                'durable': False,
                'type': 'topic'
            },
            qopts={
                'name': 'rpcdaemon-dhcp_%s' % uuid4(),
                'auto_delete': True,
                'durable': False,
                'routing_key': 'q-plugin',
                'queue_arguments'={
                    'x-expires': int(queue_expire * 1000),
                }
            }
        )

    # DHCP specific handler
    def handle(self, agent, state):
        # All alive agents
        targets=dict([(target['id'], target)
                      for target in self.agents.values()
                      if target['alive']])

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
                # Races between multiple rpc agents can make this
                # crash
                try:
                    self.client.remove_network_from_dhcp_agent(
                        agent['id'],
                        network['id']
                    )
                except NeutronAgentException:
                    self.logger.warn('Network %s already removed from agent %s' % (
                        network['id'], agent['id']))

        self.logger.debug('Targets: %s' % targets.keys())

        # Get all networks
        networks = dict([(network['id'], network)
                         for network in
                         self.client.list_networks()['networks']])

        self.logger.debug('All Networks: %s' % networks.keys())

        # Map agents to missing networks
        mapping = dict([(target, [
                        missing for missing in networks
                        if missing not in [
                            network['id'] for network in
                            self.client.list_networks_on_dhcp_agent(target)
                            ['networks']
                        ]
                    ]) for target in targets])

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
                    # This can race between multiple rpcdaemon
                    # instances
                    try:
                        self.client.add_network_to_dhcp_agent(
                            target,
                            {'network_id': network}
                        )
                    except NeutronAgentException:
                        self.logger.warn('Network %s already added to agent %s' % (
                            network, target))
                        pass
        # No agents, any networks?
        elif networks:
            self.logger.warn('No agents found to schedule networks to.')
