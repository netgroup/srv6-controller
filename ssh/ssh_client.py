#!/usr/bin/python

import sshutil

from sshutil.cmd import SSHCommand

# Utility to close a ssh session
def close_ssh_session(session):
  # Close the session
  remoteCmd.close()
  # Flush the cache
  remoteCmd.cache.flush()

# Let's create a new route
cmd = "ip -6 route add 1111:4::2/128 encap seg6 mode inline segs 1111:3::2 dev eth0"
remoteCmd = SSHCommand(cmd, "127.0.0.1", 220, "srv6", "srv6")
remoteCmd.run()

# Let's create a bunch of routes
cmd = "ip -6 route add 2222:4::2/128 encap seg6 mode inline segs 2222:3::2 dev eth0; \
ip -6 route add 3333:4::2/128 encap seg6 mode encap segs 3333:3::2,3333:2::2,3333:3::1 dev eth0"
remoteCmd = SSHCommand(cmd, "127.0.0.1", 220, "srv6", "srv6")
remoteCmd.run()
# Close the session
close_ssh_session(remoteCmd)
# Now delete all the routes created before
cmds = ["ip -6 route del 1111:4::2/128 dev eth0", "ip -6 route del 2222:4::2/128 dev eth0",
"ip -6 route del 3333:4::2/128 dev eth0"]
# Iterate over the commands
for cmd in cmds:
  # Each time creating a new session
  remoteCmd = SSHCommand(cmd, "127.0.0.1", 220, "srv6", "srv6")
  remoteCmd.run()
  close_ssh_session(remoteCmd)
