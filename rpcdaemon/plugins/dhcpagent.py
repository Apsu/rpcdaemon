# General
from uuid import uuid4

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
#    def handle(self, host, agent):
#        others = [
#            other for other in self.agents
#            if not host['host'] == host
#            and other['alive']
#        ]
#        routers = self.client.list_routers_on_l3_agent(agent['id'])['routers']
#
#        # Any other agents alive?
#        if others:
#            # Map my routers to other agents
#            mapping = zip(routers, cycle(others))
#
#            # And move them
#            for router, other in mapping:
#                self.logger.info(
#                    'Rescheduling %s(%s) -> %s/%s.' % (
#                        router['name'],
#                        router['id'],
#                        other['host'],
#                        other['type']
#                    )
#                )
#                self.client.remove_router_from_l3_agent(
#                    agent['id'],
#                    router['id']
#                )
#                self.client.add_router_to_l3_agent(
#                    other['id'],
#                    {'router_id': router['id']}
#                )
#        # No agents, any routers?
#        elif routers:
#            self.logger.warn(
#                'No agents found to reschedule routers from %s/%s(%s).' % (
#                    host,
#                    agent['type']
#                )
#            )
