# Voice Cloning & TTS (`f5-tts-mlx`)

Global CLI command: `voice-clone` (installed at `~/.local/bin/voice-clone`)
Project path: `/Users/neilghosh/devtools/voice`

## Available Voice Presets (`--voice` / `-v`)
- `neil`: Neil's isolated & denoised narration voice (`neil_clean.wav` from `Neil.m4a`)
- `tony`: Tony Greig isolated & denoised commentary voice (`tony_greig_clean.wav`)
- `bumble` / `atherton`: Mike Atherton / Bumble commentary voice from `z4IX4e1ZUHQ` (13s–26s, denoised in `atherton_clean.wav`)
- `nasser`: Nasser Hussain commentary voice from `QrpzO2NjGHg` (`nasser_clean.wav`)
- `holding`: Michael Holding commentary voice (`holding_clean.wav` from `B7yDz-HQDww`)
- `shastri`: Ravi Shastri commentary voice (`shastri_clean.wav`)
- `attenborough`: Sir David Attenborough narration voice (`attenborough_clean.wav` from `mBgek078dxQ`)
- `bear_hindi`: Bear Grylls Hindi voiceover (`bear_hindi_clean.wav` from `7VvvAEnFbQ8?t=948`, powered by AI4Bharat `IndicF5`)
- `bangla`: Native Indian Bengali narrator (`bn-IN-BashkarNeural` via `edge-tts` + 48 kHz studio mastering)
- `odia`: Native Odia studio storyteller (`odia_native_clean.wav` from IIT Madras / AI4Bharat `IndicTTS_Odia`, powered by `IndicF5`)

## Indian Language Support (AI4Bharat `IndicF5` & Native Neural TTS)
- Automatically activates whenever `--voice bear_hindi`, `--voice odia`, `--voice bangla`, `--indic`, or any Indic script (Hindi `हिन्दी`, Bengali `বাংলা`, Odia `ଓଡ଼ିଆ`, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Assamese) is passed in `--text` / `--script-file`.
- Local MLX weights & 2,545-token Indic vocabulary: `/Users/neilghosh/devtools/voice/indic_f5_mlx`

## CLI Usage (from any directory)

```bash
# Generate English speech from inline text
voice-clone --voice tony --text "Your narration text here" --output narration.wav

# Generate Hindi speech in Bear Grylls' Hindi voice (AI4Bharat IndicF5)
voice-clone --voice bear_hindi --text "पुराना लाइटहाउस तूफ़ान के सामने शांत खड़ा था।" --output hindi_narration.wav

# Generate natural native Bangla / Odia speech
voice-clone --voice bangla --text "পুরানো লাইটহাউসটি ঝড়ের সামনে নীরবে দাঁড়িয়ে ছিল।" --output bangla_out.wav
voice-clone --voice odia --text "ପୁରୁଣା ଲାଇଟହାଉସଟି ଝଡ଼ ସାମ୍ନାରେ ନୀରବରେ ଠିଆ ହୋଇଥିଲା ।" --output odia_out.wav

# Generate speech from a script file (fast mode: 16 steps + 8-bit quantization)
voice-clone --voice bumble --script-file script.txt --steps 16 -q 8 --output voiceover.wav

# Clone any custom WAV file
voice-clone --ref-audio custom.wav --ref-text "Exact words in custom.wav" --text "New script" --output out.wav
```

## Muxing Voiceover onto a Video (`ffmpeg`)

```bash
# Replace video audio with generated voiceover
ffmpeg -y -i input_video.mp4 -i narration.wav -c:v copy -map 0:v:0 -map 1:a:0 -shortest output_video.mp4
```
