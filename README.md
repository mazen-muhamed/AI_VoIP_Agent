# Voice Agent Latency Demo

Pipeline: caller voice → Whisper ASR → RAG (FAQ) → LLM → TTS (Chatterbox, cloned voice) → agent voice

## Run
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key
# put a ~10 second recording of your voice here:
#   demo/voice_ref.wav
python benchmark.py --voice voice_ref.wav
```
A GPU is strongly recommended (Colab T4 is enough). On CPU the numbers will be much higher.

## What it does
1. Loads Whisper, the embedding model and Chatterbox once (load time printed separately).
2. Does one **warm-up run** (the first run is slow, that's normal) and reports it as "cold".
3. Runs 5 questions (2 short, 3 long) from `questions.json`. If `audio/<id>.wav` doesn't exist it is synthesized with the cloned voice; drop real recordings there for realistic ASR numbers.
4. No dataset: RAG uses the small `faq.json`.
5. Writes `results.md`, `results.json` and the agent replies in `output/`.

## Metrics
`time_to_first_audio_s = asr + rag + llm_first_sentence + tts_first_sentence` is what the caller actually waits.
`time_non_streaming_s` is the same pipeline without streaming, for comparison.
