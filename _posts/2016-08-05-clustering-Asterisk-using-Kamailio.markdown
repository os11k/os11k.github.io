---
layout: post
title:  "Clustering Asterisk using Kamailio"
date:   2016-08-05 7:10:00 +0200
categories: jekyll update
comments: true
---

1) In this article I would like to explain how we can create multi-server Asterisk set-up with Kamailio help. Before we can proceed you will need to 
set-up 2 separate Asterisk servers - asterisk1 & asterisk2, server running MySQL DB, you need to configure SIP Realtime on both Asterisk servers so 
it will use same MySQL DB(please use separate sipregs table for each server, in my set-up I named them sipregs_asterisk1 & sipregs_asterisk2) 
and you will need to install Kamailio with default configuration. Additionally we will use func_odbc on Asterisk, but it should be already compiled, 
if you set up your Asterisk with SIP realtime using ODBC.

![Diagram]({{ site.url }}/assets/asterisk.png)

2) For Asterisk SIP realtime I recommend following 
<a href="http://kb.asipto.com/asterisk:realtime:kamailio-4.0.x-asterisk-11.3.0-astdb">
manual
</a>
, I skipped voicemail* tables. Use your common sense and follow only asterisk related steps.

3) First what we need to create view `sipregs_all` what will have data from our both sipregs tables: `sipregs_asterisk1` & `sipregs_asterisk2`. 
It is not recommended to share `sipregs` table between servers, each server should have it own table.
{% highlight mysql %}
CREATE VIEW sipregs_all AS select * from sipregs_asterisk1 union select * from sipregs_asterisk2;
{% endhighlight %}

4) Make sure that in `sip.conf` you have following options switched on:
{% highlight bash %}
rtcachefriends=yes
rtsavesysname=yes           
{% endhighlight %}

5) Now we need to decide how we will name our Asterisk boxes. I named them `asterisk1` & `asterisk2`.

6) Now we need to set-up systemname, use names from previous point. You can change systemname in `asterisk.conf` like this:
{% highlight bash %}
systemname = asterisk1
{% endhighlight %}

7) Now we can set-up trunks on both Asterisk servers. In `sip.conf` of asterisk1 I have following entry, you need same entry on asterisk2, 
just change ip-address and trunk name accordingly.
{% highlight bash %}
[asterisk2]
type=peer
insecure=very
nat=yes
canreinvite=no
host=asterisk2_ip_address
context=testing
{% endhighlight %}

8) This is my dialplan, please put it on both servers. Following 
dialplan check with `func_odbc` where currently called extension registered and if it is not on same server as caller then it sends call to 
trunk with name from field `regserver`, what should be systemname. If we do not find extension we just hangup a call, off cause we can hangup
with specific error like "404 Not Found", but this is homework for you. ;)
{% highlight bash %}
[testing]
exten => _XXX,1,NoOp(SYSTEMNAME: ${SYSTEMNAME})
exten => _XXX,n,Set(server=${ODBC_checkregserver(${EXTEN})})
exten => _XXX,n,NoOp(SERVER: ${server})
exten => _XXX,n,GotoIf($["${server}" = ""]?hangup)
exten => _XXX,n,ExecIf($["${server}" = "${SYSTEMNAME}"]?Dial(SIP/${EXTEN}):Dial(SIP/${EXTEN}@${server}))
exten => _XXX,n(hangup),Hangup()
{% endhighlight %}

9) Additionally you need to configure odbc function in `func_odbc.conf`. It checks on what server currently user is 
located and sort result based on `regseconds` field, cause there might be several entries, if extension didn't unregistered 
properly from one server and then registered on other one.
{% highlight bash %}
[checkregserver]
dsn=asterisk
readsql=SELECT regserver FROM sipregs_all WHERE fullcontact like 'sip:${ARG1}%' order by regseconds DESC limit 1
{% endhighlight %}

10) Now you need to add users to `sipusers` table:
{% highlight mysql %}
INSERT INTO sipusers (name, defaultuser, host, type, context, nat, sippasswd) VALUES ('101', '101', 'dynamic', 'friend', 'testing', 'yes', 'mysecurepass');
INSERT INTO sipusers (name, defaultuser, host, type, context, nat, sippasswd) VALUES ('102', '102', 'dynamic', 'friend', 'testing', 'yes', 'mysecurepass');
{% endhighlight %}

11) Please add users to `sipregs_asterisk1` & `sipregs_asterisk2` tables.
{% highlight mysql %}
INSERT INTO sipregs_asterisk1(name) VALUES('101');
INSERT INTO sipregs_asterisk1(name) VALUES('102');
INSERT INTO sipregs_asterisk2(name) VALUES('101');
INSERT INTO sipregs_asterisk2(name) VALUES('102');
{% endhighlight %}

12) On this point you should be ready with Asterisk part. To test it - register with 2 SIP clients with each on separate Asterisk server and you should be able to 
call one extension from other.

13) Now you need to install Kamailio. It is very easy to do I think even simpler then Asterisk. I recommend following 
<a href="https://www.kamailio.org/wiki/install/4.4.x/git">
manual
</a>.

14) This is my Kamailio 
<a href="https://github.com/os11k/dispatcher/blob/master/kamailio.cfg_asterisk">
config
</a>.

15) This is my content of `/usr/local/etc/kamailio/dispatcher.list`
{% highlight bash %}
1 sip:asterisk1_ip_address:5060
1 sip:asterisk2_ip_address:5060
{% endhighlight %}

16) Now you should be able to register on Kamailio ip-address and calls should work even if 2 extensions are registered on separate servers. 
When one servers dies, extension will be able to make call through second server, but it will not be able to receive call until it re-registers, 
so I recommend to put 60 seconds re-registration timeout on all extensions.

17) This is very simple and easy cluster set-up of Asterisk, off cause there are dozens other options, what include register server on 
Kamailio side, using DUNDi and etc. You can even skip Kamailio and use DNS based fail-over, just make sure that your SIP clients support DNS SRV records.

18) In following set-up single point of failure is Asterisk and MySQL DB. For MySQL you can use some-kind cluster(Galera, Percona), there is dozens manuals 
online. For Kamailio you can have some-kind fail-over set-up too. I hope this article was help-full and I really do not intended to answer all 
question, but I just wanted to provide simple manual for cluster set-up from where you can start to build up your set-up.
