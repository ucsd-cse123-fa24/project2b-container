#!/usr/bin/python2

"""
Start up a Simple topology for CS144
"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.util import quietRun
from mininet.moduledeps import pathCheck

from sys import exit
import os.path
from subprocess import Popen, STDOUT, PIPE

IPBASE = '192.168.0.0/16'
IPCONFIG_FILE = './IP_CONFIG'
IP_SETTING={}

class CS144Topo( Topo ):
    "CS 144 Lab 4 Topology"
    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        self.num_routers = 4
        self.clients = []
        self.routers = []
        self.clients.append(self.addHost('client'))
        self.clients.append(self.addHost('server1'))
        self.clients.append(self.addHost('server2'))
        for i in range(0, self.num_routers):
            self.routers.append(self.addSwitch('sw{}'.format(i + 1)))
        self.addLink(self.clients[0], self.routers[1])
        self.addLink(self.clients[1], self.routers[2])
        self.addLink(self.clients[2], self.routers[3])
        self.addLink(self.routers[1], self.routers[0])
        self.addLink(self.routers[2], self.routers[0])
        self.addLink(self.routers[3], self.routers[0])

class CS144Controller( Controller ):
    "Controller for CS144 PA4"

    def __init__( self, name, inNamespace=False, command='controller',
                 cargs='-v ptcp:%d', cdir=None, ip="127.0.0.1",
                 port=6633, **params ):
        """command: controller command name
           cargs: controller command arguments
           cdir: director to cd to before running controller
           ip: IP address for controller
           port: port for controller to listen at
           params: other params passed to Node.__init__()"""
        Controller.__init__( self, name, ip=ip, port=port, **params)

    def start( self ):
        """Start <controller> <args> on controller.
            Log to /tmp/cN.log"""
        pathCheck( self.command )
        cout = '/tmp/' + self.name + '.log'
        if self.cdir is not None:
            self.cmd( 'cd ' + self.cdir )
        self.cmd( self.command, self.cargs % self.port, '>&', cout, '&' )

    def stop( self ):
        "Stop controller."
        self.cmd( 'kill %' + self.command )
        self.terminate()


def startsshd( host ):
    "Start sshd on host"
    stopsshd()
    info( '*** Starting sshd\n' )
    name, intf, ip = host.name, host.defaultIntf(), host.IP()
    banner = '/tmp/%s.banner' % name
    host.cmd( 'echo "Welcome to %s at %s" >  %s' % ( name, ip, banner ) )
    host.cmd( '/usr/sbin/sshd -o "Banner %s"' % banner, '-o "UseDNS no"' )
    info( '***', host.name, 'is running sshd on', intf, 'at', ip, '\n' )


def stopsshd():
    "Stop *all* sshd processes with a custom banner"
    info( '*** Shutting down stale sshd/Banner processes ',
          quietRun( "pkill -9 -f Banner" ), '\n' )


def starthttp( host ):
    "Start simple Python web server on hosts"
    info( '*** Starting SimpleHTTPServer on host', host, '\n' )
    host.cmd( 'cd ./http_%s/; nohup python2.7 ./webserver.py &' % (host.name) )


def stophttp():
    "Stop simple Python web servers"
    info( '*** Shutting down stale SimpleHTTPServers', 
          quietRun( "pkill -9 -f SimpleHTTPServer" ), '\n' )    
    info( '*** Shutting down stale webservers', 
          quietRun( "pkill -9 -f webserver.py" ), '\n' )    
    
def set_default_route(host):
    info('*** setting default gateway of host %s\n' % host.name)
    if(host.name == 'server1'):
        routerip = IP_SETTING['sw3-eth1']
    elif(host.name == 'server2'):
        routerip = IP_SETTING['sw4-eth1']
    elif(host.name == 'client'):
        routerip = IP_SETTING['sw2-eth1']
    print(host.name, routerip)
    host.cmd('route add %s/32 dev %s-eth0' % (routerip, host.name))
    host.cmd('route add default gw %s dev %s-eth0' % (routerip, host.name))
    if host.name == 'client':
        host.cmd('route del -net 192.168.1.0/24 dev %s-eth0' % (host.name))
    elif host.name == 'server1':
        host.cmd('route del -net 192.168.2.0/28 dev %s-eth0' % (host.name))
    elif host.name == 'server2':
        host.cmd('route del -net 192.168.3.0/28 dev %s-eth0' % (host.name))

def get_ip_setting():
    try:
        with open(IPCONFIG_FILE, 'r') as f:
            for line in f:
                if( len(line.split()) == 0):
                  break
                name, ip = line.split()
                print(name, ip)
                IP_SETTING[name] = ip
            info( '*** Successfully loaded ip settings for hosts\n %s\n' % IP_SETTING)
    except EnvironmentError:
        exit("Couldn't load config file for ip addresses, check whether %s exists" % IPCONFIG_FILE)

def cs144net():
    stophttp()
    "Create a simple network for cs144"
    get_ip_setting()
    topo = CS144Topo()
    info( '*** Creating network\n' )
    net = Mininet( topo=topo, controller=RemoteController, ipBase=IPBASE )
    net.start()
    server1, server2, client = net.get( 'server1', 'server2', 'client')
    s1intf = server1.defaultIntf()
    s1intf.setIP('%s/28' % IP_SETTING['server1'])
    s2intf = server2.defaultIntf()
    s2intf.setIP('%s/28' % IP_SETTING['server2'])
    clintf = client.defaultIntf()
    clintf.setIP('%s/24' % IP_SETTING['client'])
    for host in server1, server2, client:
        set_default_route(host)
    starthttp( server1 )
    starthttp( server2 )
    CLI( net )
    stophttp()
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    cs144net()
