# Stream Assist

[Home Assistant](https://www.home-assistant.io/) custom component that allows you to turn almost [any camera](https://www.home-assistant.io/integrations/#camera) and almost [any speaker](https://www.home-assistant.io/integrations/#media-player) into a local [voice assistant](https://www.home-assistant.io/integrations/#voice).

Component will use:

- [Stream](https://www.home-assistant.io/integrations/stream/) integration for receiving audio from camera (RTSP/HTTP/RTMP) and automatic transcoding of audio codec into a format suitable for Speech-to-Text (STT)
- [Assist pipeline](https://www.home-assistant.io/integrations/assist_pipeline/) integration for run: Speech-to-Text (STT) => Natural Language Processing (NLP) => Text-to-Speech (TTS)
- Almost any [Media player](https://www.home-assistant.io/integrations/#media-player) for play audio respose from Text-to-Speech (TTS)

Assist pipeline can use:

- [openWakeWord](https://github.com/home-assistant/addons) core Add-on for wake word detection
- [Whisper](https://github.com/home-assistant/addons) core Add-on for local STT
- [Piper](https://github.com/home-assistant/addons) core Add-on for local TTS
- [Faster Whisper](https://github.com/AlexxIT/FasterWhisper) custom integration for local STT
- [Google Translate](https://www.home-assistant.io/integrations/google_translate/) core integration for cloud TTS

## Installation

[HACS](https://hacs.xyz/) > Integrations > 3 dots (upper top corner) > Custom repositories > URL: `AlexxIT/StreamAssist`, Category: Integration > Add > wait > Stream Assist > Install

Or manually copy `stream_assist` folder from [latest release](https://github.com/AlexxIT/StreamAssist/releases/latest) to `/config/custom_components` folder.

## Configuration

### Config wake word detection (WAKE)

1. Add wake word detection Add-on
   Settings > Add-ons > Add-on Store > openWakeWord > Install
2. Config WAKE Add-on:  
   openWakeWord > Configuration
3. Add WAKE Integration:  
   Settings > Integrations > openWakeWord > Configure

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

### Config local Voice assistant (INTENT)

1. Config Voice assistant:  
   Settings > Voice assistants > Home Assistant > Select: STT, TTS and WAKE

### Config Stream Assist

1. Add **Stream Assist** Integration  
   Settings > Integrations > Add Integration > Stream Assist
2. Config **Stream Assist** Integration  
   Settings > Integrations > Stream Assist > Configure

You can select or camera entity_id as audio (MIC) source or stream URL.

You can select Voice Assistant Pipeline for recognition process: **WAKE => STT => NLP => TTS**. By default componen will use default pipeline. You can create several **Pipelines** with different settings. And several **Stream Assist** components with different settings.

You can select one or multiple Media players (SND) to output audio response. If your camera support two way audio you can use [WebRTC Camera](https://github.com/AlexxIT/WebRTC#stream-to-camera) custom integration to add it as Media player.

You can set STT start media for play "beep" after WAKE detection (ex: `media-source://media_source/local/beep.mp3`).

## Using

Component has MIC switch and multiple sensors - WAKE, STT, INTENT, TTS. There may be fewer sensors, depending on the Pipeline settings.

The sensor attributes contain a lot of useful information about the results of each step of the assistant.

You can also view the pipelines running history in the Home Assistant interface:

- Settings > Voice assistants > Pipeline > 3 dots > Debug

## Service

You can run pipeline as a service. Almost all settings optional. But allow you to achieve customisations that are not possible in Hass by default.

```yaml
service: stream_assist.run
data:
  stream_source: rtsp://...
  camera_entity_id: camera.xxx
  player_entity_id: media_player.xxx
  stt_start_media: media-source://media_source/local/beep.mp3
  pipeline_id: abcdefg...
  assist:
    start_stage: wake_word  # wake_word, stt, intent, tts
    end_stage: tts
    pipeline:
      conversation_language: en
      conversation_engine: homeassistant
      language: en
      name: Home Assistant
      stt_engine: stt.faster_whisper
      stt_language: en
      tts_engine: tts.google_en_com
      tts_language: en
      tts_voice: None
      wake_word_entity: wake_word.openwakeword
      wake_word_id: None
    wake_word_settings: { timeout: 5 }
    audio_settings:
      noise_suppression_level: None
      auto_gain_dbfs: None
      volume_multiplier: None
    conversation_id: None
    device_id: None
    intent_input: None
    tts_audio_output: None  # None, wav, mp3
    tts_input: None
  stream:
    file: ...
    options: {}
```

## Tips

1. Recommended settings for Whisper:
   - Model: `small-int8` or `medium-int8`
   - Beam size: `5`

2. You can add remote Whisper/Piper installation from another server:
   - First server: Settings > Add-ons > Whisper/Piper > Configuration > Network > Select port
   - Second server: Settings > Integrations > Add integration > Wyoming Protocol > Select: first server IP, add-on port

3. You can use Google Translate integration instead of Piper, which support many languages for TTS.

4. If your environment does not allow you to install add-ons, you can install [Faster Whisper](https://github.com/AlexxIT/FasterWhisper) custom integration for local STT.
