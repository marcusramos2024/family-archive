DATASET_DIR = "input"
OUTPUT_DIR = "output"
PREPROCESSED = f"{OUTPUT_DIR}/preprocessed"
BANDS = f"{OUTPUT_DIR}/bands"
DRAFTS = f"{OUTPUT_DIR}/drafts"
REVIEWED = f"{OUTPUT_DIR}/reviewed"
TRANSLATED = f"{OUTPUT_DIR}/translated"
SECOND_OPINION = f"{OUTPUT_DIR}/second_opinion"
METRICS = f"{OUTPUT_DIR}/metrics"

GPT_MODEL = "gpt-5.6-sol"
CLAUDE_MODEL = "claude-opus-4-8"
WORKERS = 8

TRANSCRIBE_VENDOR = "anthropic"  # "anthropic" | "openai"

GPT_REASONING = {"effort": "medium"}
TRANSCRIBE_TIMEOUT = 300.0
BAND_HEIGHT = 500
BAND_UPSCALE = 2

VERIFY_BANDS = 1
VERIFY_AGREE = 70

CROSS_BANDS = 2
CROSS_MODEL = "claude-sonnet-5"

CONSENSUS_MODELS = ["claude-opus-4-8", "claude-sonnet-5", "claude-opus-4-8",
                    "claude-sonnet-5", "claude-opus-4-8"]
CONSENSUS_MIN = 2
