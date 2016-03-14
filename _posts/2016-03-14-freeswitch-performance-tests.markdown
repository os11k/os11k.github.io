---
layout: post
title:  "Running performance test on Freeswitch using SIPp"
date:   2016-03-14 07:10:00 +0200
categories: jekyll update
comments: true
---
In this post I will try to provide step-by-step instruction for running performance tests using SIPp against Freeswitch.
At the beginning I will explain how to compile SIPp for Debian 8 and at the end we will play with couple scenarios.

1) We will need to install dependencies:
{% highlight bash %}
apt-get update && apt-get install -y git build-essential autoconf ncurses-dev libpcap-dev
{% endhighlight %}

2) Getting source from git:
{% highlight bash %}
cd /usr/src/
git clone https://github.com/SIPp/sipp.git
{% endhighlight %}

3) Now we need to compile SIPp. Option `--with-pcap` will gave us possibility to send media:
{% highlight bash %}
cd ./sipp/
./build.sh --with-pcap
{% endhighlight %}

4) Now you should be ready with your SIPp, you can check it by running following command
{% highlight bash %}
./sipp -v
{% endhighlight %}
You should get output similar to what you can see below:
{% highlight bash %}
 SIPp v3.5.1-rc1-7-g44619c6-PCAP-RTPSTREAM built Mar  6 2016, 04:48:10.

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU General Public License as
 published by the Free Software Foundation; either version 2 of
 the License, or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public
 License along with this program; if not, write to the
 Free Software Foundation, Inc.,
 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA

 Author: see source files.
{% endhighlight %}

5) Now we are ready with SIPp. I prepared 2 scenarios, for registration and for calling. You can get them both from here: https://github.com/os11k/sipp2freeswitch
{% highlight bash %}
cd /usr/src
git clone https://github.com/os11k/sipp2freeswitch.git
{% endhighlight %}

6) My prepared scenarios have 2 parts: xml script and csv file, which should have list of accounts what we should use. If you open `/usr/src/sipp2freeswitch/register-accounts.csv` you will see that first line is 
`SEQUENTIAL` which means in what order we should try accounts, possible options are:  RANDOM, SEQUENTIAL, and USER. We will stick with `SEQUENTIAL`. 2-4 lines are comments. 
Lines 5-14 will have information about each account what we can use, in our case we will use 1000-1009 extensions and password 1234
(this is default extensions and password for Freeswitch, you should never use it in production). You should change 10.0.0.10 with your Freeswitch server IP and change extensions and passwords to yours.
File `/usr/src/sipp2freeswitch/invite-accounts.csv` will have completely same content, but lines 5-14 will have `;9196;` at the end what will be destination number where SIPp will call, 
in default Freeswitch installation 9196 is echo test.
{% highlight bash linenos=table %}
SEQUENTIAL
# Username: 1000-1009
# Password: 1234
# SIP Proxy: 10.0.0.10
1000;10.0.0.10;[authentication username=1000 password=1234]
1001;10.0.0.10;[authentication username=1001 password=1234]
1002;10.0.0.10;[authentication username=1002 password=1234]
1003;10.0.0.10;[authentication username=1003 password=1234]
1004;10.0.0.10;[authentication username=1004 password=1234]
1005;10.0.0.10;[authentication username=1005 password=1234]
1006;10.0.0.10;[authentication username=1006 password=1234]
1007;10.0.0.10;[authentication username=1007 password=1234]
1008;10.0.0.10;[authentication username=1008 password=1234]
1009;10.0.0.10;[authentication username=1009 password=1234]
{% endhighlight %}

7) Let's try scenario for registration. Please change `local_ip_address` with your SIPp server ip-address and `destination_ip_address` with Freeswitch ip-address.
`-r 1 -rp 1000` is 1 registration per 1000 milliseconds, so we will try 1 registration every second. `-aa` means that we will ignore NOTIFY from Freeswitch.
{% highlight bash %}
cd /usr/src/sipp
./sipp -i local_ip_address -sf /usr/src/sipp2freeswitch/register.xml -inf /usr/src/sipp2freeswitch/register-accounts.csv destination_ip_address:5060 -r 1 -rp 1000 -aa -trace_err
{% endhighlight %}
After couple of seconds you can hit `q` and SIPp will stop running. You should get something similar to:
{% highlight bash %}
----------------------------- Statistics Screen ------- [1-9]: Change Screen --
  Start Time             | 2016-03-14   06:28:10.506266 1457951290.506266
  Last Reset Time        | 2016-03-14   06:28:41.096387 1457951321.096387
  Current Time           | 2016-03-14   06:28:41.097313 1457951321.097313
