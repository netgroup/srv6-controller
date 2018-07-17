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
# Topology discovery entity
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
from optparse import OptionParser

# Folder of the dump
TOPO_FOLDER = "topo_discovery"
# In our experiment we use srv6 as default password
PASSWD = "srv6"

def discovery_topology(opts):
	
	# Let's parse the input
	period = float(opts.period)
	routers = []
	ports = []
	# First create the chunk
	ips_ports = opts.ips_ports.split(",")
	for ip_port in ips_ports:
		# Then parse the chunk
		data = ip_port.split("-")
		routers.append(data[0])
		ports.append(data[1])

	# Check if TOPO_FOLDER exists, if not create it
	if not os.path.exists(TOPO_FOLDER):
		os.makedirs(TOPO_FOLDER)

	while (True):
		# stub networks disctionary: keys are networks and values are sets of routers advertising the networks
		stub_networks = dict()
		# transit networks disctionary: keys are networks and values are sets of routers advertising the networks
		transit_networks = dict()
		# edges set
		edges = set()
		# nodes set
		nodes = set()
		# Topology graph
		G = nx.Graph()

		for router, port in zip(routers, ports):
			print "\n********* Connecting to %s-%s *********" %(router, port)
			password = PASSWD
			try:
				tn = telnetlib.Telnet(router, port) # Init telnet
			except socket.error:
				print "Error: cannot establish a connection to " + str(router) + " on port " + str(port) + "\n"
				break

			if password:
				tn.read_until("Password: ")
				tn.write(password + "\r\n")
			# terminal length set to 0 to not have interruptions
			tn.write("terminal length 0" + "\r\n")
			# Get routing info from ospf6 database
			tn.write("show ipv6 ospf6 route intra-area detail"+ "\r\n")
			# Close
			tn.write("q" + "\r\n")
			# Get results
			route_details = tn.read_all()
			tn.close() # Close telnet

			with open("%s/route-detail-%s-%s.txt" %(TOPO_FOLDER , router, port), "w") as route_file:
				route_file.write(route_details)    # Write database info to a file for post-processing

			with open("%s/route-detail-%s-%s.txt" %(TOPO_FOLDER , router, port), "r") as route_file:
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
						nodes.add(router_id)  # Add router to routers list

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
		print "Stub Networks:", stub_networks
		print "Nodes:", nodes
		print "Edges:", edges
		print "***************************************"

		# Build NetworkX Topology
		for r in nodes:
			G.add_node(r, fillcolor="red", style="filled")
		for r in stub_networks.keys():
			G.add_node(r, fillcolor="cyan", style="filled", shape="box")
		for e in edges:
			if (e[0] in nodes or e[0] in stub_networks.keys()) and (e[1] in nodes or e[1] in stub_networks.keys()):
				G.add_edge(*e)


		# Export NetworkX object into a json file
		graph = json_graph.node_link_data(G)

		with open("%s/topo-graph.json" %(TOPO_FOLDER), 'wb') as outfile:
			json.dump(graph, outfile, sort_keys = True, indent = 2)

		# Draw graph on a image file
		write_dot(G, '%s/topo-graph.dot' %(TOPO_FOLDER))
		os.system('dot -Tsvg %s/topo-graph.dot -o %s/topo-graph.svg' %(TOPO_FOLDER, TOPO_FOLDER))

		# Wait 'period' seconds between two extractions
		time.sleep(period)

# Parse command line options and dump results
def parseOptions():
	parser = OptionParser()
	# ip:port of the routers
	parser.add_option('--ip_ports', dest='ips_ports', type='string', default="127.0.0.1-2606",
					  help='ip-port,ip-port map ip port of the routers')
	# Topology discovery period
	parser.add_option('--period', dest='period', type='string', default="10",
					  help='topology discovery period')
	# Parse input parameters
	(options, args) = parser.parse_args()
	# Done, return
	return options

if __name__ == '__main__':
	# Let's parse input parameters
	opts = parseOptions()
	# Deploy topology
	discovery_topology(opts)
