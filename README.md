RPC Daemon
==========

**THIS IS AN ACTIVE WORK IN PROGRESS**
*It is probably unusable at any given time.*

This is an AMQP RPC Daemon, primarily intended for tracking and responding to OpenStack Quantum agent state changes and rescheduling resources appropriately.

It currently supports L3 agents, DHCP agents and a special Dump plugin to blindly log RPC messages.

The current framework correctly daemonizes and operates as a singleton by using a pidfile.
