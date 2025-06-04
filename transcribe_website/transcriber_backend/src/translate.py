from typing import Literal

from deep_translator import GoogleTranslator
from loguru import logger
from whisperx.types import AlignedTranscriptionResult


def translate_result(
    result: AlignedTranscriptionResult,
    to_language: Literal["de", "en"],
    # pyrefly: ignore
) -> AlignedTranscriptionResult:
    """TODO"""


texts = [
    "Die alte Freundin kam gestern zu Besuch.",
    # "Die Lehrerin sagte, dass die Schüler schlecht seien.",
    # "Er hat seinen Freund gestern nicht gesehen.",
    # "Er ist nicht hier, weil er krank ist.",
    # "Der Mann sah den Dieb mit dem Fernglas.",
]
for text in texts:
    logger.info(f"Source text: {text}")
    for translator in [
        GoogleTranslator("auto", "en"),
    ]:
        translated = translator.translate_batch([text])
        logger.info(f"{translator.__class__.__name__}: {translated[0]}")


# from langdetect import detect
# >>> from langdetect import detect
# >>> detect("War doesn't show who's right, just who's left.")
# 'en'
# >>> detect("Ein, zwei, drei, vier")
# 'de'

# TODO Wrap in a function to be able to reuse it
# Convert all sentences from segments into target language
# TODO Only convert if detected language is not the same as target?
