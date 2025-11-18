---
layout: post
title: "Add AI Voice Agent to FreeSWITCH in 30 Minutes"
date: 2025-11-18 10:00:00 +0200
categories: jekyll update
comments: true
image: /assets/ai.png
---

### Overview

Today I'll explain how to connect your PBX to a real AI agent from ElevenLabs or any other AI agents that can communicate via WebSockets. We'll focus on ElevenLabs, and our WebSocket server is designed to use ElevenLabs, but it can be easily adjusted for any other AI provider.

**Architecture:** End users registered to FreeSWITCH make outbound calls. FreeSWITCH connects to a local WebSocket server, which then connects to the ElevenLabs AI agent.

At the end of this setup, any user registered in FreeSWITCH will be able to dial 9999 and the call will be connected to an ElevenLabs AI agent.

We'll use `mod_audio_stream` as the FreeSWITCH module that communicates with ElevenLabs. Note that the version I'm using (1.0.3) is not open source and is limited to 10 licenses.

If you have another PBX like Asterisk, you can configure a SIP trunk between Asterisk and this setup, then route the necessary calls to FreeSWITCH and from there to ElevenLabs.

If needed, you can also get a real phone number, set up routing, and connect it to your FreeSWITCH instance, which then routes to ElevenLabs.

All of this is beyond this short manual. Here I'll just explain how to route a call from FreeSWITCH to an ElevenLabs AI agent using WebSockets.

## Requirements

You'll need an account in ElevenLabs, where you'll create or use an existing agent. For my test, I used the default public agent. Your agent should be configured for PCM 16000 Hz. You'll need to grab your Agent ID—we'll need it later.

## Installing FreeSWITCH with mod_audio_stream

I prefer a dockerized environment, and in my lab I used Docker—we'll use it extensively here.

To install FreeSWITCH, we'll use my project:

