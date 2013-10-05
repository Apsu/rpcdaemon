RPC Daemon
==========

This is an AMQP RPC Daemon, primarily intended for tracking and responding to OpenStack Quantum agent state changes and rescheduling resources appropriately.

It currently supports L3 agents and DHCP agents are coming shortly.

The future plan is to generalize the framework and integrate arbitrary code for classifying and processing data received via RPC.

The current framework correctly daemonizes and operates as a singleton by using a pidfile.
