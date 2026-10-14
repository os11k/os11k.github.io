---  
layout: post
title: "Best WordPress Cache Plugin"  
description: "Cut WordPress response times from around 800ms to under 200ms with Cloudflare and the free Super Page Cache plugin, with step-by-step setup and real graphs."
tags: [wordpress, cloudflare, performance]
date: 2025-04-30 10:00:00 +0200
categories: jekyll update  
comments: true
image: /assets/wordpress-cloudflare/7.webp
---

## Overview

This is a bit different guide than I usually publish, but I really wanted to write about the best WordPress cache plugin I found and personally use. Recently, I needed to manage a WordPress installation, and this is what I observed:

<img src="{{ '/assets/wordpress-cloudflare/1.webp' | relative_url }}" alt="Response time chart over 7 days for a WordPress site: mostly 200 to 400 ms with frequent spikes to 800 ms and some above 1 second" width="1600" height="526">

As you can see, my monitoring shows that the WordPress website mostly responds between 200 & 400ms, which I think is acceptable. However, there are several instances above 1 second, and very often it was around 800ms, which was definitely disappointing.

Long story short, I spent one night figuring out how to make it faster. The solution was to use Cloudflare with the `Super Page Cache` WordPress plugin.

After successful deployment, you can see a new graph from my monitoring. I deployed the `Super Page Cache` WordPress plugin around 1:00, and now all requests are between 30ms and 200ms, which is amazing. Basically, I have the same statistics from my static websites that I host on S3!

<img src="{{ '/assets/wordpress-cloudflare/7.webp' | relative_url }}" alt="Response time chart after enabling Super Page Cache: the spiky left half drops to a flat line under 200 ms, marked with an arrow and party emojis" width="1600" height="534">

Below, I provide a step-by-step guide to deploy the `Super Page Cache` WordPress plugin the same way I did. 

## Requirements

So, the first and most obvious requirement is a WordPress website that you want to speed up. Second, you need a free Cloudflare account. Just go to `cloudflare.com` and register there. 

## Add domain to cloudflare

When you have a Cloudflare account, please log in to Cloudflare and on the main screen, add your domain and select quick scan, which should scan your existing DNS records and set up all accordingly.

<img src="{{ '/assets/wordpress-cloudflare/2.webp' | relative_url }}" alt="Cloudflare add a domain screen with randomobjectgenerator.one entered and Quick scan for DNS records selected" width="1600" height="690" loading="lazy">

Then select the free plan, then `continue to activation`:

<img src="{{ '/assets/wordpress-cloudflare/3.webp' | relative_url }}" alt="Cloudflare DNS management page listing the imported A and NS records, with a Continue to activation button" width="1600" height="588" loading="lazy">

Then you will get to the page where you should get nameservers:

<img src="{{ '/assets/wordpress-cloudflare/4.webp' | relative_url }}" alt="Cloudflare instructions to replace the current nameservers with julio.ns.cloudflare.com and raina.ns.cloudflare.com" width="1600" height="899" loading="lazy">

Now those nameservers you should put in your registrar.

In this example, those servers are:

```
julio.ns.cloudflare.com
raina.ns.cloudflare.com
```

additional manual from cloudflare:

