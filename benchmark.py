"""
Voice Agent latency benchmark:  caller voice -> Whisper ASR -> RAG -> LLM -> TTS (Chatterbox, cloned voice)

Measures, per question:
  asr_s            : audio file -> full transcript
  rag_s            : embed query + retrieve top-k FAQ entries
  llm_ttft_s       : request sent -> first token from LLM
  llm_first_sent_s : request sent -> first complete sentence (this is what TTS can start on)
  tts_first_s      : first sentence text -> audio generated
  time_to_first_audio_s = asr + rag + llm_first_sent + tts_first   <- the number the caller feels
  llm_total_s, tts_full_s : for the non-streaming comparison

Usage:
  export ANTHROPIC_API_KEY=...
  python benchmark.py --voice voice_ref.wav
"""
import argparse
import json
import os
import re
import statistics
import time
from pathlib import Path

import numpy as np
import torch
import torchaudio

HERE = Path(__file__).parent
SENT_END = re.compile(r"[.!?؟\n]")
SYSTEM = (
    "انت مساعد صوتي لخدمة عملاء شركة توصيل. رد بالعربي باللهجة المصرية بجمل قصيرة وواضحة "
    "من غير رموز أو قوائم، واعتمد بس على المعلومات المرفقة. لو المعلومة مش موجودة قول إنك هتحول العميل لموظف."
)


def now():
    return time.perf_counter()


def load_models(args):
    from faster_whisper import WhisperModel
    from sentence_transformers import SentenceTransformer
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute = "float16" if device == "cuda" else "int8"
    t = now()
    asr = WhisperModel(args.whisper, device=device, compute_type=compute)
    emb = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device=device)
    tts = ChatterboxMultilingualTTS.from_pretrained(device=device)
    print(f"[load] models loaded in {now() - t:.1f}s on {device}")
    return asr, emb, tts


def build_index(emb):
    faq = json.loads((HERE / "faq.json").read_text(encoding="utf-8"))
    vecs = emb.encode([f"{x['q']} {x['a']}" for x in faq], normalize_embeddings=True)
    return faq, vecs


def retrieve(emb, faq, vecs, query, k=3):
    qv = emb.encode([query], normalize_embeddings=True)[0]
    top = np.argsort(-(vecs @ qv))[:k]
    return "\n".join(f"- {faq[i]['q']}: {faq[i]['a']}" for i in top)


def synth(tts, text, voice, lang):
    return tts.generate(text, language_id=lang, audio_prompt_path=voice)


def ensure_question_audio(tts, questions, voice, lang):
    """Questions need to be audio for Whisper. If audio/<id>.wav is missing, synthesize it (not timed)."""
    (HERE / "audio").mkdir(exist_ok=True)
    for q in questions:
        p = HERE / "audio" / f"{q['id']}.wav"
        if not p.exists():
            print(f"[prep] no recording for {q['id']}, synthesizing it with the cloned voice")
            torchaudio.save(str(p), synth(tts, q["text"], voice, lang).cpu(), tts.sr)
        q["audio"] = str(p)


def run_once(models, index, q, voice, lang, llm_model):
    import anthropic

    asr, emb, tts = models
    faq, vecs = index
    r = {"id": q["id"], "type": q["type"]}

    t0 = now()
    segs, _ = asr.transcribe(q["audio"], language=lang)
    transcript = " ".join(s.text for s in segs).strip()  # generator: consumed inside the timing
    r["asr_s"] = now() - t0

    t0 = now()
    context = retrieve(emb, faq, vecs, transcript)
    r["rag_s"] = now() - t0

    client = anthropic.Anthropic()
    t0 = now()
    text, first_sentence = "", None
    r["llm_ttft_s"] = None
    with client.messages.stream(
        model=llm_model,
        max_tokens=300,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"معلومات الشركة:\n{context}\n\nسؤال العميل: {transcript}"}],
    ) as stream:
        for chunk in stream.text_stream:
            if r["llm_ttft_s"] is None:
                r["llm_ttft_s"] = now() - t0
            text += chunk
            if first_sentence is None and SENT_END.search(text):
                m = SENT_END.search(text)
                first_sentence = text[: m.end()].strip()
                r["llm_first_sent_s"] = now() - t0
    r["llm_total_s"] = now() - t0
    first_sentence = first_sentence or text
    r.setdefault("llm_first_sent_s", r["llm_total_s"])

    t0 = now()
    synth(tts, first_sentence, voice, lang)
    r["tts_first_s"] = now() - t0

    t0 = now()
    wav = synth(tts, text, voice, lang)
    r["tts_full_s"] = now() - t0
    out = HERE / "output"
    out.mkdir(exist_ok=True)
    torchaudio.save(str(out / f"{q['id']}_reply.wav"), wav.cpu(), tts.sr)

    r["time_to_first_audio_s"] = r["asr_s"] + r["rag_s"] + r["llm_first_sent_s"] + r["tts_first_s"]
    r["time_non_streaming_s"] = r["asr_s"] + r["rag_s"] + r["llm_total_s"] + r["tts_full_s"]
    r["transcript"], r["reply"] = transcript, text
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default=str(HERE / "voice_ref.wav"), help="~10s WAV of the voice to clone")
    ap.add_argument("--whisper", default="large-v3")
    ap.add_argument("--llm", default="claude-haiku-5-5")
    ap.add_argument("--lang", default="ar")
    args = ap.parse_args()

    if not Path(args.voice).exists():
        raise SystemExit(f"Voice sample not found: {args.voice} (put your 10s .wav there)")
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))

    models = load_models(args)
    index = build_index(models[1])
    ensure_question_audio(models[2], questions, args.voice, args.lang)

    print("[warm-up] first run is slow (model init / cache) - reported separately")
    cold = run_once(models, index, questions[0], args.voice, args.lang, args.llm)
    print(f"[warm-up] time_to_first_audio = {cold['time_to_first_audio_s']:.2f}s (cold)")

    results = [run_once(models, index, q, args.voice, args.lang, args.llm) for q in questions]

    cols = ["asr_s", "rag_s", "llm_ttft_s", "llm_first_sent_s", "tts_first_s", "time_to_first_audio_s", "time_non_streaming_s"]
    lines = ["| id | type | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 2)]
    for r in results:
        lines.append(f"| {r['id']} | {r['type']} | " + " | ".join(f"{r[c]:.2f}" for c in cols) + " |")
    for label, sel in [("short avg", "short"), ("long avg", "long"), ("all avg", None)]:
        rows = [r for r in results if sel is None or r["type"] == sel]
        lines.append(f"| **{label}** | | " + " | ".join(f"{statistics.mean(r[c] for r in rows):.2f}" for c in cols) + " |")
    table = "\n".join(lines)
    print("\n" + table)

    (HERE / "results.md").write_text(table + f"\n\nCold first run (time_to_first_audio): {cold['time_to_first_audio_s']:.2f}s\n", encoding="utf-8")
    (HERE / "results.json").write_text(json.dumps({"cold": cold, "runs": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nSaved results.md, results.json, output/*.wav")


if __name__ == "__main__":
    main()
