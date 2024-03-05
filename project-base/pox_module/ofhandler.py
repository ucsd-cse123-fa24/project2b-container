# Copyright 2011 James McCauley
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX.  If not, see <http://www.gnu.org/licenses/>.

"""
This is an L2 learning switch written directly against the OpenFlow library.
It is derived from one written live for an SDN crash course.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.util import str_to_bool
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
import pox.lib.packet.icmp as icmp
from pox.lib.packet.arp import arp
from pox.lib.packet.udp import udp
from pox.lib.packet.dns import dns
from pox.lib.addresses import IPAddr, EthAddr


import time
import code
import os
import struct
import sys

log = core.getLogger()
FLOOD_DELAY = 5
IPCONFIG_FILE = './IP_CONFIG'
IP_SETTING={}
RTABLE = {}
ROUTER_IP_DICT = {}
NUM_SW = 4

#Topology is fixed 

class RouterInfo(Event):
  '''Event to raise upon the information about an openflow router is ready'''

  def __init__(self, info, rtable, vhost):
    Event.__init__(self)
    self.info = info
    self.rtable = rtable
    self.vhost = vhost

class OFHandler (EventMixin):
  def __init__ (self, connection, transparent):
    # Switch we'll be adding L2 learning switch capabilities to
    self.connection = connection
    self.transparent = transparent
    self.sw_info = {}
    self.vhost_id = ''
    self.connection.send(of.ofp_set_config(miss_send_len = 65535))
    for port in connection.features.ports:
        intf_name = port.name.split('-')
        if(len(intf_name) < 2):
          continue
        else:
          self.vhost_id = intf_name[0]
          intf_name = intf_name[1]
        if self.vhost_id not in self.sw_info:
          self.sw_info[self.vhost_id] = {}
        self.sw_info[self.vhost_id][intf_name] = (ROUTER_IP_DICT[self.vhost_id][intf_name], port.hw_addr.toStr(), '10Gbps', port.port_no)
        # print(self.sw_info[self.vhost_id][intf_name])
    self.rtable = RTABLE
    # We want to hear Openflow PacketIn messages, so we listen
    self.listenTo(connection)
    self.listenTo(core.cs123_srhandler)
    core.cs123_ofhandler.raiseEvent(RouterInfo(self.sw_info[self.vhost_id], self.rtable[self.vhost_id], self.vhost_id))

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch to implement above algorithm.
    """
    pkt = event.parse()
    vhost = "sw%s" % event.dpid
    raw_packet = pkt.raw
    core.cs123_ofhandler.raiseEvent(SRPacketIn(raw_packet, event.port, vhost))
    # msg = of.ofp_packet_out()
    # msg.buffer_id = event.ofp.buffer_id
    # msg.in_port = event.port
    # self.connection.send(msg)

  def _handle_SRPacketOut(self, event):
    if self.vhost_id != event.vhost:
      return
    # log.debug("SRPacketOut event, port=%d, pkt=%s, vhost=%s" % (event.port, ethernet(raw=event.pkt), event.vhost))
    msg = of.ofp_packet_out()
    new_packet = event.pkt
    msg.actions.append(of.ofp_action_output(port=event.port))
    # msg.buffer_id = -1
    msg.in_port = of.OFPP_NONE
    msg.data = new_packet
    self.connection.send(msg)

class SRPacketIn(Event):
  '''Event to raise upon a receive a packet_in from openflow'''

  def __init__(self, packet, port, vhost):
    Event.__init__(self)
    self.pkt = packet
    self.port = port
    self.vhost = vhost

class cs123_ofhandler (EventMixin):
  """
  Waits for OpenFlow switches to connect and makes them learning switches.
  """
  _eventMixin_events = set([SRPacketIn, RouterInfo])

  def __init__ (self, transparent):
    EventMixin.__init__(self)
    self.listenTo(core.openflow)
    self.transparent = transparent

  def _handle_ConnectionUp (self, event):
    log.debug("Connection %s" % (event.connection,))
    OFHandler(event.connection, self.transparent)

def get_ip_setting():
  if (not os.path.isfile(IPCONFIG_FILE)):
    return -1
  f = open(IPCONFIG_FILE, 'r')
  for line in f:
    if(len(line.split()) == 0):
      break
    name, ip = line.split()
    if ip == "<ELASTIC_IP>":
      log.info("ip configuration is not set, please put your Elastic IP addresses into %s" % IPCONFIG_FILE)
      sys.exit(2)
    #print name, ip
    IP_SETTING[name] = ip

  for i in range(0, NUM_SW):
    sw = 'sw{}'.format(i + 1)
    rtable = 'rtable{}'.format(i + 1)
    RTABLE[sw] = []
    with open(rtable) as f:
      rows = f.read().strip().splitlines()
      for row in rows:
        entry = tuple(row.split())
        RTABLE[sw].append(entry)
      f.close()

  # print(RTABLE)
  
  for node in IP_SETTING:
    ip = IP_SETTING[node]
    if 'sw' not in node:
      continue
    sw = node.split('-')[0]
    iface = node.split('-')[1]
    if sw not in ROUTER_IP_DICT:
      ROUTER_IP_DICT[sw] = {}
    ROUTER_IP_DICT[sw][iface] = ip

  # print(ROUTER_IP_DICT)

  return 0

def launch (transparent=False):
  """
  Starts an Simple Router Topology
  """    
  core.registerNew(cs123_ofhandler, str_to_bool(transparent))
  
  r = get_ip_setting()
  if r == -1:
    log.debug("Couldn't load config file for ip addresses, check whether %s exists" % IPCONFIG_FILE)
    sys.exit(2)
  else:
    log.debug('*** ofhandler: Successfully loaded ip settings for hosts\n %s\n' % IP_SETTING)
