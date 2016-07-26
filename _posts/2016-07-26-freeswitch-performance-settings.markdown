---
layout: post
title:  "Freeswitch and performance tuning"
date:   2016-07-26 7:10:00 +0200
categories: jekyll update
comments: true
---

1) Freeswitch is great app and it is very well can handle hundreds of calls on single server. Off cause if you have server which do not make transcoding 
and do not have video conference, then you will need much less resources then server who has several conferences and do a lot of transcoding. Freeswitch 
confluence page has a lot of cool info and I used it heavily to write this article: 
<a href="https://freeswitch.org/confluence/display/FREESWITCH/Performance+Testing+and+Configurations">
https://freeswitch.org/confluence/display/FREESWITCH/Performance+Testing+and+Configurations
</a>

2) I recommend to use minimal configuration for all your new set-ups, for this set-up we will use minimal config too. Minimal config you can find in 
freeswitch source file directory under `./conf/minimal`. You can download my minimal config with already applied performance settings from github:
<a href="https://github.com/os11k/freeswitch_minimal_with_perf_settings">
https://github.com/os11k/freeswitch_minimal_with_perf_settings
</a>

3) Below you can see what is difference between minimal config and my updated minimal config with performance settings applied.

{% highlight bash linenos=table %}
diff -ENwbur '--exclude=.git' /usr/src/freeswitch.git/conf/minimal/autoload_configs/logfile.conf.xml /usr/src/perf/autoload_configs/logfile.conf.xml
--- /usr/src/freeswitch.git/conf/minimal/autoload_configs/logfile.conf.xml      2016-05-05 07:45:17.296000000 +0000
+++ /usr/src/perf/autoload_configs/logfile.conf.xml     2016-07-26 11:47:02.048793376 +0000
@@ -15,7 +15,7 @@
             name can be a file name, function name or 'all'
             value is one or more of debug,info,notice,warning,err,crit,alert,all
         -->
-        <map name="all" value="debug,info,notice,warning,err,crit,alert"/>
+        <map name="all" value="err,crit,alert"/>
       </mappings>
     </profile>
   </profiles>
diff -ENwbur '--exclude=.git' /usr/src/freeswitch.git/conf/minimal/autoload_configs/switch.conf.xml /usr/src/perf/autoload_configs/switch.conf.xml
--- /usr/src/freeswitch.git/conf/minimal/autoload_configs/switch.conf.xml       2016-05-05 07:45:17.296000000 +0000
+++ /usr/src/perf/autoload_configs/switch.conf.xml      2016-07-26 11:41:19.060793376 +0000
@@ -1,11 +1,12 @@
 <configuration name="switch.conf" description="Core Configuration">
   <settings>
+    <param name="core-db-name" value="/dev/shm/core.db" />
     <param name="colorize-console" value="true"/>

     <!-- Max number of sessions to allow at any given time -->
-    <param name="max-sessions" value="1000"/>
+    <param name="max-sessions" value="20000"/>
     <!--Most channels to create per second -->
-    <param name="sessions-per-second" value="30"/>
+    <param name="sessions-per-second" value="20000"/>

     <!-- Default Global Log Level - value is one of debug,info,notice,warning,err,crit,alert -->
     <param name="loglevel" value="debug"/>
diff -ENwbur '--exclude=.git' /usr/src/freeswitch.git/conf/minimal/README.md /usr/src/perf/README.md
--- /usr/src/freeswitch.git/conf/minimal/README.md      2016-05-05 07:45:17.296000000 +0000
+++ /usr/src/perf/README.md     2016-07-26 12:34:35.028793376 +0000
@@ -1,4 +1,4 @@
-## Minimal FreeSWITCH Configuration
+## Minimal FreeSWITCH Configuration with minimal performance settings

 The default "vanilla" configuration that comes with FreeSWITCH has
 been designed as a showcase of the configurability of the myriad of
{% endhighlight %}

4) First I changed config file `./autoload_configs/logfile.conf.xml`, changes you can find below. I changed this file in such way that we 
will write to log file only err, crit and alert log levels. On busy server we don't want to write to much info to log files cause it might affect 
performance.

{% highlight bash %}
-        <map name="all" value="debug,info,notice,warning,err,crit,alert"/>
+        <map name="all" value="err,crit,alert"/>
{% endhighlight %}

5) In regular config Freeswitch writes to file system almost every second, to fix this we can have freeswitch internal DB in memory. For this 
we need to add following line to: `./autoload_configs/switch.conf.xml`.

{% highlight bash %}
+    <param name="core-db-name" value="/dev/shm/core.db" />
{% endhighlight %}

6) Minimal config by default has limitation to 1000 simultaneous calls and 30 call setups per seconds, probably on busy system you need much more. 
I changed both values to 20000, nevertheless theoretical limit for gigabit Ethernet port is about 10500 simultaneous calls for G.711 codec.

{% highlight bash %}
     <!-- Max number of sessions to allow at any given time -->
-    <param name="max-sessions" value="1000"/>
+    <param name="max-sessions" value="20000"/>
     <!--Most channels to create per second -->
-    <param name="sessions-per-second" value="30"/>
+    <param name="sessions-per-second" value="20000"/>
{% endhighlight %}

7) Last, but not least, we will need to add this "magic" ulimit settings to maximize performance, sadly freeswitch confluence page do not have exact 
explanation, where to put this ulimit settings. Thanks to me now you know that We need to put ulimit inside init.d script, 
my init.d script you can find here:

<a href="https://github.com/os11k/freeswitch_init_with_ulimit">
https://github.com/os11k/freeswitch_init_with_ulimit
</a>

You should add following lines before `do_start()` in `/etc/init.d/freeswitch` file

{% highlight bash %}
ulimit -c unlimited # The maximum size of core files created.
ulimit -d unlimited # The maximum size of a process's data segment.
ulimit -f unlimited # The maximum size of files created by the shell (default option)
ulimit -i unlimited # The maximum number of pending signals
ulimit -n 999999    # The maximum number of open file descriptors.
ulimit -q unlimited # The maximum POSIX message queue size
ulimit -u unlimited # The maximum number of processes available to a single user.
ulimit -v unlimited # The maximum amount of virtual memory available to the process.
ulimit -x unlimited # ???
ulimit -s 240         # The maximum stack size
ulimit -l unlimited # The maximum size that may be locked into memory.
ulimit -a           # All current limits are reported.
{% endhighlight %}

8) Additionally you might need to remove unnecessary modules from `./autoload_configs/modules.conf.xml` and leave only ones which you are using.
With this config I was able to load server using SIPP with 8k simultaneous calls and it was performing very well. 
You can check my [article](/jekyll/update/2016/03/14/freeswitch-performance-tests.html) about running performance tests and try to run performance 
test on your own server.
