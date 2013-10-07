# Threading
from threading import Semaphore

# Datetime parsing
from dateutil.parser import parse as dateparse
from datetime import datetime, timedelta

# Quantumclient
from quantumclient.v2_0.client import Client


# Generalized quantum agent handler
class QuantumAgent():
    def __init__(self, config, agent_type):
        # Config blob for us
        self.config = config

        # Store what type of agent we are
        self.agent_type = agent_type

        # Dict of agent state information, keyed by host
        self.agents = {}

        # Lock for self.agents access
        self.lock = Semaphore()

        # Agent timeout helpers
        self.downtime = timedelta(seconds=int(self.config['agent_down_time']))
        self.timeout = int(self.config['agent_down_time'])

        # Initialize quantum client
        self.client = Client(
            username=self.config['admin_user'],
            password=self.config['admin_password'],
            tenant_name=self.config['admin_tenant_name'],
            auth_url=self.config['auth_url']
        )

        # Populate agents and states
        agents = self.client.list_agents(agent_type=self.agent_type)['agents']
        for agent in agents:
            agent['heartbeat_timestamp'] = dateparse(
                agent['heartbeat_timestamp']
            )
            self.agents[agent['host']] = agent

    # Empty default handler
    def handle(self, host, agent):
        pass

    # RPC Callback to update agents and states
    def update(self, body, message):
        if body['method'] == 'report_state':
            state = body['args']['agent_state']['agent_state']
            time = body['args']['time']
            host = state['host']

            if state['agent_type'] == self.agent_type:
                self.lock.acquire()  # Lock inside RPC callback
                if not host in self.agents:
                    # Get full agent info
                    self.agents[host] = self.client.list_agents(
                        host=host,
                        agent_type=self.agent_type
                    )['agents'][0]

                # Update state since we got a message
                self.agents[host]['heartbeat_timestamp'] = dateparse(time)
                self.agents[host]['alive'] = True
                self.lock.release()  # Unlock inside RPC callback

        # Ack that sucker
        message.ack()

    # Called in loop
    def check(self):
        self.lock.acquire()  # Lock outside RPC callback
        for host, agent in self.agents.items():
            # Check timestamp + allowed down time against current time
            if (
                    agent['heartbeat_timestamp'] +
                    self.downtime <
                    datetime.utcnow()
            ):
                # Agent is down!
                self.logger.debug(
                    '%s/%s(%s): is down.' % (
                        host,
                        agent['agent_type'],
                        agent['id']
                    )
                )
                self.agents[host]['alive'] = False

                # Handle down agent
                self.handle(host, agent)
            else:
                # Agent is up!
                self.logger.debug(
                    '%s/%s(%s): is up.' % (
                        host,
                        agent['agent_type'],
                        agent['id']
                    )
                )

                # Don't need to update state, RPC callback did that

        self.lock.release()  # Unlock outside RPC callback
