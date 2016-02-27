---
layout: post
title:  "Simple way to secure Freeswitch with iptables"
date:   2016-02-27 16:28:00 +0200
categories: jekyll update
comments: true
---
Today we will discuss how to secure your Freeswitch(or it can be any other PBX) with iptables. This is very simple, but nevertheless is very effective way to protect your PBX. 
We are assuming that you do not need to access your PBX from whole internet. In most cases you just need to access your PBX from your office 
where most phones should be located and I assume that your office network have static IP, in our case let it be 1.2.3.4.

Think twice before allowing everybody to be able to reach your PBX.

I'm assuming that you already installed Freeswitch, as it was described in my previous manual.
I'm assuming that you are running Debian 8 and you will plan to use Flowroute
(You can use any provider, in this manual I will use Flowroute ip-addresses as example) for calling in and out.

![Diagram]({{ site.url }}/assets/freeswitch.png)

On this point we need to generate iptables rules, as you see from diagram above, we need to allow connection to our server from 3 ip-addresses. 
Below is simple iptables rules, for our case:
{% highlight bash linenos=table %}
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [45:7685]
-A INPUT -p udp -m multiport --dports 16384:32768 -j ACCEPT -m comment --comment "RTP media ports"
-A INPUT -s 216.115.69.144/32 -p udp --dport 5060 -j ACCEPT -m comment --comment "Flowroute 1st ip"
-A INPUT -s 70.167.153.130/32 -p udp --dport 5060 -j ACCEPT -m comment --comment "Flowroute 2nd ip"
-A INPUT -s 1.2.3.4/32 -j ACCEPT -m comment --comment "Office"
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
-A INPUT -p icmp -j ACCEPT
-A INPUT -i lo -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 22 -j ACCEPT
-A INPUT -j REJECT --reject-with icmp-host-prohibited
-A FORWARD -j REJECT --reject-with icmp-host-prohibited
COMMIT
{% endhighlight %}

1) Check rules above, line 8, change 1.2.3.4 to your office network ip.

2) In rules above I'm assuming that Freeswitch is using default RTP ports 16384-32768. You can check what ports is used in 
`/usr/local/freeswitch/conf/autoload_configs/switch.conf.xml` if no ports are set, then it is default ports, what we are using in above rules. 
If you are using other PBX, then check manual and change port range accordingly(For Asterisk default ports are 10000-20000).

3) If you are using different then Flowroute provider, update lines 6 & 7 accordingly.

4) On this point when our rules are ready, please save rules to `/etc/iptables.up.rules`

5) Run following command to load them:
{% highlight bash %}
iptables-restore < /etc/iptables.up.rules
{% endhighlight %}

6) Check that all rules are loaded by running following command:
{% highlight bash %}
iptables -L -n -v
{% endhighlight %}

You should see something similar to:

{% highlight bash %}
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination
    0     0 ACCEPT     udp  --  *      *       0.0.0.0/0            0.0.0.0/0            multiport dports 16384:32768 /* RTP media ports */
    0     0 ACCEPT     udp  --  *      *       216.115.69.144       0.0.0.0/0            udp dpt:5060 /* Flowroute 1st ip */
    0     0 ACCEPT     udp  --  *      *       70.167.153.130       0.0.0.0/0            udp dpt:5060 /* Flowroute 2nd ip */
   30  2160 ACCEPT     all  --  *      *       1.2.3.4              0.0.0.0/0            /* Office */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED
    0     0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0
    0     0 ACCEPT     all  --  lo     *       0.0.0.0/0            0.0.0.0/0
    0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            state NEW tcp dpt:22
    0     0 REJECT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            reject-with icmp-host-prohibited

Chain FORWARD (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination
    0     0 REJECT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            reject-with icmp-host-prohibited

Chain OUTPUT (policy ACCEPT 17 packets, 1784 bytes)
 pkts bytes target     prot opt in     out     source               destination
{% endhighlight %}

7) Now we need to make sure that our rules are loaded after server reboot. Create file `/etc/network/if-pre-up.d/iptables` with following content:
{% highlight bash %}
#!/bin/sh
/sbin/iptables-restore < /etc/iptables.up.rules
{% endhighlight %}

8) Make this file executable:
{% highlight bash %}
chmod +x /etc/network/if-pre-up.d/iptables
{% endhighlight %}

9) On this point you should be ready with your iptables set-up.
