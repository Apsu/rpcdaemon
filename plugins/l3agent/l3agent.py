# General
from uuid import uuid4

# Quantum Agent superclass
from rpcdaemon.plugins.l3agent.quantumagent import QuantumAgent


class L3Agent(QuantumAgent):
    def __init__(self, connection, conf, handler=None):
        # Grab a copy of our config section
        self.conf = conf.section('L3Agent')

        # Parse quantum.conf
        self.qconf = Config(file=conf['conffile'], section='AGENT')

        super(L3Agent, self).__init__(
            connection,
            qconf,
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

        # Initialize logger
        self.logger = logging.getLogger('l3-agent')
        self.logger.setLevel(conf['loglevel'])
        self.logger.addHandler(handler)  # Existing daemon log handler

        # Populate L3 agents
        self.logger.debug('Prepopulating L3 agents.')
        for agent in self.client.list_agents(agent_type='L3 agent')['agents']:
            self.agents[agent['host']] = ({
                agent['agent_type']: {
                    'heartbeat_timestamp': dateparse(
                        agent['heartbeat_timestamp']
                    ),
                    'alive': agent['alive']
                }
            })

    def update_states(self, body, message):
        if body['method'] == 'report_state':
            state = body['args']['agent_state']['agent_state']
            time = body['args']['time']
            host = state['host']
            type = state['agent_type']  # Ok to override builtin, honest

            # L3 agents only
            if type == 'L3 agent':
                self.lock.acquire()  # Lock
                if not host in self.agents:
                    self.agents[host] = {}
                self.agents[host][type] = {
                    'heartbeat_timestamp': dateparse(time),
                    'alive': True
                }
                self.lock.release()  # Unlock
        else:
            # Skip other RPC methods
            pass
        message.ack()



    def reschedule_routers(self, host, type):
        agents = self.client.list_agents(agent_type=type)['agents']
        mine = [agent for agent in agents if agent['host'] == host][0]
        if not mine:
            self.logger.warn('%s/%s not found.' % (host, type))
            return

        rest = [
            agent for agent in agents
            if not agent['host'] == host
            and agent['alive']
        ]
        routers = self.client.list_routers_on_l3_agent(mine['id'])['routers']

        # Any other agents alive?
        if rest:
            # Map my routers to other agents
            mapping = zip(routers, cycle(rest))

            # And move them
            for router, agent in mapping:
                self.logger.info(
                    'Rescheduling %s/%s(%s) -> %s.' % (
                        host,
                        router['name'],
                        router['id'],
                        agent['host']
                    )
                )
                self.client.remove_router_from_l3_agent(
                    mine['id'],
                    router['id']
                )
                self.client.add_router_to_l3_agent(
                    agent['id'],
                    {'router_id': router['id']}
                )
        elif routers:
            self.logger.warn(
                'No agents found to reschedule routers from %s/%s.' % (
                    host,
                    type
                )
            )

    def check_states(self):
        self.lock.acquire()  # Lock
        for host, agents in self.worker.agents.items():
            for type, info in agents.items():
                # Check timestamp + allowed down time against current time
                if (
                        info['heartbeat_timestamp'] +
                        self.downtime <
                        datetime.utcnow()
                ):
                    self.logger.debug('%s/%s: is down.' % (host, type))
                    self.worker.agents[host][type]['alive'] = False
                    self.reschedule_routers(host, type)
                else:
                    self.logger.debug('%s/%s: is up.' % (host, type))
                    self.worker.agents[host][type]['alive'] = True
        self.lock.release()  # Unlock

def do():
    print "l3agent!"
