from __future__ import print_function
from re import sub

from subprocess import PIPE
from mininet.net import Mininet
from mininet.node import Controller, Host
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time

import subprocess


def experiment(outfile, pcs, N, pingings, ping_rpts, net):
    pings = []

    for i in range(2, 2+pingings):
        target = i + 1 if i <= N else 2
        # print(i, 'pings', target)
        pings.append(pcs[i-2].popen(
            ['ping', '10.10.{}.{}'.format(
                target, target), '-c', str(ping_rpts), '-i', '0.2'],
            stdout=PIPE
        ))

    outdatas = []

    for pingproc in pings:
        outdata, errdata = pingproc.communicate()
        outdatas.append(outdata)

    for od in outdatas:
        try:
            ll = float(od.split('\n')[-2].split('/')[4])
            print('{},{},{},{}'.format(N, pingings, ping_rpts, ll), file=outfile)
        except:
            print(od)
            CLI(net)
            raise

def ring_topo(outfile, N, pingings, ping_rpts):
    net = Mininet()
    net.addController('c0')

    pcs = [None] * N
    switches = [None] * N

    for i in range(2, N+2):
        pcs[i-2] = net.addHost('pc{}'.format(i),
                               ip='10.10.{}.{}/16'.format(i, i))
        switches[i-2] = net.addSwitch('s{}'.format(i))
    
    for i in range(2, N+2):
        net.addLink(pcs[i-2], switches[i-2])
        if i > 2:
            net.addLink(switches[i-3], switches[i-2])

    net.start()
    
    # for i in range(1, N+1):
    #     subprocess.call(['brctl', 'stp', 's{}'.format(i), 'on'])
    
    time.sleep(1)

    try:
        experiment(outfile, pcs, N, pingings, ping_rpts, net)
    except KeyboardInterrupt:
        pass
    
    # CLI(net)

    net.stop()

def star_topo(outfile, N, pingings, ping_rpts):
    net = Mininet()
    net.addController('c0')

    router = net.addHost('router', ip='10.10.2.1/24')

    pcs = [None] * N
    switches = [None] * N

    for i in range(2, N+2):
        pcs[i-2] = net.addHost('pc{}'.format(i),
                               ip='10.10.{}.{}/24'.format(i, i))
        switches[i-2] = net.addSwitch('s{}'.format(i))

        net.addLink(pcs[i-2], switches[i-2])
        net.addLink(router, switches[i-2])

        if i > 2:
            router.cmd(
                'ip addr add 10.10.{}.1/24 dev router-eth{}'.format(i, i-2))

    router.cmd('echo 1 > /proc/sys/net/ipv4/ip_forward')
    net.start()

    for i in range(2, N+2):
        pcs[i-2].cmd('ip route add default via 10.10.{}.1'.format(i))

    try:
        experiment(outfile, pcs, N, pingings, ping_rpts)
    except KeyboardInterrupt:
        pass

    net.stop()


def main():
    TOPO = ring_topo

    with open('./ring.csv', 'a') as f:
        for N in [2, 5, 10, 50, 100]:
            for pingings in [1, N]:
                for ping_rpts in [10, 100]:
                    print(N, pingings, ping_rpts)
                    TOPO(f, N, pingings, ping_rpts)


main()
# ring_topo(None, 2, 2, 2)
