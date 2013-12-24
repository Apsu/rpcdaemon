# RPCDAEMON #

## Overview ##

*Note: This project currently supports both the Grizzly and Havana releases of OpenStack, though we will refer to Havana's Neutron for the purposes of this doc.*

Currently, OpenStack does not have built-in support for highly available virtual routers or DHCP services. In the existing releases, virtual routers and DHCP services are scheduled to a single Neutron network node, and are not rescheduled on network node failure.

Since virtual router and DHCP services are normally scheduled approximately evenly, the failure of a single Neutron network node could cause IP addressing and routing failure on a number of networks proportional to the number of Neutron network nodes in use. Because this is generally an unacceptable risk in production environments, most production deployments of OpenStack have traditionally used either the "old-style" nova network driver in HA mode instead of Neutron, or chosen to use Neutron with provider networks so as to externalize these services for higher availability.

This has the unfortunate consequence of reducing the utility of software defined networking, which is frequently one of the most compelling features of OpenStack itself. While the Neutron project itself will likely find solutions to the problem, production requirements dictated that a solution to the problem be found sooner.  To attempt to solve some of these issues, we have developed a service to monitor topology changes in a running OpenStack cluster, and automatically make changes to the networking configuration to maintain availability of services even in the event of Neutron network node failure.

## Theory of Operation ##

The RPCDaemon is a python-based daemon that subscribes to the AMQP message bus and watches for events that it should take action on.  Three plugins are currently implemented:

* **DHCPAgent**: Implements high availability in DHCP services

* **L3Agent**: Implements high availability in virtual routers

* **Dump**: Simple plugin to dump message traffic. This is typically only used for development or troubleshooting purposes.

### DHCPAgent ###

The operation of the DHCPAgent plugin is simple to describe. At periodic intervals, DHCP services are removed from any Neutron DHCP agent that is no longer reporting itself as available. In addition, DHCP services are provisioned on every Neutron DHCP agent node that doesn't already have them provisioned.

In addition, when a DHCP enabled network is removed, the DHCPAgent plugin ensures that DHCP services are deprovisioned on all Neutron DHCP agent nodes.

The operational effect of these actions is that when creating new DHCP enabled networks, DHCP servers appear on every Neutron network node, rather than on a single Neutron network node. While this slightly increases DHCP traffic from multiple offers to each DHCP discovery request, it does so safely, as the OpenStack DHCP implementation uses DHCP reservations to ensure virtual machines always boot with predictable IP addresses.

Because of this, DHCP requests can continue to be serviced by other available network nodes, even in the event of catastrophic failure of a single network node.

### L3Agent ###

The L3 agent also runs periodically, but is only interested in virtual routers that are currently assigned to L3 agents that have become inactive. If the L3Agent plugin observes a "down" L3 agent that Neutron believes is hosting a virtual router, then the L3Agent plugin deprovisions the virtual router from that node and reprovisions it on another active Neutron L3 agent node.

This reprovisioning action does not occur immediately, and there will be some minimal network interruption while the virtual router is migrated, however the corrective action happens without intervention, and any network outage is transient. While not perfect, this does allow a higher availability of virtual routing, and may be acceptable for some production workloads.

## Configuration ##

While not all of the configuration options are currently exposed by the Rackspace Private Cloud cookbooks, the following is a description of the configuration values in the rpcdaemon configuration file (typically located at `/etc/rpcdaemon.conf`)

The configuration file is a python ConfigParser ini-style file. There is one section for general daemon settings, and then configuration sections for each plugin.

### Daemon Options ###

General daemon options are specified in the `Daemon` section of the configuration file. Available options include:

* **plugins**: Space-separated list of plugins to load. Valid options include L3Agent, DHCPAgent, and Dump.

* **rpchost**: Kombu connection url for the OpenStack message server.  In the case of rabbitmq, an IP address is sufficient. See the [Kombu Documentation] (http://kombu.readthedocs.org/en/latest/userguide/connections.html) for more information on Kombu connection urls.

* **pidfile**: Location of the daemon pid file.

* **logfile**: Location of the log file.

* **loglevel**: Verbosity of logging. Valid options include DEBUG, INFO, WARNING, ERROR, and CRITICAL.

* **check_interval**: How often to run plugin checks.

### L3Agent Options ###

L3Agent options are specified in the `L3Agent` section of the configuration file. The L3Agent logs to the logfile specified in the `Daemon` section, but the log level of the L3Agent can be configured independently of the daemon itself. Available configuration options include:

* **conffile**: Path to the neutron configuration file.

* **loglevel**: Verbosity of logging.

* **timeout**: Max time for API calls to complete. This also affects failover speed.

* **queue_expire**: Auto-terminate rabbitmq queues if no activity in specified time.

### DHCPAgent ###

DHCPAgent options are specified in the `DHCPAgent` section of the configuration file. Like the L3Agent, logs will also be sent to the logfile specified in the `Daemon` section, while the log level is independently configurable. The DHCPAgent takes the same configuration options as the L3Agent, namely:

* **conffile**: Path to the neutron configuration file.

* **loglevel**: Verbosity of logging.

* **timeout**: Max time for API calls to complete. This also affects failover speed.

* **queue_expire**: Auto-terminate rabbitmq queues if no activity in specified time.

### Dump ###

Unsurprisingly, the Dump plugin options are specified in the `Dump` section of the configuration file. In daemon mode, the Dump plugin will log to the logfile specified in the `Daemon` section, and although the log level is configurable, dumped messages are emitted at DEBUG level, so any other loglevel setting is essentially useless.

The Dump plugin is most useful when running in foreground mode. See the `Command Line Options` section for more information.

Available options:

* **loglevel**: Any valid loglevel verbosity, but should be DEBUG as explained previously.

* **queue**: Queue to dump. Typically `neutron` to view network related messages.

## Command Line Options ##

The RPCDaemon currently understands only two command-line options:

* **-d**: Don't detach (run in foreground). When running in foreground, a pidfile is not dropped, the default log level is set to DEBUG, and the daemon logs to stderr rather than the specified logfile.  This is most useful for running the Dump plugin, but can be helpful in development mode as well.

* **-c <config file>**: Path to configuration file. The default configuration file path is `/usr/local/etc/rpcdaemon.conf`, but init scripts on packaged version of RPCDaemon pass `-c /etc/rpcdaemon.conf`.
