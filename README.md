# SRv6 Controller

This project provides a collection of modules implementing different functionalities of a SDN controller

### Topology Information Extraction ###

This project includes a module named ***ti_extraction.py*** for extracting network topology from a router running OSPF6 protocol. This module is invoked with router IP address, a list of ports on which OSPF6 daemon(s) VTY is listening and the interval between two extractions. It buils a NetworkX object and exports it into a JSON file in the folder ***topo_extraction***. Network graph is also exported as an image file in the same folder.

Run an example experiment

    > cd /home/user/workspace/srv6-controller

    Usage: ti_extraction.py <ip_address> <port1,port2,...,portN> <period_in_seconds>

    Options:
    <ip_address> ip address of the router
    <port1,port2,...,portN> telnet ports of the daemons
    <period_in_seconds> polling period in seconds

You can extract topology from ospfd

    > ./ti_extraction.py 2000::c 2606 1

After a while the enitity will populate the ***topo_extraction*** folder with the topology files

	> route-detail-2609.txt
	> topo-graph.dot
	> topo-graph.json
	> topo-graph.svg

### SRv6 Southbound API ###

The project provides four different implementations of the SRv6 Southbound API: i) gRPC; ii) NETCONF; iii) REST; iv) SSH.
Each folder contains the server and the client implementation.

As of the server, it requires the init of the variable interfaces which defines the interface under the control of the SRv6Manager

    interfaces = ['eth0']

For the NETCONF and SSH implementation it is required to properly initialized USER and PASSWORD

    SSH_USER = 'srv6'
    SSH_PASSWORD = 'srv6'

Run the server

    > cd /home/user/workspace/srv6-controller/*

    Usage: *_server.py [options]

    Options:
        -h, --help    show this help message and exit
        -d, --debug   Activate debug logs
        -s, --secure  Activate secure mode

Instead for the client, it is necessary to define the mode and the IP/PORT of the server

    SECURE = False
    srv6_stub,channel = get_grpc_session(IP, PORT, SECURE)

NETCONF and SSH implementation does support only secure mode

Run the client
    
    > cd /home/user/workspace/srv6-controller/*

    Usage: *_client.py