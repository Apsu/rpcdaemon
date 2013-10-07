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

        # Dict of agent state information, keyed by id
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
        agents = {
            agent['id']: agent for agent in
            self.client.list_agents(agent_type=self.agent_type)['agents']
        }
        for agent in agents.values():
            agent['heartbeat_timestamp'] = dateparse(
                agent['heartbeat_timestamp']
            )
            self.agents[agent['id']] = agent

    # Empty default handler
    def handle(self, agent, state):
        pass

    # RPC Callback to update agents and states
    def update(self, body, message):
        if body['method'] == 'report_state':
            state = body['args']['agent_state']['agent_state']
            time = body['args']['time']
            host = state['host']

            if state['agent_type'] == self.agent_type:
                self.lock.acquire()  # Lock inside RPC callback
                if not host in [
                        agent['host'] for agent in self.agents.values()
                ]:
                    # Get full agent info
                    self.agents.update(
                        {
                            agent['id']: agent for agent in
                            self.client.list_agents(
                                host=host,
                                agent_type=self.agent_type
                            )['agents']
                        }
                    )

                # Update state since we got a message
                for agent in self.agents.values():
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
                self.logger.debug(
                    '%s/%s(%s): is down.' % (
                        agent['host'],
                        agent['agent_type'],
                        agent['id']
                    )
                )
                self.agents[agent['host']]['alive'] = False

                # Handle down agent
                self.handle(agent, False)
            else:
                # Agent is up!
                self.logger.debug(
                    '%s/%s(%s): is up.' % (
                        agent['host'],
                        agent['agent_type'],
                        agent['id']
                    )
                )

                # Handle up agent
                self.handle(agent, True)

        self.lock.release()  # Unlock outside RPC callback
