#!/usr/bin/python

# Copyright (C) 2018 Carmine Scarpitta, Pier Luigi Ventre, Stefano Salsano - (CNIT and University of Rome "Tor Vergata")
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Topology extraction entity
# 
# @author Carmine Scarpitta <carmine.scarpitta.94@gmail.com>
# @author Pier Luigi Ventre <pier.luigi.ventre@uniroma2.it>
# @author Stefano Salsano <stefano.salsano@uniroma2.it>
#

import json
import os
import time, threading
import telnetlib
import re 
import networkx as nx
from networkx.drawing.nx_agraph import write_dot
from networkx.readwrite import json_graph
import socket
import sys


def extract_topology(router, ports, period = 10, prevGraph = None):
    
    while (True):
        print
        print "********* Topology Extraction *********"

        stub_networks = dict()  # stub networks disctionary: keys are networks and values are sets of routers advertising the networks
        transit_networks = dict()  # transit networks disctionary: keys are networks and values are sets of routers advertising the networks
        edges = set()   # edges set
        routers = set() # routers set

        for port in ports:
            
            # Check if ./topo_extraction exists, if not create it
            if not os.path.exists(os.getcwd() + "/topo_extraction"): os.makedirs(os.getcwd() + "/topo_extraction")

            G = nx.Graph() # Topology graph

            password = "zebra"
            #router = "2000::c"
            #port = "2606"


            try:
                tn = telnetlib.Telnet(router, port) # Init telnet
            except socket.error:
                print "Error: cannot establish a connection to " + str(router) + " on port " + str(port) + "\n"
                break

            if password:
                tn.read_until("Password: ")
                tn.write(password + "\r\n")
            tn.write("terminal length 0" + "\r\n") # terminal length set to 0 to not have interruptions
            tn.write("show ipv6 ospf6 route intra-area detail"+ "\r\n")  # Get routing info from ospf6 database
            tn.write("q" + "\r\n") # Close
            route_details = tn.read_all()   # Get results
            tn.close() # Close telnet

            with open("topo_extraction/route-detail-" + str(port) + ".txt", "w") as route_file:
                route_file.write(route_details)    # Write database info to a file for post-processing

            with open("topo_extraction/route-detail-" + str(port) + ".txt", "r") as route_file:
                # Process infos and get active routers
                for line in route_file:
                    # Get a network prefix
                    m = re.search('Destination: (\S+)', line)  
                    if(m):
                        net = m.group(1)
                        continue
                    # Get routers advertising that network
                    m = re.search('Adv: (\d*.\d*.\d*.\d*)', line)  
                    if(m):
                        router_id = m.group(1)
                        if stub_networks.get(net) == None:
                            # Network is unknown, mark as a stub network
                            # Each network starts as a stub network, 
                            # then it is processed and (eventually) marked as transit network
                            stub_networks[net] = set()
                        stub_networks[net].add(router_id)   # router can reach net
                        routers.add(router_id)  # Add router to routers list

        # Make separation between stub networks and transit networks
        for net in stub_networks.keys():
            if len(stub_networks[net]) == 2:    
                # net advertised by two routers: mark as a transit network
                transit_networks[net] = stub_networks[net]
                stub_networks.pop(net)
            elif len(stub_networks[net]) > 2:
                print "Error: inconsistent network list"
                exit(-1)

        # Build edges list
        for net in transit_networks.keys():
            if len(transit_networks[net]) >= 2:
                # Link between two routers
                r1 = transit_networks[net].pop()
                r2 = transit_networks[net].pop()
                edge=(r1, r2)
                edges.add(edge)

        for net in stub_networks.keys():
            if len(stub_networks[net]) >= 1:
                # Link between a router and a stub network
                r = stub_networks[net].pop()
                edge=(r, net)
                edges.add(edge)


        # Print results
        print "Stub Networks: ", stub_networks
        print
        print "Routers: ", routers
        print
        print "Edges: ", edges
        print
        print "***************************************"


        # Build NetworkX Topology
        for r in routers:
            G.add_node(r, fillcolor="red", style="filled")
        for r in stub_networks.keys():
            G.add_node(r, fillcolor="cyan", style="filled", shape="box")
        for e in edges:
            if (e[0] in routers or e[0] in stub_networks.keys()) and (e[1] in routers or e[1] in stub_networks.keys()):
                G.add_edge(*e)


        # Export NetworkX object into a json file
        graph = json_graph.node_link_data(G)

        with open("topo_extraction/topo-graph.json", 'wb') as outfile:
            json.dump(graph, outfile, sort_keys = True, indent = 2)

        # Draw graph on a image file
        write_dot(G, 'topo_extraction/topo-graph.dot')
        os.system('dot -Tsvg topo_extraction/topo-graph.dot -o topo_extraction/topo-graph.svg')


        # Wait 'period' seconds between two extractions
        time.sleep(period)

if __name__ == '__main__':

    if len(sys.argv) != 4:
        print "Wrong arguments"    
        print "Usage: " + sys.argv[0] + " <ip_address> <port1,port2,...,portN> <period_in_seconds>" 
        exit(-1)

    router = sys.argv[1]    # Get router ip address
    ports = sys.argv[2]     # Get ports list
    period = float(sys.argv[3]) # Get period and convert it to a float value

    ports = ports.split(",")    # Convert port list from string to a list

    extract_topology(router, ports, period)
    #extract_topology("2000::c", 2606, period=10)
    #extract_topology("2000::c", [2606, 2607, 2608, 2609], period=10)
    
    