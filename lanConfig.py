from __future__ import print_function
from re import sub

from subprocess import PIPE
from mininet.net import Mininet
from mininet.node import Controller, Host
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time
import random
import subprocess


def experiment(outfile, topo, pcs, N, pingings, ping_rpts, net, is_random):
    print('   --', topo, N, pingings, ping_rpts, is_random)
    all_ok = True

    while all_ok:
        pings = []
        outdatas = []
        
        if is_random:
            targets = [random.randint(2, N+1) for _ in range(pingings)]
        else:
            targets = [ i + 1 if i <= N else 2 for i in range(2, 2+pingings)]
        
        for i in range(2, 2+pingings):
            target = targets[i - 2]
            pcs[i-2].cmd('ping 10.10.{}.{} -c 1 -W 20'.format(target, target))

        for i in range(2, 2+pingings):
            target = targets[i - 2]
            # print(i, 'pings', target)
            pings.append(pcs[i-2].popen(
                ['ping', '10.10.{}.{}'.format(target, target),
                    '-c', str(ping_rpts), '-i', '0.1', '-W', '20'],
                stdout=PIPE
            ))

        all_ok = False

        for pingproc in pings:
            outdata, errdata = pingproc.communicate()
            outdatas.append(outdata)
            if len(outdata.split('\n')[-2].split('/')) <= 4:
                print(outdata)
                all_ok = True

    for od in outdatas:
        ll, _, mdev = od.split('\n')[-2].split('/')[4:7]
        mdev = mdev.split(' ')[0]
        print('{},{},{},{},{},{},{}'.format(topo, N, pingings, ping_rpts, is_random, ll, mdev), file=outfile)

def ring_topo(outfile, N):
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
        # experiment(None, 'bus', pcs, N, N-1, 1, net, False)
        for pingings in [1, N-1]:
            for ping_rpts in [100]:
                for is_random in [True, False]:
                    experiment(outfile, 'bus', pcs, N, pingings, ping_rpts, net, is_random)
    except KeyboardInterrupt:
        pass
    
    # CLI(net)

    net.stop()

def star_topo(outfile, N):
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
        # experiment(None, 'star', pcs, N, N, 1, net, False)
        for pingings in [1, N]:
            for ping_rpts in [100]:
                for is_random in [True, False]:
                    experiment(outfile, 'star', pcs, N, pingings, ping_rpts, net, is_random)
    except KeyboardInterrupt:
        pass

    net.stop()


def main():
    TOPO = star_topo

    with open('./output_3.csv', 'a') as f:
        for TOPO in [star_topo]:
            for N in [200, 500, 1000]:
                print(' **', N, TOPO.__name__)
                TOPO(f, N)


main()
# ring_topo(None, 2, 2, 2)