[Update nameservers](https://developers.cloudflare.com/dns/nameservers/update-nameservers/#your-domain-uses-a-different-registrar)

When you set up your registrar, press continue and then press `check nameservers`.

In a few minutes, you should get an email that all is good, and then you can go to the main screen and see that your server is active:

<img src="{{ '/assets/wordpress-cloudflare/5.webp' | relative_url }}" alt="Cloudflare domains list showing randomobjectgenerator.one with status Active on the Free plan" width="1600" height="483" loading="lazy">

Obviously, your setup may differ, but on my test installation, I instantly got:

`ERR_TOO_MANY_REDIRECTS`:

<img src="{{ '/assets/wordpress-cloudflare/0.webp' | relative_url }}" alt="Chrome error page: randomobjectgenerator.one redirected you too many times, ERR_TOO_MANY_REDIRECTS" width="1600" height="972" loading="lazy">

That means the end-user connects to Cloudflare via HTTPS, and then Cloudflare tries to connect to your server via HTTP. My server sees the connection via HTTP, wants to redirect to HTTPS, and it creates a loop. It seems it is because, by default, Cloudflare uses encryption mode as `Flexible`:

<img src="{{ '/assets/wordpress-cloudflare/6.webp' | relative_url }}" alt="Cloudflare SSL/TLS overview showing the current encryption mode as Flexible, with a Configure button" width="1600" height="533" loading="lazy">

To fix it, you can select either `Full` or `Full (Strict)` encryption. So the connection from Cloudflare and to your server will be encrypted. If you use `Full (Strict)`, make sure you use a valid certificate on your server or one which Cloudflare provides, otherwise, you will face issues. And if you stick with `Full (Strict)`, make sure you don't forget to renew the expiring certificate, otherwise, you might end up in the same troubles as some big corporate companies.

Long story short, after setting to `Full (Strict)`, my WordPress website was online again!

## Configure Super Page Cache WordPress plugin

Next step would be to install the plugin on your WordPress. Just go to your WordPress admin panel, then to plugins, and hit `Add Plugin`, and in the search bar, put `Super Page Cache`:

<img src="{{ '/assets/wordpress-cloudflare/8.webp' | relative_url }}" alt="WordPress Add Plugins search results for Super Page Cache with the Install Now button on the Super Page Cache plugin by Optimole" width="1600" height="919" loading="lazy">

Click `Install Now` and then click `Activate`, then it will open new screen:

<img src="{{ '/assets/wordpress-cloudflare/9.webp' | relative_url }}" alt="Super Page Cache welcome screen with an Enable Page Caching Now button" width="1600" height="941" loading="lazy">

Please make sure you disabled caching of any other plugins if there were any!

Then hit `ENABLE PAGE CACHING NOW`

You should see confirmation with `Page cache enabled successfully`

## Getting cloudflare API key

Next, we need to get an API key so we can set up the Super Page Cache plugin to authorize and update necessary settings in Cloudflare.

To get the API key, go to `Profile` => `API Tokens` and click `View` under `Global API Key`. Make sure you secure your API key, don't share it with anyone!

When we have the key, we can continue with the Super Page Cache plugin

## Configuring Cloudflare (CDN & Edge Caching) in plugin

Go back to your `WordPress admin page` => `Plugins` => `Super Page Cache` => `Settings` => `Cloudflare (CDN & Edge Caching)`. Under `Cloudflare e-mail`, put your Cloudflare email, and under `Cloudflare API Key`, the key we just grabbed from Cloudflare, and press `UPDATE SETTINGS`:

<img src="{{ '/assets/wordpress-cloudflare/10.webp' | relative_url }}" alt="Super Page Cache Cloudflare settings tab with authentication mode API Key, a Cloudflare e-mail and an API key filled in, and an Update Settings button" width="1600" height="1032" loading="lazy">

Then on the new window, make sure you have the correct domain name under `Cloudflare Domain Name`. If you have several ones, for me, it took straight away the correct one:

<img src="{{ '/assets/wordpress-cloudflare/11.webp' | relative_url }}" alt="Super Page Cache cache settings with Cloudflare Domain Name set to randomobjectgenerator.one and Enable Disk Page cache set to Yes" width="1600" height="1113" loading="lazy">

Hit `Continue`, and you should be good!

## Validate Super Page Cache plugin

Next, a good idea would be to double-check that all is good, so on the same page, just click `TEST CACHE`, and if all is good, you should see this screen with 2 green ticks - `Cloudflare Page Caching is working properly` & `Disk Page Caching is functional`:

<img src="{{ '/assets/wordpress-cloudflare/12.webp' | relative_url }}" alt="Super Page Cache status dialog with two green ticks: Cloudflare Page Caching is working properly and Disk Page Caching is functional" width="1600" height="862" loading="lazy">

And we are done!

## Conclusion

Obviously, the `Super Page Cache` plugin is just one piece of your infrastructure/deployment, and it is not a silver bullet, and if you have several underlying issues with your setup, I doubt that it will help a lot. Nevertheless, it can speed up your WordPress significantly, which is not just promises but backed up with statistics from my monitoring of my WordPress setup before and after I installed the plugin. I was not paid or sponsored by the author of the plugin, I just felt that I must share this with others, because for me, this plugin worked really well and way above my expectations, and most importantly, this costs nothing. You get all this performance improvement for free!