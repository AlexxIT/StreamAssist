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
