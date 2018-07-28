#!/usr/bin/python

import grpc
import json

import srv6_explicit_path_pb2_grpc
import srv6_explicit_path_pb2

# Define wheter to use SSL or not
SECURE = False
# SSL cerificate for server validation
CERTIFICATE = 'cert_client.pem'

# Build a grpc stub
def get_grpc_session(ip_address, port, secure):
  # If secure we need to establish a channel with the secure endpoint
  if secure:
    # Open the certificate file
    with open(CERTIFICATE) as f:
      certificate = f.read()
    # Then create the SSL credentials and establish the channel
    grpc_client_credentials = grpc.ssl_channel_credentials(certificate)
    channel = grpc.secure_channel("%s:%s" %(ip_address, port), grpc_client_credentials)
  else:
    channel = grpc.insecure_channel("%s:%s" %(ip_address, port))
  return srv6_explicit_path_pb2_grpc.SRv6ExplicitPathStub(channel), channel

# Get the reference of the stub
srv6_stub,channel = get_grpc_session("localhost", 12345, SECURE)
# Create message request
path_request = srv6_explicit_path_pb2.SRv6EPRequest()
# Create a new path
path = path_request.path.add()
# Set destination, device, encapmode
path.destination = "1111:4::2/128"
path.device = "eth0"
path.encapmode = "inline"
# Create a new segment
srv6_segment = path.sr_path.add()
srv6_segment.segment = "1111:3::2"
# Single add
response = srv6_stub.Create(path_request)
print response

path_request = srv6_explicit_path_pb2.SRv6EPRequest()
path = path_request.path.add()
path.destination = "2222:4::2/128"
path.device = "eth0"
path.encapmode = "inline"
srv6_segment = path.sr_path.add()
srv6_segment.segment = "2222:3::2"
path = path_request.path.add()
path.destination = "3333:4::2/128"
path.device = "eth0"
path.encapmode = "encap"
srv6_segment = path.sr_path.add()
srv6_segment.segment = "3333:3::2"
srv6_segment = path.sr_path.add()
srv6_segment.segment = "3333:2::2"
srv6_segment = path.sr_path.add()
srv6_segment.segment = "3333:1::2"
# Bulk add
response = srv6_stub.Create(path_request)
print response
# Let's close the session
channel.close()

# Delete all the routes created before
data = """
[
  {
    "paths": [
      {
        "device": "eth0",
        "destination": "1111:4::2/128",
        "encapmode": "inline",
        "segments": [
          "1111:3::2"
        ]
      }
    ]
  },
  {
    "paths": [
      {
        "device": "eth0",
        "destination": "2222:4::2/128",
        "encapmode": "inline",
        "segments": [
          "2222:3::2"
        ]
      }
    ]
  },
  {
    "paths": [
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
]
"""
json_data = json.loads(data)
# Iterate over the array and delete one by one all the paths
for data in json_data:
  # Each time we create a new session
  srv6_stub,channel = get_grpc_session("localhost", 12345, SECURE)
  path_request = srv6_explicit_path_pb2.SRv6EPRequest()
  for jpath in data['paths']:
    path = path_request.path.add()
    path.destination = jpath['destination']
    path.device = jpath['device']
    path.encapmode = jpath['encapmode']
    for segment in jpath['segments']:
      srv6_segment = path.sr_path.add()
      srv6_segment.segment = segment
    response = srv6_stub.Remove(path_request)
    print response
    channel.close()
