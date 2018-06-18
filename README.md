# SRv6 Controller

This project provides a collection of modules implementing different functionalities of a SDN controller

### Topology Discovery ###

This project includes a module named ***td_entity.py*** for extracting network topology from a router running OSPF6 protocol. This module is invoked with router IP address, a list of ports on which OSPF6 daemon(s) VTY is listening and the interval between two extractions. It buils a NetworkX object and exports it into a JSON file in the folder ***topo_extraction***. Network graph is also exported as an image file in the same folder.

Run an example experiment

    > cd /home/user/workspace/srv6-controller

    Usage: td_entity.py <ip_address> <port1,port2,...,portN> <period_in_seconds>

    Options:
    <ip_address> ip address of the router
    <port1,port2,...,portN> telnet ports of the daemons
    <period_in_seconds> polling period in seconds

You can extract topology from ospfd

    > ./td_entity 2000::c 2606 1

After a while the enitity will populate the ***topo_extraction*** folder with the topology files

	> route-detail-2609.txt
	> topo-graph.dot
	> topo-graph.json
	> topo-graph.svg
