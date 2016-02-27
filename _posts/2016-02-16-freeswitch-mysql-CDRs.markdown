---
layout: post
title:  "Freeswitch 1.6 and MySQL CDRs on Debian 8"
date:   2016-02-16 17:12:35 +0200
categories: jekyll update
comments: true
---
In this manual I will try to explain what you need to do, to get freeswitch CDRs saved to MySQL. On this point I assume that freeswitch and MySQL are installed already.

1) First we will need to isntall unixodbc & libmyodbc, by running following command:
{% highlight bash %}
apt-get install unixodbc libmyodbc
{% endhighlight %}

2) Please update /etc/odbcinst.ini:
{% highlight bash %}
[MySQL]
Description = ODBC for MySQL
Driver = /usr/lib/x86_64-linux-gnu/odbc/libmyodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libodbcmyS.so
FileUsage = 1
{% endhighlight %}

3) In my example MySQL is running on same server where freeswitch, please change `localhost` to your ip-address if MySQL DB is on separate machine. DB name, username and password is freeswitch in my case, but you will need to update it accordingly. When you are ready with config, please save it to `/etc/odbc.ini`.
{% highlight bash %}
[freeswitch]
Description           = MySQL connection to 'freeswitch' database
Driver                = MySQL
Database              = freeswitch
Server                = localhost
USER                  = freeswitch
PASSWORD              = freeswitch
Port                  = 3306
Socket                = /var/run/mysqld/mysqld.sock
{% endhighlight %}

4) Now we need to test if you set-up ODBC correctly, please run `echo "select 1" | isql -v freeswitch` in shell, you should get something similar to what you see below:
{% highlight bash %}
+---------------------------------------+
| Connected!                            |
|                                       |
| sql-statement                         |
| help [tablename]                      |
| quit                                  |
|                                       |
+---------------------------------------+
SQL> select 1
+---------------------+
| 1                   |
+---------------------+
| 1                   |
+---------------------+
SQLRowCount returns 1
1 rows fetched
{% endhighlight %}

5) Now we need to recompile freeswitch with mod_odbc_cdr. Go to freeswitch source category and add line `event_handlers/mod_odbc_cdr` on top 
of `/usr/src/freeswitch/modules.conf`(please update path accordingly if your freeswitch source directory is different):
{% highlight bash %}
event_handlers/mod_odbc_cdr
#applications/mod_abstraction
#applications/mod_av
#applications/mod_avmd
#applications/mod_bert
#applications/mod_blacklist
#applications/mod_callcenter
#applications/mod_cidlookup
#applications/mod_cluechoo
applications/mod_commands
...
{% endhighlight %}

6) In freeswitch source directory run: 
{% highlight bash %}
make
make install
{% endhighlight %}

7) At this point we need to copy odbc_cdr.conf.xml to freeswich conf directory, I'm assuming that freeswitch source directory is `/usr/src/freeswitch`
{% highlight bash %}
cp /usr/src/freeswitch/src/mod/event_handlers/mod_odbc_cdr/conf/autoload_configs/odbc_cdr.conf.xml /usr/local/freeswitch/conf/autoload_configs/odbc_cdr.conf.xml
{% endhighlight %}

8) Please update `/usr/local/freeswitch/conf/autoload_configs/odbc_cdr.conf.xml` accordingly so it points to MySQL DB(line No4). In line no 4 `freeswitch` is connection name or value in square brackets in first line of `/etc/odbc.ini`:
{% highlight bash linenos=table %}
<configuration name="odbc_cdr.conf" description="ODBC CDR Configuration">
  <settings>
    <!-- <param name="odbc-dsn" value="database:username:password"/> -->
	<param name="odbc-dsn" value="odbc://freeswitch"/>
        <!-- global value can be "a-leg", "b-leg", "both" (default is "both") -->
        <param name="log-leg" value="both"/>
    <!-- value can be "always", "never", "on-db-fail" -->
    <param name="write-csv" value="on-db-fail"/>
        <!-- location to store csv copy of CDR -->
    <param name="csv-path" value="/usr/local/freeswitch/log/odbc_cdr"/>
    <!-- if "csv-path-on-fail" is set, failed INSERTs will be placed here as CSV files otherwise they will be placed in "csv-path" -->
    <param name="csv-path-on-fail" value="/usr/local/freeswitch/log/odbc_cdr/failed"/>
    <!-- dump SQL statement after leg ends -->
        <param name="debug-sql" value="true"/>
  </settings>
  <tables>
        <!-- only a-legs will be inserted into this table -->
    <table name="cdr_table_a_leg" log-leg="a-leg">
      <field name="CallId" chan-var-name="call_uuid"/>
      <field name="orig_id" chan-var-name="uuid"/>
      <field name="term_id" chan-var-name="sip_call_id"/>
      <field name="ClientId" chan-var-name="uuid"/>
      <field name="IP" chan-var-name="sip_network_ip"/>
      <field name="IPInternal" chan-var-name="sip_via_host"/>
      <field name="CODEC" chan-var-name="read_codec"/>
      <field name="directGateway" chan-var-name="sip_req_host"/>
      <field name="redirectGateway" chan-var-name="sip_redirect_contact_host_0"/>
      <field name="CallerID" chan-var-name="sip_from_user"/>
      <field name="TelNumber" chan-var-name="sip_req_user"/>
      <field name="TelNumberFull" chan-var-name="sip_to_user"/>
      <field name="sip_endpoint_disposition" chan-var-name="endpoint_disposition"/>
      <field name="sip_current_application" chan-var-name="current_application"/>
    </table>
        <!-- only b-legs will be inserted into this table -->
    <table name="cdr_table_b_leg" log-leg="b-leg">
      <field name="CallId" chan-var-name="call_uuid"/>
      <field name="orig_id" chan-var-name="uuid"/>
      <field name="term_id" chan-var-name="sip_call_id"/>
      <field name="ClientId" chan-var-name="uuid"/>
      <field name="IP" chan-var-name="sip_network_ip"/>
      <field name="IPInternal" chan-var-name="sip_via_host"/>
      <field name="CODEC" chan-var-name="read_codec"/>
      <field name="directGateway" chan-var-name="sip_req_host"/>
      <field name="redirectGateway" chan-var-name="sip_redirect_contact_host_0"/>
      <field name="CallerID" chan-var-name="sip_from_user"/>
      <field name="TelNumber" chan-var-name="sip_req_user"/>
      <field name="TelNumberFull" chan-var-name="sip_to_user"/>
      <field name="sip_endpoint_disposition" chan-var-name="endpoint_disposition"/>
      <field name="sip_current_application" chan-var-name="current_application"/>
    </table>
        <!-- both legs will be inserted into this table -->
    <table name="cdr_table_both">
      <field name="CallId" chan-var-name="uuid"/>
      <field name="orig_id" chan-var-name="Caller-Unique-ID"/>
      <field name="TEST_id" chan-var-name="sip_from_uri"/>
    </table>
  </tables>
