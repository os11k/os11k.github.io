---
layout: post
title:  "Freeswitch 1.6 install on Debian 8 from git"
date:   2016-02-23 15:38:00 +0200
categories: jekyll update
comments: true
---
I compiled this manual from several official Freeswitch documentation pages, which is great place to start, but all of them are missing full steps - for example latest one at this time is missing post installation steps, but it is covered in older documentation, what is fine, but sometimes is hard to find, so I believe it will be nice to have all of this info just in one page. :)

1) We will need to install dependencies:
{% highlight bash %}
apt-get update && apt-get install -y curl
curl https://files.freeswitch.org/repo/deb/debian/freeswitch_archive_g0.pub | apt-key add -
 
echo "deb http://files.freeswitch.org/repo/deb/freeswitch-1.6/ jessie main" > /etc/apt/sources.list.d/freeswitch.list
apt-get update
apt-get install -y --force-yes freeswitch-video-deps-most
 
# because we're in a branch that will go through many rebases it's
# better to set this one, or you'll get CONFLICTS when pulling (update)
git config --global pull.rebase true
{% endhighlight %}

2) Getting source from git:
{% highlight bash %}
cd /usr/src/
git clone https://freeswitch.org/stash/scm/fs/freeswitch.git -bv1.6 freeswitch.git
{% endhighlight %}

3) Now we need to install Freeswitch:
{% highlight bash %}
cd freeswitch.git
./bootstrap.sh -j
./configure
make
make install
{% endhighlight %}

4) We will download sound-files:
{% highlight bash %}
make cd-sounds-install cd-moh-install
{% endhighlight %}

5) Add user and change user owner of necessary folders:
{% highlight bash %}
adduser --disabled-password  --quiet --system --home /usr/local/freeswitch --gecos "FreeSWITCH Voice Platform" --ingroup daemon freeswitch
chown -R freeswitch:daemon /usr/local/freeswitch/
chmod -R ug=rwX,o= /usr/local/freeswitch/
chmod -R u=rwx,g=rx /usr/local/freeswitch/bin/*
{% endhighlight %}

6) We need to create symbolic link for freeswitch binary file, create missing folders, change rights and etc:
{% highlight bash %}
ln /usr/local/freeswitch/bin/freeswitch /usr/bin/freeswitch
mkdir /etc/freeswitch
ln /usr/local/freeswitch/conf/freeswitch.xml /etc/freeswitch/freeswitch.xml
chown freeswitch:daemon /etc/freeswitch
chmod ug=rwx,o= /etc/freeswitch
mkdir /var/lib/freeswitch
chown freeswitch:daemon /var/lib/freeswitch
chmod -R ug=rwX,o= /var/lib/freeswitch
{% endhighlight %}

7) Now we need to copy default file and init file and update access rights:
{% highlight bash %}
cp /usr/src/freeswitch.git/debian/freeswitch-sysvinit.freeswitch.default /etc/default/freeswitch
chown freeswitch:daemon /etc/default/freeswitch
chmod ug=rw,o= /etc/default/freeswitch
cp /usr/src/freeswitch.git/debian/freeswitch-sysvinit.freeswitch.init  /etc/init.d/freeswitch
chown freeswitch:daemon /etc/init.d/freeswitch
chmod u=rwx,g=rx,o= /etc/init.d/freeswitch
{% endhighlight %}

8) Following step is not mandatory, but it is much easier when you can just run fs_cli from shell, otherwise you will need to run /usr/local/freeswitch/bin/fs_cli or to add freeswitch bin directory to $PATH.
{% highlight bash %}
ln /usr/local/freeswitch/bin/fs_cli /usr/bin/fs_cli
{% endhighlight %}

9) Now you need to update /etc/init.d/freeswitch accordingly(lines 23-27):
{% highlight bash %}
CONFDIR=/usr/local/freeswitch/conf
RUNDIR=/var/run/$NAME
PIDFILE=$RUNDIR/$NAME.pid
SCRIPTNAME=/etc/init.d/$NAME
WORKDIR=/usr/local/freeswitch/log
{% endhighlight %}

10) Now we need to make sure that freeswitch starts automatically after reboot:
{% highlight bash %}
update-rc.d freeswitch defaults
{% endhighlight %}

11) Please do not forget to change default password for default extensions in /usr/local/freeswitch/conf/vars.xml
