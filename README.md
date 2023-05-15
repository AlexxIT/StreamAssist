# Stream Assist

[Home Assistant](https://www.home-assistant.io/) custom component that allows you to turn almost [any camera](https://www.home-assistant.io/integrations/#camera) and almost [any speaker](https://www.home-assistant.io/integrations/#media-player) into a local [voice assistant](https://www.home-assistant.io/integrations/#voice).

Component will use:

- [Stream](https://www.home-assistant.io/integrations/stream/) integration for receiving audio from camera (RTSP/HTTP/RTMP) and automatic transcoding of audio codec into a format suitable for Speech-to-Text (STT)
- [Voice Activity Detector](https://github.com/wiseman/py-webrtcvad) (VAD) library for auto detect the beginning and end of speech
- [Assist pipeline](https://www.home-assistant.io/integrations/assist_pipeline/) integration for run: Speech-to-Text (STT) => Natural Language Processing (NLP) => Text-to-Speech (TTS)
- Almost any [Media player](https://www.home-assistant.io/integrations/#media-player) for play audio respose from Text-to-Speech (TTS)

Assist pipeline can use:

- [Whisper](https://github.com/home-assistant/addons) core Add-on for local STT
- [Pipper](https://github.com/home-assistant/addons) core Add-on for local TTS
- [Faster Whisper](https://github.com/AlexxIT/FasterWhisper) custom integration for local STT
- [Google Translate](https://www.home-assistant.io/integrations/google_translate/) core integration for cloud TTS

**Important.** Component does not support **wake** word. The recognition process must be started manually or by automation (remote button, motion sensor, etc).

## Installation

[HACS](https://hacs.xyz/) > Integrations > 3 dots (upper top corner) > Custom repositories > URL: `AlexxIT/StreamAssist`, Category: Integration > Add > wait > Stream Assist > Install

Or manually copy `stream_assist` folder from [latest release](https://github.com/AlexxIT/StreamAssist/releases/latest) to `/config/custom_components` folder.

## Configuration

### Config local Speech-to-Text (STT)

1. Add local Speech-to-Text Add-on  
   Settings > Add-ons > Add-on Store > Whisper > Install
2. Config STT Add-on:  
   Whisper > Configuration
3. Add STT Integration:  
   Settings > Integrations > Whisper > Configure

### Config local Text-to-Speech (TTS)
 
1. Add local Text-to-Speech Add-on  
   Settings > Add-ons > Add-on Store > Piper > Install
2. Config TTS Integration:  
   Piper > Configuration
3. Add TTS Integration:  
   Settings > Integrations > Piper > Configure

### Config cloud Text-to-Speech (TTS)

`configuration.yaml`

```yaml
tts:
  - platform: google_translate
```

### Config local Voice assistant (NLP)

1. Config Voice assistant:  
   Settings > Voice assistants > Home Assistant > Select: STT and TTS

### Config Stream Assist

1. Add **Stream Assist** Integration  
   Settings > Integrations > Add Integration > Stream Assist
2. Config **Stream Assist** Integration  
   Settings > Integrations > Stream Assist > Configure

You can select or camera entity_id as audio (MIC) source or stream URL.

You can change Voice activity detector (VAD) settings. It will wait **voice** of "VAD speech seconds" duration and **silence** after voice of "VAD silence seconds" duration. Then the text recognition (STT) will start. Maximum voice search duration - "VAD timeout seconds".

You can select Voice Assistant Pipeline for recognition process: **STT => NLP => TTS**. By default componen will use default pipeline. You can create several **Pipelines** with different settings. And several **Stream Assist** components with different settings.

You can select Pipeline end stage when processing will stops:

- You can use only **MIC => VAD** stage to know if there is a voice in the place with the camera. You don't need any pipeline in this case
- You can use only **MIC => VAD => STT** stage and process recognized text inside automation
- You can use only **MIC => VAD => STT => NLP** stage and process recognized intent inside automation
- You can use only **MIC => VAD => STT => NLP => TTS** stage and process response text or audio inside automation
- You can use all stages **MIC => VAD => STT => NLP => TTS => SND** and allow the integration to output audio to the speakers

You can select one or multiple Media players (SND) to output audio response. If your camera support two way audio you can use [WebRTC Camera](https://github.com/AlexxIT/WebRTC#stream-to-camera) custom integration to add it as Media player.

## Using

Component has MIC switch and multiple sensors - VAD, STT, NLP, TTS. There may be fewer sensors, depending on the "Pipeline end stage" setting.

You can create automations to activate the microphone, and to monitor changes in the state of the sensors and their attributes. The sensor attributes contain a lot of useful information about the results of each step of the assistant.

You can also view the pipelines running history in the Home Assistant interface:

- Settings > Voice assistants > Pipeline > 3 dots > Debug

## Tips

1. Recommended settings for Whisper:
   - Model: `small-int8` or `medium-int8`
   - Beam size: `5`

2. You can add remote Whisper/Piper installation from another server:
   - First server: Settings > Add-ons > Whisper/Piper > Configuration > Network > Select port
   - Second server: Settings > Integrations > Add integration > Wyoming Protocol > Select: first server IP, add-on port

3. Whisper supports many languages, but Piper much less. You can use Google Translate integration instead of Piper, which support many languages for TTS.

4. If your environment does not allow you to install add-ons, you can install [Faster Whisper](https://github.com/AlexxIT/FasterWhisper) custom integration for local STT
