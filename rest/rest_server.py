#!/usr/bin/python

from optparse import OptionParser
from pyroute2 import IPRoute
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from collections import namedtuple
from urlparse import parse_qs

import logging
import time
import json
import socket
import ssl

# Global variables definition

# Server reference
rest_server = None
# Netlink socket
ip_route = None
# Cache of the resolved interfaces
interfaces = ['eth0']
idxs = {}
# logger reference
logger = logging.getLogger(__name__)
# Server ip/ports
REST_IP = "::"
REST_PORT = 8080
# Debug option
SERVER_DEBUG = False
# SRv6 base path
SRV6_BASE_PATH = "/srv6-explicit-path"
# HTTP utilities
ResponseStatus = namedtuple("HTTPStatus", ["code", "message"])
ResponseData = namedtuple("ResponseData", ["status"])
HTTP_STATUS = {"OK": ResponseStatus(code=204, message="OK"),
               "NOT_FOUND": ResponseStatus(code=404, message="Not found")}
PUT = "PUT"
DELETE = "DELETE"
# SRv6 mapping
OP = {
  "create":"add",
  "remove":"del",
  "destination":"dst",
  "device":"dev",
  "encapmode":"encapmode",
  "segments":"segs"
}
# SSL certificate
CERTIFICATE = 'cert_server.pem'

# HTTP utilities class
class HTTPUtils:
  """ Class containing utilities method for HTTP processing """

  """
  SRv6 explicit path configuration example

  POST /srv6-explicit-path?operation={create|remove}

  {
    "paths": [
      {
        "device": "eth0",
        "destination": "2222:4::2/128",
        "encapmode": "inline",
        "segments": [
          "2222:3::2"
        ]
      },
      {
        "device": "eth0",
        "destination": "3333:4::2/128",
        "encapmode": "encap",
        "segments": [
          "3333:3::2",
          "3333:2::2",
          "3333:1::2"
        ]
      }
    ]
  }
  """

  @staticmethod
  def get_srv6_p(http_path):
    # Init steps
    path = {}
    # Get srv6 path
    for k,v in http_path.iteritems():
      # Translating key and saving values
      path[OP[k]] = v
    return path

  @staticmethod
  def get_srv6_ep(request, query):
    # Init steps
    msg = {}
    # Get operation type
    op_type = OP[query['operation'][0]]
    # Let's parse paths
    length = int(request.headers['Content-Length'])
    http_data = request.rfile.read(length)
    http_data = json.loads(http_data)
    # Get paths
    paths = []
    http_paths = http_data['paths']
    for http_path in http_paths:
      paths.append(HTTPUtils.get_srv6_p(http_path))
    # Finally let's fill the python dict
    msg['operation'] = op_type
    msg['paths'] = paths
    return msg

class HTTPv6Server(HTTPServer):
  address_family = socket.AF_INET6

class SRv6HTTPv6Server(ThreadingMixIn, HTTPv6Server):
  """An HTTP Server that handles each srv6-explicit-path request using a new thread"""
  daemon_threads = True

class SRv6HTTPRequestHandler(BaseHTTPRequestHandler):
  """"HTTP 1.1 SRv6 request handler"""
  protocol_version = "HTTP/1.1"

  def setup(self):
    self.wbufsize = -1
    self.disable_nagle_algorithm = True
    BaseHTTPRequestHandler.setup(self)

  def send_headers(self, status):
    # Send proper HTTP headers
    self.send_response(status.code, status.message)
    self.end_headers()

  def do_POST(self):
    # Extract values from the query string
    path, _, query_string = self.path.partition('?')
    query = parse_qs(query_string)
    # Handle post requests
    if path == SRV6_BASE_PATH:
      srv6_config = HTTPUtils.get_srv6_ep(self, query)
      """
      {
        "paths": [
          {
            "dev": "eth0",
            "dst": "2222:4::2/128",
            "encapmode": "inline",
            "segs": [
              "2222:3::2"
            ]
          },
          {
            "dev": "eth0",
            "dst": "3333:4::2/128",
            "encapmode": "encap",
            "segs": [
              "3333:3::2",
              "3333:2::2",
              "3333:1::2"
            ]
          }
        ]
      }
      """
      logger.debug("config received:\n%s", json.dumps(srv6_config, indent=2, sort_keys=True))
      # Let's push the routes
      for path in srv6_config["paths"]:
        ip_route.route(srv6_config["operation"], dst=path['dst'], oif=idxs[path['dev']],
          encap={'type':'seg6', 'mode':path['encapmode'], 'segs':path['segs']})
      # and create the response
      response = ResponseData(status=HTTP_STATUS["OK"])
    else:
      # Unexpected paths
      logger.info("not supported yet")
      response = ResponseData(status=HTTP_STATUS["NOT_FOUND"])
    # Done, send back the respons
    self.send_headers(response.status)

# Start HTTP/HTTPS server
def start_server(secure):
  # Configure Server listener and ip route
  global rest_server, ip_route
  # Setup server
  if rest_server is not None:
    logger.error("HTTP/HTTPS Server is already up and running")
  else:
    rest_server = SRv6HTTPv6Server((REST_IP, REST_PORT), SRv6HTTPRequestHandler)

    # If secure let's protect the socket with ssl
    if secure:
      rest_server.socket = ssl.wrap_socket(rest_server.socket, certfile=CERTIFICATE,
                                          server_side=True)
  # Setup ip route
  if ip_route is not None:
    logger.error("IP Route is already setup")
  else:
    ip_route = IPRoute()
  # Resolve the interfaces
  for interface in interfaces:
    idxs[interface] = ip_route.link_lookup(ifname=interface)[0]
  # Start the loop for REST
  logger.info("Listening %s" %("HTTPS" if secure else "HTTP"))
  rest_server.serve_forever()

# Parse options
def parse_options():
  global REST_PORT
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
  SERVER_DEBUG = logger.getEffectiveLevel() == logging.DEBUG
  logger.info("SERVER_DEBUG:" + str(SERVER_DEBUG))
  # Return secure/insecure mode
  if options.secure:
    REST_PORT = 443
    return True
  return False

if __name__ == "__main__":
  secure = parse_options()
  start_server(secure)
