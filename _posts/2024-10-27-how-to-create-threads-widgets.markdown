---
layout: post
title:  "How to Create a Widget for Meta Threads using Scriptable"
description: "Build iOS home screen widgets for Meta Threads with the Scriptable app and the Threads API: follower counts, profile visitors and views on your latest post."
tags: [threads, scriptable, ios, api]
date:   2024-10-26 16:01:00 +0200
categories: jekyll update
comments: true
---

This post will be a bit different. I recently started using Meta Threads, and I saw someone complaining that Meta should create a widget for certain stats. I replied, saying it should be possible using the Scriptable app. Long story short, I decided to dive into this rabbit hole and create some widgets for Meta Threads. I’ll be creating two widgets—one for follower counts and profile visitors for today and yesterday, and a second widget to display view counts for the latest post. I’ll be using the Scriptable app to make these, which you can download for free from the iOS App Store.

<img src="{{ '/assets/threads_widget/0.webp' | relative_url }}" alt="Diagram" width="1097" height="1280" style="width: 25%;">

## Step 1: Set Up the Meta App

The first thing to do is go to [Meta for Developers](https://developers.facebook.com/) and create an app.

Once you're there, the setup process is mostly "next-next-next."

Select **"I don’t want to connect a business portfolio yet."**

<img src="{{ '/assets/threads_widget/1.webp' | relative_url }}" alt="Diagram" width="1600" height="618">

Then, choose **"Access the Threads API"**.

<img src="{{ '/assets/threads_widget/2.webp' | relative_url }}" alt="Diagram" width="1600" height="909">

Enter your app name and email:

<img src="{{ '/assets/threads_widget/3.webp' | relative_url }}" alt="Diagram" width="1600" height="524">

Click **"Go to Dashboard"**.

<img src="{{ '/assets/threads_widget/4.webp' | relative_url }}" alt="Diagram" width="1600" height="495" loading="lazy">

In the dashboard settings, continue with more "next-next-next."

<img src="{{ '/assets/threads_widget/5.webp' | relative_url }}" alt="Diagram" width="1600" height="722" loading="lazy">

First, go to **"Access the Threads API"** and select **"threads_basic"** and **"threads_manage_insights"**—these are the bare minimum permissions needed for this project. If you want to do more, adjust your permissions accordingly.

<img src="{{ '/assets/threads_widget/6.webp' | relative_url }}" alt="Diagram" width="1600" height="883" loading="lazy">

Then, click **"Test Use Cases"** (it should automatically show a green tick).

<img src="{{ '/assets/threads_widget/7.webp' | relative_url }}" alt="Diagram" width="1600" height="709" loading="lazy">

Finally, click **"Finish Customization"**.

<img src="{{ '/assets/threads_widget/8.webp' | relative_url }}" alt="Diagram" width="1600" height="733" loading="lazy">

## Step 2: Add Roles

Now, go to **"App Roles"** and then to **"Roles"**.

<img src="{{ '/assets/threads_widget/9.webp' | relative_url }}" alt="Diagram" width="1353" height="1521" loading="lazy" style="width: 25%;">

Click **"Add People"** and select **"Threads Tester."** Below that, add your own user, as shown in the screenshot:

<img src="{{ '/assets/threads_widget/10.webp' | relative_url }}" alt="Diagram" width="1600" height="752" loading="lazy">

Now, open the Threads app with that user. Go to **Settings > Account > Website Permissions > Invites** and accept the invite.

<img src="{{ '/assets/threads_widget/11.webp' | relative_url }}" alt="Diagram" width="1600" height="1024" loading="lazy">

## Step 3: Get an Access Token

Now, we need to get a token. Go to the [Facebook Developer Explorer](https://developers.facebook.com/tools/explorer/).

Select **"threads.net"** and click **"Generate Threads Access Token"**.

<img src="{{ '/assets/threads_widget/12.webp' | relative_url }}" alt="Diagram" width="1600" height="598" loading="lazy">

When the Threads pop-up appears, just click **"Continue."**

<img src="{{ '/assets/threads_widget/13.webp' | relative_url }}" alt="Diagram" width="1600" height="1227" loading="lazy">

You’ll now see your token in the **"Access Token"** field.

<img src="{{ '/assets/threads_widget/14.webp' | relative_url }}" alt="Diagram" width="1600" height="734" loading="lazy">

Validate that your token works by using the **"Access Token Debugger":**

[Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)

If it shows something similar to the screenshot below, then you’re good to go.

<img src="{{ '/assets/threads_widget/15.webp' | relative_url }}" alt="Diagram" width="1600" height="913" loading="lazy">

## Step 4: Exchange for a Long-Lived Token

Now we need to exchange this short-lived token (which expires in 60 minutes) for a long-lived token that will last two months. Details are here: [Long-Lived Tokens](https://developers.facebook.com/docs/threads/get-started/long-lived-tokens/).

Run this command:
{% highlight bash %}
curl -s -X GET "https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=<THREADS_APP_SECRET>&access_token=<SHORT_LIVED_ACCESS_TOKEN>"
{% endhighlight %}

Since we’re missing `THREADS_APP_SECRET`, go to [Facebook Apps](https://developers.facebook.com/apps/?show_reminder=true), select your app, and go to **"App Settings"** > **"Basic"**. You’ll see a screen like this:

<img src="{{ '/assets/threads_widget/16.webp' | relative_url }}" alt="Diagram" width="1600" height="776" loading="lazy">

Click **"Show"** next to **"App Secret"**.

Now use this in the `curl` command above to get your long-lived token.

Once you have the long-lived token, recheck it using the [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/).

## Step 5: Start Building the Widgets

The idea is to have two widgets—a "main" widget for followers + visitors and a "secondary" widget for the last post's view count.

- The main widget will display stats and handle token refresh, saving it in iCloud under the same filename you initially used. 
- The secondary widget will use the same token from iCloud but won’t handle token refreshes (assuming the token remains valid). This means you can’t use the secondary widget independently without adjusting the code. You can, however, copy the token refresh code from the main widget to the secondary if needed.

## Step 6: Save the Long-Lived Token to iCloud

To store the token, use this one-time Scriptable app code during your initial setup. The main widget code will handle future token refreshes and updates:

[Token Storage Script](https://gist.github.com/os11k/501d7b2be09c6bba0e734485cce28365)

Once the token is in iCloud, we’re ready to build the main widget.

## Building the Widgets

Documentation from Meta used for the main widget:

[Meta Threads Insights Documentation](https://developers.facebook.com/docs/threads/insights/)

For the main widget, I’m using the following endpoints for followers and profile visitors:

**Followers:**
{% highlight bash %}
https://graph.threads.net/v1.0/me/threads_insights?metric=followers_count&access_token=zzz
{% endhighlight %}

**Profile Visitors:**
{% highlight bash %}
https://graph.threads.net/v1.0/me/threads_insights?metric=views&access_token=zzz
{% endhighlight %}

You can find the full code for the main widget here:

[Main Widget Code](https://gist.github.com/os11k/1f109155706ce2bef8b68ea61a324126)

The secondary widget checks the latest post, and if a post exists with stats (since reposts have no views), it displays the view count and a snippet of the post. For reposts, it’ll just show 0.

Documentation from Meta for this part is here:

[Meta Threads Documentation](https://developers.facebook.com/docs/threads/threads-media)

To fetch the latest threads:
{% highlight bash %}
https://graph.threads.net/v1.0/me/threads?fields=id,text,views&access_token=zzz
{% endhighlight %}

Then, retrieve stats for the latest thread:
{% highlight bash %}
https://graph.threads.net/v1.0/${postId}/insights?metric=likes,replies,views&access_token=zzz
{% endhighlight %}

Here’s the full code for the secondary widget:

[Secondary Widget Code](https://gist.github.com/os11k/583b8513b8abe1aa902c3d05f90ac8f7)

And that’s it! After following these steps, you should have a working Threads widget.

