#!/usr/bin/python

from netconf.client import NetconfSSHSession


try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree

# Let's create a NetConf session
session = NetconfSSHSession("127.0.0.1", 830, "srv6", "srv6")

# From the hello, we got the capabilities
for capability in session.capabilities:
  print capability

config = """
<edit-config>
<target>
  <running/>
</target>
<default-operation>none</default-operation>
<test-option>test-then-set</test-option>
<error-option>rollback-on-error</error-option>
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <srv6-explicit-path operation="create" xmlns="urn:ietf:params:xml:ns:yang:srv6-explicit-path">
      <path>
          <destination>1111:4::2/128</destination>
          <sr-path>
              <srv6-segment>1111:3::2</srv6-segment>
          </sr-path>
          <encapmode>inline</encapmode>
          <device>eth0</device>
      </path>
    </srv6-explicit-path>
</config>
</edit-config>
"""

# Single add
result = session.send_rpc(config)
print format(etree.tostring(result[0], pretty_print=True))

config = """
<edit-config>
<target>
  <running/>
</target>
<default-operation>none</default-operation>
<test-option>test-then-set</test-option>
<error-option>rollback-on-error</error-option>
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <srv6-explicit-path operation="create" xmlns="urn:ietf:params:xml:ns:yang:srv6-explicit-path">
      <path>
          <destination>2222:4::2/128</destination>
          <sr-path>
              <srv6-segment>2222:3::2</srv6-segment>
          </sr-path>
          <encapmode>inline</encapmode>
          <device>eth0</device>
      </path>
      <path>
          <destination>3333:4::2/128</destination>
          <sr-path>
              <srv6-segment>3333:3::2</srv6-segment>
              <srv6-segment>3333:2::2</srv6-segment>
              <srv6-segment>3333:1::2</srv6-segment>
          </sr-path>
          <encapmode>encap</encapmode>
          <device>eth0</device>
      </path>
    </srv6-explicit-path>
</config>
</edit-config>
"""

# Bulk add
result = session.send_rpc(config)
print format(etree.tostring(result[0], pretty_print=True))