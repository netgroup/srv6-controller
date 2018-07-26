#!/usr/bin/python

import requests
import json

# Global variables

# Base path for the url
SRV6_BASE_PATH = "srv6-explicit-path"
# HTTP definitions
ACCEPT = "application/json"
CONTENT_TYPE = "application/json"
POST = "POST"
# Define wheter to use HTTP or HTTPS
SECURE = False
# SSL cerificate for server validation
CERTIFICATE = 'cert_client.pem'

# Build an http requests object
def get_http_requests(ip_address, port, secure, params, data):
  # Create a request, build the url and headers
  url = '{scheme}://{ip}:{port}/{basePath}'.format(scheme=('https' if secure else 'http'),
                                                  ip=ip_address, port=port, basePath=SRV6_BASE_PATH)
  headers = {'Accept': ACCEPT, 'Content-Type': CONTENT_TYPE}
  request = requests.Request(POST, url, data=data, headers=headers, params=params)
  return request.prepare()

# Let's create a http session
session = requests.Session()
# Define body content and query params
data = """
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
}
"""
params = {"operation": "create"}
# Create a POST request with the given data
request = get_http_requests("localhost", 443 if SECURE else 8080, SECURE, params, data)
# Single add
response = session.send(request, verify=(CERTIFICATE if SECURE else None))
print response.status_code

data = """
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
params = {"operation": "create"}
request = get_http_requests("localhost", 443 if SECURE else 8080, SECURE, params, data)
# Bulk add
response = session.send(request, verify=(CERTIFICATE if SECURE else None))
print response.status_code
# Let's close the session
session.close()
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
  session = requests.Session()
  params = {"operation": "remove"}
  # Paths is our common data-model
  request = get_http_requests("localhost", 443 if SECURE else 8080, SECURE, params, json.dumps(data))
  response = session.send(request, verify=(CERTIFICATE if SECURE else None))
  print response.status_code
  session.close()