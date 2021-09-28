---
layout: post
title:  "How to Stop DDoS attacks in VoIP/SIP using Kamailio"
date:   2021-09-21 18:55:00 +0200
categories: jekyll update
comments: true
---

Kamailio is SIP proxy what can handle 5000+ call setup per seconds and much more. Kamailio is great tool not only as SIP proxy, but in this example I will try to explain how to use it to secure your VoIP network against DDOS attacks.

If you face DDOS attack on your SIP/VoIP infrastructure, then it is good to understand what is a bottleneck. Is it your VoIP application or MySQL DB is overloaded due many requests, or some other 3rd party service is blocking VoIP system(like billing for example)? In some cases it can be network(too much packets arriving on server network card or router or maybe even your internet connection is not enough for all of that load), in this case Kamailio might not help, but there are solutions for that problem too, but probably we can discuss this next time.

In this scenario we will look into a case when there are bottleneck in your VoIP services. In this case we can put Kamailio as Proxy in front of your SIP/VoIP services and it should be easy as it gets, as far as your SIP/VoIP application supports SIP Path Extension. I have sample config for Kamailio as load-balancer using path - 
<a href="https://github.com/os11k/dispatcher">
here
</a>

So to fight DDOS we will use 
<a href="https://www.kamailio.org/docs/modules/devel/modules/pike.html">
pike 
</a>
& 
<a href="https://kamailio.org/docs/modules/devel/modules/htable.html">
htable
</a>
 modules.

Default Kamailio config 
<a href="https://github.com/kamailio/kamailio/blob/master/etc/kamailio.cfg">
file
</a>
 has everything what we need, you just need to put in config file somewhere after others "defines"(just search for `#!define`):

`#!define WITH_ANTIFLOOD`

It is worth to look into what those parts of code actually do.

First part of relevant code:
{% highlight bash %}
loadmodule "htable.so"
loadmodule "pike.so"
{% endhighlight %}
Here we are loading necessary libraries, pike for actual blocking and htable for hash table support. Kamailio will use hash tables (`$sht`) for saving IP with flag 1 if it is should be blocked.

{% highlight bash %}
# - - - pike params - - -
modparam("pike", "sampling_time_unit", 2)
modparam("pike", "reqs_density_per_unit", 16)
modparam("pike", "remove_latency", 4)
# - - - htable params - - -
/* ip ban htable with autoexpire after 5 minutes */
modparam("htable", "htable", "ipban=>size=8;autoexpire=300;")
#!endif
{% endhighlight %}
In this block first 3 lines tells how big time-period is(2 seconds) and how much requests are allowed during that period - 16. In reality it might be a bit more, but lets stick with this explanation, to make it easier to understand. 4th line is kind of technical settings, it basically tells how long to have IP in memory.

So htable parameters is self explanatory, what means that in 5 minutes block will be removed, so if we have blocked 1 IP then after 5 minutes Kamailio will start to process traffic again from that IP.

Last part of the code:

{% highlight bash %}
# flood detection from same IP and traffic ban for a while
# be sure you exclude checking trusted peers, such as pstn gateways
# - local host excluded (e.g., loop to self)
if(src_ip!=myself) {
	if($sht(ipban=>$si)!=$null) {
		# ip is already blocked
		xdbg("request from blocked IP - $rm from $fu (IP:$si:$sp)\n");
		exit;
	}
	if (!pike_check_req()) {
		xlog("L_ALERT","ALERT: pike blocking $rm from $fu (IP:$si:$sp)\n");
		$sht(ipban=>$si) = 1;
		exit;
	}
}
{% endhighlight %}

In first four lines of this block we make sure to not block our-self, 5–9 lines check if IP is already blocked and if it is, then we just stop processing this SIP request, so attacker will get no response. Last part of code is checking if there are an attack ongoing and if it is, we write to hash table, so next time code will not even reach this part but will exit on first 9 lines of code. After writing to hash table Kamailio stops processing and attacker gets no response.

As you can see this is not something very difficult to implement using Kamailio, so I hope this will be useful.
