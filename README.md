# family-archive

Pipeline that turns scanned German family letters (Kurrent handwriting) into
translated English text.

## Pipeline

1. **preprocess** — clean scans (deskew, flatten lighting, denoise)
2. **split** — cut each page into columns/bands for transcription
3. **transcribe** — draft transcription per band (GPT / Claude)
4. **consensus** — re-read bands with multiple models, keep agreed words
5. **verify** — same-model re-read, score self-agreement
6. **cross_verify** — other-vendor re-read, score cross-agreement
7. **review** — correct the draft against the full page (Claude)
8. **translate** — German → English (Google Translate)
9. **report** — summarize coverage/agreement per document

Each step caches its output, so reruns only process what's missing.

## Setup

```bash
cp .env.example .env   # add OPENAI_API_KEY / ANTHROPIC_API_KEY
./run.sh
```

Input images go in `input/`; results land in `output/`.