-------------------------+---------------------------+--------------------------
  Counter Name           | Periodic value            | Cumulative value
-------------------------+---------------------------+--------------------------
  Elapsed Time           | 00:00:00:000000           | 00:00:30:591000
  Call Rate              |    0.000 cps              |    0.981 cps
-------------------------+---------------------------+--------------------------
  Incoming call created  |        0                  |        0
  OutGoing call created  |        0                  |       30
  Total Call created     |                           |       30
  Current Call           |        0                  |
-------------------------+---------------------------+--------------------------
  Successful call        |        0                  |       30
  Failed call            |        0                  |        0
-------------------------+---------------------------+--------------------------
  Response Time 1        | 00:00:00:000000           | 00:00:00:000000
  Call Length            | 00:00:00:000000           | 00:00:00:003000
------------------------------ Test Terminated --------------------------------


2016-03-14      06:28:41.095788 1457951321.095788: Aborted call with Call-ID '513eace0-6472-1234-fa92-0401b57f4a01'.
sipp: There were more errors, see '/usr/src/sipp2freeswitch/register_9906_errors.log' file
{% endhighlight %}
As we can see that we sent 30 registration and all of them was successful, there was some errors, as you can see, but this is about NOTIFY which sends Freeswitch, so this is not very important. :)

8) Now you can try to send more registrations by increasing `-r 1` to `-r 30`, what means that now we will send 30 registrations per second.
{% highlight bash %}
./sipp -i local_ip_address -sf /usr/src/sipp2freeswitch/register.xml -inf /usr/src/sipp2freeswitch/register-accounts.csv destination_ip_address:5060 -r 30 -rp 1000 -aa -trace_err
{% endhighlight %}
After several rounds of increasing `-r` value you should get understanding how much your Freeswitch system can handle and you should compare it with your requirements and if 
necessary adjust performance settings of Freeswitch and if necessary adding more memory and CPUs to Freeswitch server.

9) Let's try second scenario:
{% highlight bash %}
./sipp -i local_ip_address -sf /usr/src/sipp2freeswitch/invite-auth.xml -inf /usr/src/sipp2freeswitch/invite-accounts.csv destination_ip_address:5060 -r 1 -rp 5000
{% endhighlight %}
This command will trigger 1 call each 5 seconds. After some time you can push `q`.

10) After exiting you should see something similar to:
{% highlight bash %}
----------------------------- Statistics Screen ------- [1-9]: Change Screen --
  Start Time             | 2016-03-14   08:08:44.911128 1457957324.911128
  Last Reset Time        | 2016-03-14   08:11:33.026712 1457957493.026712
  Current Time           | 2016-03-14   08:11:33.027607 1457957493.027607
-------------------------+---------------------------+--------------------------
  Counter Name           | Periodic value            | Cumulative value
-------------------------+---------------------------+--------------------------
  Elapsed Time           | 00:00:00:000000           | 00:02:48:116000
  Call Rate              |    0.000 cps              |    0.178 cps
-------------------------+---------------------------+--------------------------
  Incoming call created  |        0                  |        0
  OutGoing call created  |        0                  |       30
  Total Call created     |                           |       30
  Current Call           |        0                  |
-------------------------+---------------------------+--------------------------
  Successful call        |        0                  |       30
  Failed call            |        0                  |        0
-------------------------+---------------------------+--------------------------
  Response Time 1        | 00:00:00:000000           | 00:00:10:086000
  Call Length            | 00:00:00:000000           | 00:00:18:115000
------------------------------ Test Terminated --------------------------------
{% endhighlight %}
As you can see we created 30 calls and all of them was successful. Now you can try to increase `-r` value to 5-10-20-30-... and decrease `-rp` value to 1000, what is one second, if needed. 
At the end you should understand how much call setup per second your server are able to support.

11) At this point you should have some basic understanding how to make performance tests using SIPp. Keep in mind it is always good idea to make some calls and test quality of call while loading Freeswitch with SIPp, 
so you can confirm that call quality is not impacted by your load.
