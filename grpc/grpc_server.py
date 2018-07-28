#!/usr/bin/python

from concurrent import futures
from optparse import OptionParser
from pyroute2 import IPRoute
from google.protobuf import json_format


import logging
import time
import json
import grpc

import srv6_explicit_path_pb2_grpc
import srv6_explicit_path_pb2

# Global variables definition

# Server reference
grpc_server = None
# Netlink socket
ip_route = None
# Cache of the resolved interfaces
interfaces = ['eth0']
idxs = {}
# logger reference
logger = logging.getLogger(__name__)
# Server ip and port
GRPC_IP = "::"
GRPC_PORT = 12345
# Debug option
SERVER_DEBUG = False
# Secure option
SECURE = False
# Server certificate
CERTIFICATE = "cert_server.pem"
# Server key
KEY = "key_server.pem"

class SRv6ExplicitPathHandler(srv6_explicit_path_pb2_grpc.SRv6ExplicitPathServicer):
  """gRPC request handler"""

  def Execute(self, op, request, context):
    logger.debug("config received:\n%s", request)
    # Let's push the routes
    for path in request.path:
      # Rebuild segments
      segments = []
      for srv6_segment in path.sr_path:
        segments.append(srv6_segment.segment)
      ip_route.route(op, dst=path.destination, oif=idxs[path.device],
        encap={'type':'seg6', 'mode':path.encapmode, 'segs':segments})
    # and create the response
    return srv6_explicit_path_pb2.SRv6EPReply(message="OK")

  def Create(self, request, context):
    # Handle Create operation 
    return self.Execute("add", request, context)


  def Remove(self, request, context):
    # Handle Remove operation 
    return self.Execute("del", request, context)

# Start gRPC server
def start_server():
  # Configure gRPC server listener and ip route
  global grpc_server, ip_route
  # Setup gRPC server
  if grpc_server is not None:
    logger.error("gRPC Server is already up and running")
  else:
    # Create the server and add the handler
    grpc_server = grpc.server(futures.ThreadPoolExecutor())
    srv6_explicit_path_pb2_grpc.add_SRv6ExplicitPathServicer_to_server(SRv6ExplicitPathHandler(),
                                                                        grpc_server)
    # If secure we need to create a secure endpoint
    if SECURE:
      # Read key and certificate
      with open(KEY) as f:
        key = f.read()
      with open(CERTIFICATE) as f:
        certificate = f.read()
      # Create server ssl credentials
      grpc_server_credentials = grpc.ssl_server_credentials(((key, certificate,),))
      # Create a secure endpoint
      grpc_server.add_secure_port("[%s]:%s" %(GRPC_IP, GRPC_PORT), grpc_server_credentials)
    else:
      # Create an insecure endpoint
      grpc_server.add_insecure_port("[%s]:%s" %(GRPC_IP, GRPC_PORT))
  # Setup ip route
  if ip_route is not None:
    logger.error("IP Route is already setup")
  else:
    ip_route = IPRoute()
  # Resolve the interfaces
  for interface in interfaces:
    idxs[interface] = ip_route.link_lookup(ifname=interface)[0]
  # Start the loop for gRPC
  logger.info("Listening gRPC")
  grpc_server.start()
  while True:
    time.sleep(5)

# Parse options
def parse_options():
  global SECURE
  parser = OptionParser()
  parser.add_option("-d", "--debug", action="store_true", help="Activate debug logs")
  parser.add_option("-s", "--secure", action="store_true", help="Activate secure mode")
  # Parse input parameters
  (options, args) = parser.parse_args()
  # Setup properly the logger
  if options.debug:
    logging.basicConfig(level=logging.DEBUG)
  else:
    logging.basicConfig(level=logging.INFO)
  # Setup properly the secure mode
  if options.secure:
    SECURE = True
  else:
    SECURE = False
  SERVER_DEBUG = logger.getEffectiveLevel() == logging.DEBUG
  logger.info("SERVER_DEBUG:" + str(SERVER_DEBUG))

if __name__ == "__main__":
  parse_options()
  start_server()
