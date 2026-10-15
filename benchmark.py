"""
Voice Agent latency benchmark (demo / simulation, no external API needed)
caller voice -> Whisper ASR -> RAG (FAQ) -> local open-source LLM -> TTS (Chatterbox, cloned voice)

Measures, per question:
  asr_s            : audio file -> full transcript (includes reading the file)
  rag_s            : embed query + retrieve top-k FAQ entries
  llm_ttft_s       : request sent -> first token from LLM
  llm_first_sent_s : request sent -> first complete sentence (TTS can start on this)
  tts_first_s      : first sentence text -> audio generated
  time_to_first_audio_s = asr + rag + llm_first_sent + tts_first   <- what the caller feels
  llm_total_s, tts_full_s : used for the non-streaming comparison

Usage:
  python benchmark.py --voice voice_ref.wav
  python benchmark.py --voice voice_ref.wav --llm Qwen/Qwen2.5-3B-Instruct
"""
import argparse
import json
import re
import statistics
import time
from pathlib import Path
from threading import Thread

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


def load_audio(path, sr=16000):
    import librosa

    audio, _ = librosa.load(path, sr=sr, mono=True)
    return audio


def load_models(args):
    from faster_whisper import WhisperModel
    from sentence_transformers import SentenceTransformer
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute = "float16" if device == "cuda" else "int8"
    t = now()
    asr = WhisperModel(args.whisper, device=device, compute_type=compute)
    emb = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device=device)
    tts = ChatterboxMultilingualTTS.from_pretrained(device=device)
    tok = AutoTokenizer.from_pretrained(args.llm)
    llm = AutoModelForCausalLM.from_pretrained(
        args.llm, dtype=torch.float16 if device == "cuda" else torch.float32
    ).to(device)
    llm.eval()
    print(f"[load] models loaded in {now() - t:.1f}s on {device} (LLM: {args.llm})")
    return asr, emb, tts, (tok, llm)


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


def run_once(models, index, q, voice, lang, max_new_tokens):
    from transformers import TextIteratorStreamer

    asr, emb, tts, (tok, llm) = models
    faq, vecs = index
    r = {"id": q["id"], "type": q["type"]}

    # ---- ASR ----
    t0 = now()
    segs, _ = asr.transcribe(load_audio(q["audio"]), language=lang)
    transcript = " ".join(s.text for s in segs).strip()  # generator: consumed inside the timing
    r["asr_s"] = now() - t0

    # ---- RAG ----
    t0 = now()
    context = retrieve(emb, faq, vecs, transcript)
    r["rag_s"] = now() - t0

    # ---- LLM (local, streaming) ----
    t0 = now()
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"معلومات الشركة:\n{context}\n\nسؤال العميل: {transcript}"},
    ]
    prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt").to(llm.device)
    streamer = TextIteratorStreamer(tok, skip_prompt=True, skip_special_tokens=True)
    thread = Thread(
        target=llm.generate,
        kwargs=dict(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                    pad_token_id=tok.eos_token_id, streamer=streamer),
    )
    thread.start()
    text, first_sentence = "", None
    r["llm_ttft_s"] = None
    for chunk in streamer:
        if not chunk:
            continue
        if r["llm_ttft_s"] is None:
            r["llm_ttft_s"] = now() - t0
        text += chunk
        if first_sentence is None:
            m = SENT_END.search(text)
            if m:
                first_sentence = text[: m.end()].strip()
                r["llm_first_sent_s"] = now() - t0
    thread.join()
    r["llm_total_s"] = now() - t0
    text = text.strip()
    first_sentence = first_sentence or text
    r.setdefault("llm_first_sent_s", r["llm_total_s"])
    if r["llm_ttft_s"] is None:
        r["llm_ttft_s"] = r["llm_total_s"]

    # ---- TTS: first sentence (streaming case) ----
    t0 = now()
    synth(tts, first_sentence, voice, lang)
    r["tts_first_s"] = now() - t0

    # ---- TTS: full reply (non-streaming case) ----
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
    ap.add_argument("--llm", default="Qwen/Qwen2.5-1.5B-Instruct", help="local HF chat model (no API key needed)")
    ap.add_argument("--max-new-tokens", type=int, default=120)
    ap.add_argument("--lang", default="ar")
    args = ap.parse_args()

    if not Path(args.voice).exists():
        raise SystemExit(f"Voice sample not found: {args.voice} (put your 10s .wav there)")
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))

    models = load_models(args)
    index = build_index(models[1])
    ensure_question_audio(models[2], questions, args.voice, args.lang)

    print("[warm-up] first run is slow (model init / cache) - reported separately")
    cold = run_once(models, index, questions[0], args.voice, args.lang, args.max_new_tokens)
    print(f"[warm-up] time_to_first_audio = {cold['time_to_first_audio_s']:.2f}s (cold)")

    results = [run_once(models, index, q, args.voice, args.lang, args.max_new_tokens) for q in questions]

    cols = ["asr_s", "rag_s", "llm_ttft_s", "llm_first_sent_s", "tts_first_s", "time_to_first_audio_s", "time_non_streaming_s"]
    lines = ["| id | type | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 2)]
    for r in results:
        lines.append(f"| {r['id']} | {r['type']} | " + " | ".join(f"{r[c]:.2f}" for c in cols) + " |")
    for label, sel in [("short avg", "short"), ("long avg", "long"), ("all avg", None)]:
        rows = [r for r in results if sel is None or r["type"] == sel]
        lines.append(f"| **{label}** | | " + " | ".join(f"{statistics.mean(r[c] for r in rows):.2f}" for c in cols) + " |")
    table = "\n".join(lines)
    print("\n" + table)

    note = f"\n\nLLM: {args.llm} (local). Cold first run (time_to_first_audio): {cold['time_to_first_audio_s']:.2f}s\n"
    (HERE / "results.md").write_text(table + note, encoding="utf-8")
    (HERE / "results.json").write_text(json.dumps({"cold": cold, "runs": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nSaved results.md, results.json, output/*.wav")


if __name__ == "__main__":
    main()
