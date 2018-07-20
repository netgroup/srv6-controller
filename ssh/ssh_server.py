#!/usr/bin/python

from optparse import OptionParser
from pyroute2 import IPRoute

import logging
import time
import json
import paramiko
import SocketServer
import traceback
import threading
import subprocess
import os

# Global variables definition

# Server reference
ssh_server = None
# logger reference
logger = logging.getLogger(__name__)
# Server port, user and password
SSH_PORT = 220
SSH_USER = 'srv6'
SSH_PASSWORD = 'srv6'
SSH_IP = '0.0.0.0'
# Debug option
SERVER_DEBUG = False
# Closing message
CLOSING_MESSAGE = "\r\nbye\r\n"

class SSHKeyHandler(object):
  """ Handler for SSH key """

  def __init__(self, host_key=None):
    # Parse host key
    self.host_key = host_key
    self.parse_host_key()

  def parse_host_key(self):
    # Read defined host key and parses it
    if self.host_key:
      assert os.path.exists(host_key)
      self.host_key = paramiko.RSAKey.from_private_key_file(host_key)
    else:
      for keypath in [ "/etc/ssh/ssh_host_rsa_key",
                        "/etc/ssh/ssh_host_dsa_key"]:
        if os.path.exists(keypath):
          self.host_key = paramiko.RSAKey.from_private_key_file(keypath)
          break

class SSHRequestHandler(paramiko.ServerInterface):
  """ Implements paramiko based SSH request handler """

  def __init__(self, key_handler):
    self.event = threading.Event()
    self.key_handler = key_handler

  def check_channel_request(self, kind, chanid):
    # We support only session
    if kind == 'session':
        return paramiko.OPEN_SUCCEEDED
    return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

  def check_auth_password(self, username, password):
    # We support only auth with username and password
    if (username == SSH_USER) and (password == SSH_PASSWORD):
      return paramiko.AUTH_SUCCESSFUL
    return paramiko.AUTH_FAILED

  def get_allowed_auths(self, username):
    return 'password'

  def check_channel_exec_request(self, channel, command):
    logger.debug("Cmd received:%s", command)
    exit_status = 0
    # Let's parse the command and then executes it
    commands = command.split(";")
    # It could be a sequence of commands chained with ';'
    for command in commands:
      exit_status =  exit_status + subprocess.call(command, shell=True)
    # Let's send the sum of the status
    channel.send_exit_status(exit_status)
    # Let's set the event and return true for the happy ending
    self.event.set()
    return True

class TransportRequestHandler(SocketServer.StreamRequestHandler):
  """ Implements transport request handler """

  def handle(self):
    # Let's handle it
    try:
      logger.debug("tcp connection")
      # Get transport and add the host key
      t = paramiko.Transport(self.connection)
      t.add_server_key(self.server.key_handler.host_key)
      # Create a server handler and start it
      server = SSHRequestHandler(self.client_address)
      try:
          t.start_server(server=server)
      except paramiko.SSHException:
          logger.info("SSH negotiation failed")
          return
      # Wait for auth with user and pswd
      while True:
        chan = t.accept(20)
        if chan is None:
            t.close()
            logger.info("SSH connection timeout")
            return
        # Waiting for commands
        server.event.wait(10)
        if not server.event.is_set():
          t.close()
          logger.info("SSH command timeout")
          return
        server.event.clear()
        chan.close()
    except Exception as e:
      traceback.print_exc()
    finally:
      try:
        t.close()
      except:
        pass

# Start netconf server
def start_server():
  # Configure SSH server listener
  global ssh_server
  # Setup SSH
  if ssh_server is not None:
    logger.error("SSH Server is already up and running")
  else:
    ssh_server = SocketServer.ThreadingTCPServer((SSH_IP, SSH_PORT),
      TransportRequestHandler)
    ssh_server.key_handler = SSHKeyHandler()
  # Start the loop for SSH
  logger.info("Listening Server")
  ssh_server.serve_forever()

# Parse options
def parse_options():
  parser = OptionParser()
  parser.add_option("-d", "--debug", action="store_true", help="Activate debug logs")
  # Parse input parameters
  (options, args) = parser.parse_args()
  # Setup properly the logger
  if options.debug:
    logging.basicConfig(level=logging.DEBUG)
  else:
    logging.basicConfig(level=logging.INFO)
  SERVER_DEBUG = logger.getEffectiveLevel() == logging.DEBUG
  logger.info("SERVER_DEBUG:" + str(SERVER_DEBUG))

if __name__ == "__main__":
  parse_options()
  start_server()