[https://github.com/os11k/freeswitch-docker-compose](https://github.com/os11k/freeswitch-docker-compose)

On your server, run the following (this will put all code in `/usr/src`):

```bash
apt-get update && apt-get upgrade -y && apt-get install docker-compose -y
cd /usr/src
git clone https://github.com/os11k/freeswitch-docker-compose.git
```

We'll need to update `docker-compose.yml` to install `mod_audio_stream`. Add `wget` to the package list and append the installation commands:

```diff
-DEBIAN_FRONTEND=noninteractive apt-get -y install git build-essential pkg-config uuid-dev zlib1g-dev libjpeg-dev libsqlite3-dev libcurl4-openssl-dev libpcre3-dev libspeexdsp-dev libldns-dev libedit-dev libtiff5-dev yasm libopus-dev libsndfile1-dev unzip libavformat-dev libswscale-dev libswresample-dev liblua5.2-dev liblua5.2-0 cmake libpq-dev unixodbc-dev autoconf automake ntpdate libxml2-dev libpq-dev libpq5 libspeex-dev &&\
+DEBIAN_FRONTEND=noninteractive apt-get -y install wget git build-essential pkg-config uuid-dev zlib1g-dev libjpeg-dev libsqlite3-dev libcurl4-openssl-dev libpcre3-dev libspeexdsp-dev libldns-dev libedit-dev libtiff5-dev yasm libopus-dev libsndfile1-dev unzip libavformat-dev libswscale-dev libswresample-dev liblua5.2-dev liblua5.2-0 cmake libpq-dev unixodbc-dev autoconf automake ntpdate libxml2-dev libpq-dev libpq5 libspeex-dev &&\
 \
 cd /usr/src/ && \
 git clone https://github.com/signalwire/libks.git && \
@@ -45,7 +45,13 @@ cp /modules.conf /usr/src/freeswitch/modules.conf && \
 ./bootstrap.sh -j && \
 ./configure && \
 make && \
-make install
+make install && \
+\
+cd /usr/src/ && \
+wget https://github.com/amigniter/mod_audio_stream/releases/download/v1.0.3/mod-audio-stream_1.0.3_amd64.deb && \
+dpkg-deb -x mod-audio-stream_1.0.3_amd64.deb /usr/src/extracted/ && \
+cp -a /usr/src/extracted/usr/lib/freeswitch/mod/mod_audio_stream.so /usr/local/freeswitch/mod/
```

For this lab, I used the vanilla config:

```bash
git clone https://github.com/signalwire/freeswitch.git
cp -a ./freeswitch/conf/vanilla ./freeswitch-docker-compose/freeswitch/conf
```

**Important:** Change the default password from `1234` in `./freeswitch-docker-compose/freeswitch/conf/vars.xml`:

```xml
<X-PRE-PROCESS cmd="set" data="default_password=YOUR_SECURE_PASSWORD"/>
```

Enable the module in `./freeswitch-docker-compose/freeswitch/conf/autoload_configs/modules.conf.xml` by adding this line before `</modules>`:

```xml
<load module="mod_audio_stream"/>
```

Add the dialplan configuration to route calls to extension 9999:

```xml
<extension name="audio_stream_9999">
  <condition field="destination_number" expression="^9999$">
    <action application="set" data="STREAM_PLAYBACK=true"/>
    <action application="set" data="STREAM_SAMPLE_RATE=16000"/>
    <action application="set" data="api_on_answer=uuid_audio_stream ${uuid} start ws://127.0.0.1:8080 mono 16k"/>
    <action application="answer"/>
    <action application="park"/>
  </condition>
</extension>
```

I added this after the `laugh break` block, so it looks like this:

```
...
    <extension name="laugh break">
      <condition field="destination_number" expression="^9386$">
        <action application="answer"/>
        <action application="sleep" data="1500"/>
        <action application="playback" data="phrase:funny_prompts"/>
        <action application="hangup"/>
      </condition>
    </extension>

<extension name="audio_stream_9999">
  <condition field="destination_number" expression="^9999$">
    <action application="set" data="STREAM_PLAYBACK=true"/>
    <action application="set" data="STREAM_SAMPLE_RATE=16000"/>
    <action application="set" data="api_on_answer=uuid_audio_stream ${uuid} start ws://127.0.0.1:8080 mono 16k"/>
    <action application="answer"/>
    <action application="park"/>
  </condition>
</extension>

    <!--
        You can place files in the default directory to get included.
    -->
...
```

Now we have FreeSWITCH with the installed module and dialplan ready.

Don't forget to restart FreeSWITCH so the dialplan is updated and `mod_audio_stream` is loaded.

It's a good idea to validate that `mod_audio_stream` is actually loaded. Since we're in a dockerized environment, run this command:

```bash
docker exec -ti freeswitch /usr/local/freeswitch/bin/fs_cli -x "module_exists mod_audio_stream"
```

It should return:

```
true
```

If `mod_audio_stream` is loaded and the dialplan is in place, let's move to the WebSocket server setup.

## Setting up the WebSocket Server

The WebSocket server is very straightforward, and I've already prepared all the code.

Clone the repository to the same machine and start it up:

```bash
git clone https://github.com/os11k/freeswitch-elevenlabs-bridge
cd freeswitch-elevenlabs-bridge
```

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your ElevenLabs Agent ID:

```
ELEVENLABS_AGENT_ID=your_actual_agent_id_here
```

Then run:

```bash
docker compose up -d --build
```

## Testing a Call with AI

At this point, you should have FreeSWITCH and the WebSocket server running. All that's left is to register to FreeSWITCH and make a test call.

During a call, you can monitor the logs:

```bash
docker logs freeswitch-elevenlabs-bridge -f
```

If everything is working correctly, you should see something like this:

```
websocket listening on port 8080
received connection from 172.19.0.1
Connected to Eleven Labs
[ElevenLabs] Non-audio response: {
  conversation_initiation_metadata_event: {
    conversation_id: 'conv_9501kac1bwyyfy297f4gjrhefyqc',
    agent_output_audio_format: 'pcm_16000',
    user_input_audio_format: 'pcm_16000'
  },
  type: 'conversation_initiation_metadata'
}
[ElevenLabs] Non-audio response: {
  agent_response_event: {
    agent_response: "Hey there, I'm Alexis from ElevenLabs support. How can I help you today?",
    event_id: 1
  },
  type: 'agent_response'
}
[ElevenLabs] Non-audio response: {
  user_transcription_event: { user_transcript: 'Hey, how are you?', event_id: 23 },
  type: 'user_transcript'
}
[ElevenLabs] Non-audio response: {
  agent_response_event: {
    agent_response: "I'm doing great, thanks for asking! And yourself? What brings you here today?\n",
    event_id: 23
  },
  type: 'agent_response'
}
```

## Conclusion

As you can see, it's not rocket science to connect FreeSWITCH to an AI agent and make actual phone calls where you can speak with AI. Obviously, this configuration is not production-ready, but rather a starting point for your adventure with FreeSWITCH and `mod_audio_stream`.