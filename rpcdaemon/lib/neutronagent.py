# Threading
from threading import Semaphore

# Datetime parsing
from dateutil.parser import parse as dateparse
from datetime import datetime, timedelta

# JSON
from json import loads

try:
    from neutronclient.v2_0.client import Client
    from neutronclient.common.exceptions import NeutronException as NeutronAgentException
except:
    from quantumclient.v2_0.client import Client
    from quantumclient.common.exceptions import QuantumException as NeutronAgentException


# Generalized neutron agent handler
class NeutronAgent():
    def __init__(self, config, agent_type):
        # Config blob for us
        self.config = config

        # Store what type of agent we are
        self.agent_type = agent_type

        # Dict of agent state information, keyed by id
        self.agents = {}

        # Lock for self.agents access
        self.lock = Semaphore()

        # Agent timeout helpers
        self.downtime = timedelta(seconds=int(self.config['agent_down_time']))
        self.timeout = int(self.config['agent_down_time'])

        # Initialize neutron client
        self.client = Client(
            username=self.config['admin_user'],
            password=self.config['admin_password'],
            tenant_name=self.config['admin_tenant_name'],
            auth_url=self.config['auth_url']
        )

        # Populate agents and states
        self.logger.info('Populating agents...')
        agents = dict([(agent['id'], agent) for agent in
                       self.client.list_agents(agent_type=self.agent_type)['agents']])
        for agent in agents.values():
            agent['heartbeat_timestamp'] = dateparse(
                agent['heartbeat_timestamp']
            )
            self.agents[agent['id']] = agent

        self.logger.debug('Agents: %s' % agents.keys())

    # Empty default handler
    def handle(self, agent, state):
        pass

    # RPC Callback to update agents and states
    def update(self, body, message):
        if 'oslo.message' in body:
            body = loads(body['oslo.message'])

        if body['method'] == 'report_state':
            state = body['args']['agent_state']['agent_state']
            time = body['args']['time']
            host = state['host']

            # Accept our agent type only; '' for all agent types
            if not self.agent_type or state['agent_type'] == self.agent_type:
                self.lock.acquire()  # Lock inside RPC callback

                # Agents to update if we've seen host/type before
                updates = [
                    agent for agent in self.agents.values()
                    if agent['host'] == host
                    and agent['agent_type'] == state['agent_type']
                ]

                # Haven't seen this host/type before?
                if not updates:
                    # Get full agent info
                    updates = [
                        agent for agent in
                        self.client.list_agents(
                            host=host,
                            agent_type=state['agent_type']
                        )['agents']
                    ]

                self.logger.debug(
                    'Updates: %s' % [
                        str(update['host']) + '/' + str(update['agent_type'])
                        for update in updates
                    ]
                )

                # Update state since we got a message
                for agent in updates:
                    self.agents[agent['id']].update(state)
                    self.agents[agent['id']]['heartbeat_timestamp'] = (
                        dateparse(time)
                    )
                    self.agents[agent['id']]['alive'] = True

                self.lock.release()  # Unlock inside RPC callback

        # Ack that sucker
        message.ack()

    # Called in loop
    def check(self):
        self.lock.acquire()  # Lock outside RPC callback
        for agent in self.agents.values():
            # Check timestamp + allowed down time against current time
            if (
                    agent['heartbeat_timestamp'] +
                    self.downtime <
                    datetime.utcnow()
            ):
                # Agent is down!
                self.logger.warn(
                    '%s/%s [%s]: is down.' % (
                        agent['host'],
                        agent['agent_type'],
                        agent['id']
                    )
                )
                self.agents[agent['id']]['alive'] = False

                # Handle down agent
                self.handle(agent, False)
            else:
                # Agent is up!
                self.logger.debug(
                    '%s/%s [%s]: is up.' % (
                        agent['host'],
                        agent['agent_type'],
                        agent['id']
                    )
                )

                # Handle up agent
                self.handle(agent, True)

        self.lock.release()  # Unlock outside RPC callback
