---
layout: post  
title: "HOMER 7 Packet Manipulation Using Lua"  
date: 2024-11-24 18:00:00 +0200  
categories: jekyll update  
comments: true  
---

In this guide, I will show how to manipulate data written in HOMER 7 using Lua scripts. Here is the official documentation:

[HOMER 7 Packet Manipulation Using LuaJIT](https://github.com/sipcapture/homer/wiki/HOMER-LUA-Scripting)

In this example, we'll modify the "User-Agent" header in the `CANCEL` SIP method to "cisco".

This tutorial assumes you already have HOMER 7 up and running, and that your PBX is sending data to it. We are also assuming HOMER 7 is running in Docker.

## Step 1: Create the lua Directory

First, create a `./lua` directory in the folder where your `docker-compose.yml` file is located. Then, add this directory as a bind mount for the `heplify-server` container by adding the following code to the relevant section:

{% highlight bash %}
volumes:
  - ./lua:/lua
{% endhighlight %}

Additionally, set the following environment variables in your `docker-compose.yml`:

{% highlight bash %}
    - "HEPLIFYSERVER_SCRIPTENABLE=true"
    - "HEPLIFYSERVER_SCRIPTFOLDER=/lua/"
{% endhighlight %}

For reference, here is the updated configuration for `heplify-server` in `docker-compose.yml`:

{% highlight bash %}
heplify-server:
  image: sipcapture/heplify-server
  container_name: heplify-server
  ports:
    - "9060:9060"
    - "9060:9060/udp"
    - "9061:9061/tcp"
  command:
    - './heplify-server'
  environment:
    - "HEPLIFYSERVER_HEPADDR=0.0.0.0:9060"
    - "HEPLIFYSERVER_HEPTCPADDR=0.0.0.0:9061"
    - "HEPLIFYSERVER_DBSHEMA=homer7"
    - "HEPLIFYSERVER_DBDRIVER=postgres"
    - "HEPLIFYSERVER_DBADDR=db:5432"
    - "HEPLIFYSERVER_DBUSER=root"
    - "HEPLIFYSERVER_DBPASS=homerSeven"
    - "HEPLIFYSERVER_DBDATATABLE=homer_data"
    - "HEPLIFYSERVER_DBCONFTABLE=homer_config"
    - "HEPLIFYSERVER_DBROTATE=true"
    - "HEPLIFYSERVER_DBDROPDAYS=5"
    - "HEPLIFYSERVER_LOGLVL=info"
    - "HEPLIFYSERVER_LOGSTD=true"
    - "HEPLIFYSERVER_PROMADDR=0.0.0.0:9096"
    - "HEPLIFYSERVER_DEDUP=false"
    - "HEPLIFYSERVER_LOKIURL=http://loki:3100/api/prom/push"
    - "HEPLIFYSERVER_LOKITIMER=2"
    - "HEPLIFYSERVER_SCRIPTENABLE=true"
    - "HEPLIFYSERVER_SCRIPTFOLDER=/lua/"
  restart: unless-stopped
  depends_on:
    - loki
    - db
  expose:
    - 9090
    - 9096
  volumes:
    - ./lua:/lua
  labels:
    org.label-schema.group: "monitoring"
  logging:
    options:
      max-size: "50m"
{% endhighlight %}

## Step 2: Create Lua Code

Now, create a file named `my.lua` in the newly created `./lua` folder. Use the following code:

{% highlight bash %}
-- This Lua code modifies the "User-Agent" header to "cisco" in CANCEL methods. 
-- If there are multiple "User-Agent" headers, it will update all of them.

-- This function will be executed first
function checkRAW()

    local protoType = GetHEPProtoType()

    -- Check if the packet is of SIP type
    if protoType ~= 1 then
        return
    end

    -- Get the original SIP message payload
    local raw = GetRawMessage()

    -- Extract the method name from the first few characters
    local method = string.sub(raw, 1, 6)

    if method == "CANCEL" then
        -- Replace "User-Agent" header with "cisco"
        local ripe, count = string.gsub(raw, "(User%-Agent:)(.-)(\n+)", "%1 cisco%3")

        if count > 0 then
            Logp("ERROR", "ripe", ripe)
            SetRawMessage(ripe)
        end
    end

    return
end
{% endhighlight %}

## Step 3: Restart Your Containers

Restart your Docker containers to apply the changes:

{% highlight bash %}
docker compose down
docker compose up -d --build
{% endhighlight %}

## Step 4: Verify

Log in to HOMER and check the `CANCEL` method. The `User-Agent` header should now be `cisco`. As you can see in my example, the same call is used, but the Invite has an untouched user agent `LinphoneiOS/5.2.4 (iPhone) LinphoneSDK/5.3.89`, while the Cancel has it changed to `cisco`:

![Diagram]({{ site.url }}/assets/homer7-lua/0.png)