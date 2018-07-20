#!/usr/bin/python
import sshutil
from sshutil.cmd import SSHCommand
import logging

# Let's create a new route
cmd = "ip -6 route add 1111:4::2/128 encap seg6 mode encap segs 1111:3::2 dev eth0"
remoteCmd = SSHCommand(cmd, "127.0.0.1", 220, "srv6", "srv6")
remoteCmd.run()

# Let's create a bunch of routes
cmd = "ip -6 route add 2222:4::2/128 encap seg6 mode encap segs 2222:3::2 dev eth0; \
ip -6 route add 3333:4::2/128 encap seg6 mode encap segs 3333:3::2,3333:2::2,3333:3::1 dev eth0"
remoteCmd = SSHCommand(cmd, "127.0.0.1", 220, "srv6", "srv6")
remoteCmd.run()