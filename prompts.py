TRANSCRIBE_PROMPT = """This is a horizontal band cropped from a page of a German family letter. It may begin or end mid-sentence.

The hand is Kurrent - the old German cursive taught before Latin script replaced it. Read it as Kurrent, not as modern German handwriting. In this hand: 'e' and 'n' are near-identical short zigzags, 'h' and 'f' differ mainly in the lower loop, long-s appears inside words, and capitals are elaborate and looped. Spelling is period spelling - 'December', 'daß', 'u.' for 'und', doubled consonants - keep it exactly as written and do not modernize.

Accuracy matters more than coverage. Transcribe only what the strokes on this image actually say. Wrap any word you are not certain of in [[double brackets]], and write [[?]] where you cannot read the text at all.

Never substitute a plausible-sounding word or phrase for one you cannot actually read. A later step re-reads your draft against the full page and can resolve a marked uncertainty, but it cannot detect an invented word that reads fluently - a confident wrong answer is far more damaging here than an admitted gap.

Output only the transcription, line by line, with no commentary and no translation."""

REVIEW_PROMPT = """The draft below is a transcription of the attached page, produced without the benefit of seeing the whole page at once.

You are correcting a draft, not re-transcribing from scratch. Using the full page image: correct misread words, resolve [[uncertain]] markers wherever the surrounding context settles them, and make names and spellings consistent across the page.

For any word the draft already renders concretely, you may confirm it, replace it with a different concrete reading, or leave it alone. You may never turn it into [[?]]. Dropping a word back to [[?]] destroys information the next step needs - if you doubt a reading but cannot better it, keep it and wrap it as [[word]].

Keep the original German - do not translate or modernize it. Preserve the line breaks. Leave [[?]] only where the draft already had one and the image does not settle it.

Output only the corrected German transcription, with no commentary.

Draft:
"""
