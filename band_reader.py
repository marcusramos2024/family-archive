import anthropic
from openai import OpenAI

from config import CLAUDE_MODEL, GPT_MODEL, GPT_REASONING, TRANSCRIBE_TIMEOUT, TRANSCRIBE_VENDOR
from prompts import TRANSCRIBE_PROMPT
from utils import usage_of


def band_text(image, vendor=None, model=None):
    vendor = vendor or TRANSCRIBE_VENDOR
    if vendor == "openai":
        reply = OpenAI(timeout=TRANSCRIBE_TIMEOUT, max_retries=1).responses.create(
            model=model or GPT_MODEL,
            reasoning=GPT_REASONING,
            input=[{"role": "user", "content": [
                {"type": "input_text", "text": TRANSCRIBE_PROMPT},
                {"type": "input_image", "image_url": f"data:image/png;base64,{image}"},
            ]}],
        )
        return reply.output_text, usage_of(reply)

    reply = anthropic.Anthropic().messages.create(
        model=model or CLAUDE_MODEL, max_tokens=4000,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/png", "data": image}},
            {"type": "text", "text": TRANSCRIBE_PROMPT},
        ]}],
    )
    return "".join(b.text for b in reply.content if b.type == "text"), usage_of(reply)