</configuration>
{% endhighlight %}

9) Please enable auto-load of mod_odbc_cdr. For this you need to edit /usr/local/freeswitch/conf/autoload_configs/modules.conf.xml and add `<load module="mod_odbc_cdr"/>` on top of `<load module="mod_cdr_csv"/>`. In my minimal set-up it looks in following way(line No12):
{% highlight bash linenos=table %}
<configuration name="modules.conf" description="Modules">
  <modules>

    <!-- Loggers (I'd load these first) -->
    <load module="mod_console"/>
    <load module="mod_logfile"/>

    <!-- XML Interfaces -->
    <load module="mod_xml_rpc"/>

    <!-- Event Handlers -->
    <load module="mod_odbc_cdr"/>
    <load module="mod_cdr_csv"/>
    <load module="mod_event_socket"/>

    <!-- Endpoints -->
    <load module="mod_sofia"/>
    <load module="mod_loopback"/>

    <!-- Applications -->
    <load module="mod_commands"/>
    <load module="mod_conference"/>
    <load module="mod_db"/>
    <load module="mod_dptools"/>
    <load module="mod_expr"/>
    <load module="mod_hash"/>
    <load module="mod_esf"/>

    <!-- Dialplan Interfaces -->
    <load module="mod_dialplan_xml"/>

    <!-- Codec Interfaces -->

    <!-- File Format Interfaces -->
    <load module="mod_sndfile"/>
    <load module="mod_native_file"/>

    <!-- Third party modules -->

  </modules>
</configuration>
{% endhighlight %}

10) Now we need to create tables:
{% highlight sql %}
CREATE TABLE IF NOT EXISTS `cdr_table_a_leg` (
`CallId` varchar(80) DEFAULT NULL,
`orig_id` varchar(80) DEFAULT NULL,
`term_id` varchar(80) DEFAULT NULL,
`ClientId` varchar(80) DEFAULT NULL,
`IP` varchar(80) DEFAULT NULL,
`IPInternal` varchar(80) DEFAULT NULL,
`CODEC` varchar(80) DEFAULT NULL,
`directGateway` varchar(80) DEFAULT NULL,
`redirectGateway` varchar(80) DEFAULT NULL,
`CallerID` varchar(80) DEFAULT NULL,
`TelNumber` varchar(80) DEFAULT NULL,
`TelNumberFull` varchar(80) DEFAULT NULL,
`sip_endpoint_disposition` varchar(80) DEFAULT NULL,
`sip_current_application` varchar(80) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS `cdr_table_b_leg` (
`CallId` varchar(80) DEFAULT NULL,
`orig_id` varchar(80) DEFAULT NULL,
`term_id` varchar(80) DEFAULT NULL,
`ClientId` varchar(80) DEFAULT NULL,
`IP` varchar(80) DEFAULT NULL,
`IPInternal` varchar(80) DEFAULT NULL,
`CODEC` varchar(80) DEFAULT NULL,
`directGateway` varchar(80) DEFAULT NULL,
`redirectGateway` varchar(80) DEFAULT NULL,
`CallerID` varchar(80) DEFAULT NULL,
`TelNumber` varchar(80) DEFAULT NULL,
`TelNumberFull` varchar(80) DEFAULT NULL,
`sip_endpoint_disposition` varchar(80) DEFAULT NULL,
`sip_current_application` varchar(80) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS `cdr_table_both` (
`CallId` varchar(80) DEFAULT NULL,
`orig_id` varchar(80) DEFAULT NULL,
`TEST_id` varchar(80) DEFAULT NULL
);
{% endhighlight %}

11) Please restart freeswitch: `service freeswitch restart`

12) On this point you can check if module `mod_odbc_cdr` loaded. Please run following command in freeswitch CLI:
{% highlight bash %}
module_exists mod_odbc_cdr
{% endhighlight %}
If everything is ok, you will get following output:
{% highlight bash %}
freeswitch@internal> module_exists mod_odbc_cdr
true
freeswitch@internal>
{% endhighlight %}

13) On this point you CDRs should be written to MySQL DB, if somehow you still do not get CDRs in DB, you need to check `/usr/local/freeswitch/log/freeswitch.log` for errors or any other hints. 
Keep in mind that you might need to add some additional fields to DB and update `odbc_cdr.conf.xml` accordingly. Please take a closer look on data type used in 
CDRs table, probably it is not optimal and  you might need to update it.
