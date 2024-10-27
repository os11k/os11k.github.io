---
layout: post
title:  "How to Create a Widget for Meta Threads using Scriptable"
date:   2024-10-26 16:01:00 +0200
categories: jekyll update
comments: true
---

This post will be a bit different. I recently started using Meta Threads, and I saw someone complaining that Meta should create a widget for certain stats. I replied, saying it should be possible using the Scriptable app. Long story short, I decided to dive into this rabbit hole and create some widgets for Meta Threads. I’ll be creating two widgets—one for follower counts and profile visitors for today and yesterday, and a second widget to display view counts for the latest post. I’ll be using the Scriptable app to make these, which you can download for free from the iOS App Store.

<img src="{{ site.url }}/assets/threads_widget/0.jpg" alt="Diagram" style="width: 25%;">

### Step 1: Set Up the Meta App

The first thing to do is go to [Meta for Developers](https://developers.facebook.com/) and create an app.

Once you're there, the setup process is mostly "next-next-next."

Select **"I don’t want to connect a business portfolio yet."**

![Diagram]({{ site.url }}/assets/threads_widget/1.png)

Then, choose **"Access the Threads API"**.

![Diagram]({{ site.url }}/assets/threads_widget/2.png)

Enter your app name and email:

![Diagram]({{ site.url }}/assets/threads_widget/3.png)

Click **"Go to Dashboard"**.

![Diagram]({{ site.url }}/assets/threads_widget/4.png)

In the dashboard settings, continue with more "next-next-next."

![Diagram]({{ site.url }}/assets/threads_widget/5.png)

First, go to **"Access the Threads API"** and select **"threads_basic"** and **"threads_manage_insights"**—these are the bare minimum permissions needed for this project. If you want to do more, adjust your permissions accordingly.

![Diagram]({{ site.url }}/assets/threads_widget/6.png)

Then, click **"Test Use Cases"** (it should automatically show a green tick).

![Diagram]({{ site.url }}/assets/threads_widget/7.png)

Finally, click **"Finish Customization"**.

![Diagram]({{ site.url }}/assets/threads_widget/8.png)

### Step 2: Add Roles

Now, go to **"App Roles"** and then to **"Roles"**.

![Diagram]({{ site.url }}/assets/threads_widget/9.png)

Click **"Add People"** and select **"Threads Tester."** Below that, add your own user, as shown in the screenshot:

![Diagram]({{ site.url }}/assets/threads_widget/10.png)

Now, open the Threads app with that user. Go to **Settings > Account > Website Permissions > Invites** and accept the invite.

![Diagram]({{ site.url }}/assets/threads_widget/11.png)

### Step 3: Get an Access Token

Now, we need to get a token. Go to the [Facebook Developer Explorer](https://developers.facebook.com/tools/explorer/).

Select **"threads.net"** and click **"Generate Threads Access Token"**.

![Diagram]({{ site.url }}/assets/threads_widget/12.png)

When the Threads pop-up appears, just click **"Continue."**

![Diagram]({{ site.url }}/assets/threads_widget/13.png)

You’ll now see your token in the **"Access Token"** field.

![Diagram]({{ site.url }}/assets/threads_widget/14.png)

Validate that your token works by using the **"Access Token Debugger":**

[Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)

If it shows something similar to the screenshot below, then you’re good to go.

![Diagram]({{ site.url }}/assets/threads_widget/15.png)

### Step 4: Exchange for a Long-Lived Token

Now we need to exchange this short-lived token (which expires in 60 minutes) for a long-lived token that will last two months. Details are here: [Long-Lived Tokens](https://developers.facebook.com/docs/threads/get-started/long-lived-tokens/).

Run this command:
{% highlight bash %}
curl -s -X GET "https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=<THREADS_APP_SECRET>&access_token=<SHORT_LIVED_ACCESS_TOKEN>"
{% endhighlight %}

Since we’re missing `THREADS_APP_SECRET`, go to [Facebook Apps](https://developers.facebook.com/apps/?show_reminder=true), select your app, and go to **"App Settings"** > **"Basic"**. You’ll see a screen like this:

![Diagram]({{ site.url }}/assets/threads_widget/16.png)

Click **"Show"** next to **"App Secret"**.

Now use this in the `curl` command above to get your long-lived token.

Once you have the long-lived token, recheck it using the [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/).

### Step 5: Start Building the Widgets

The idea is to have two widgets—a "main" widget for followers + visitors and a "secondary" widget for the last post's view count.

- The main widget will display stats and handle token refresh, saving it in iCloud under the same filename you initially used. 
- The secondary widget will use the same token from iCloud but won’t handle token refreshes (assuming the token remains valid). This means you can’t use the secondary widget independently without adjusting the code. You can, however, copy the token refresh code from the main widget to the secondary if needed.

### Step 6: Save the Long-Lived Token to iCloud

To store the token, use this one-time Scriptable app code during your initial setup. The main widget code will handle future token refreshes and updates:

[Token Storage Script](https://gist.github.com/os11k/501d7b2be09c6bba0e734485cce28365)

Once the token is in iCloud, we’re ready to build the main widget.

### Building the Widgets

For the main widget, I’m using the following endpoints for followers and profile visitors:

**Followers:**
{% highlight bash %}
https://graph.threads.net/v1.0/me/threads_insights?metric=followers_count&access_token=zzz
{% endhighlight %}

**Profile Visitors:**
{% highlight bash %}
https://graph.threads.net/v1.0/me/threads_insights?metric=views&access_token=zzz
{% endhighlight %}

Full code for the main widget is here:

[Main Widget Code](https://gist.github.com/os11k/1f109155706ce2bef8b68ea61a324126)

The secondary widget checks the latest post, and if a post exists with stats (since reposts have no views), it displays the view count and a snippet of the post. For reposts, it shows 0.

Documentation for this setup is here:

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
