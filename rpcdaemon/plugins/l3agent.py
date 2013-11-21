# General
from uuid import uuid4
from itertools import cycle

# Neutron Agent superclass
from rpcdaemon.lib.neutronagent import NeutronAgent, NeutronAgentException

# RPC superclass
from rpcdaemon.lib.rpc import RPC

# Logger wrapper
from rpcdaemon.lib.logger import Logger

# Config parser
from rpcdaemon.lib.config import Config


# Specific L3 agent handler
class L3Agent(NeutronAgent, RPC):
    def __init__(self, connection, config, handler=None):
        # Grab a copy of our config section
        self.config = config.section('L3Agent')

        # grab relevant settings
        queue_expire = self.config.get('queue_expire', 60)

        # Initialize logger
        self.logger = Logger(
            name='l3agent',
            level=self.config['loglevel'],
            handler=handler
        )

        # Parse agent config
        self.qconfig = Config(self.config['conffile'], 'AGENT')

        # Initialize super
        NeutronAgent.__init__(self, self.qconfig, 'L3 agent')

        # Initialize RPC bits
        RPC.__init__(
            self,
            connection,
            exopts={
                'name': self.event_queue(),
                'durable': False,
                'type': 'topic'
            },
            qopts={
                'name': 'rpcdaemon-l3_%s' % uuid4(),
                'auto_delete': True,
                'durable': False,
                'routing_key': 'q-plugin',
                'queue_arguments': {
                    'x-expires': int(queue_expire * 1000),
                }
            }
        )

    # L3 specific handler
    def handle(self, agent, state):
        # All alive agents
        targets = dict([(target['id'], target)
                        for target in self.agents.values()
                        if target['alive']])

        # If agent is down, remove routers first
        if not state:
            routerlist = self.retryable(
                lambda: self.client.list_routers_on_l3_agent(agent['id']))['routers']

            for router in routerlist:
                self.logger.info(
                    'Removing router %s from %s/%s [%s]' % (
                        router['id'],
                        agent['host'],
                        agent['agent_type'],
                        str(agent['id'])
                    )
                )

                self.retryable(
                    lambda: self.client.remove_router_from_l3_agent(agent['id'],
                                                                    router['id']))

        self.logger.debug('Targets: %s' % targets.keys())

        # get all routers
        routerlist = self.retryable(
            lambda: self.client.list_routers())['routers']

        # Get routers on agents
        binds = dict([(router['id'], router) for target in targets
                      for router in routerlist])


        self.logger.debug('Bound Routers: %s' % binds.keys())

        # And routers not on agents
        routers = dict([(router['id'], router)
                        for router in routerlist
                        if not router['id'] in binds])

        self.logger.debug('Free Routers: %s' % routers.keys())

        # Map free routers to agents
        mapping = zip(routers, cycle(targets))

        self.logger.debug('Mapping: %s' % mapping)

        # Any agents alive?
        if targets:
            # Schedule routers to them
            for router, target in mapping:
                self.logger.info(
                    'Scheduling %s [%s] -> %s/%s [%s].' % (
                        routers[router]['name'],
                        str(router),
                        targets[target]['host'],
                        targets[target]['agent_type'],
                        str(target)
                    )
                )
                # this can cause errors if multiple rpcdaemons are running
                msg = 'Router %s already added to agent %s' % (router, target)

                self.retryable(
                    lambda: self.client.add_router_to_l3_agent(
                        target,
                        {'router_id': router}),
                    retries=1, delay=0, 
                    on_fail=lambda x:self.logger.warn(msg))

        # No agents, any routers?
        elif routers:
            self.logger.warn('No agents found to schedule routers to.')
