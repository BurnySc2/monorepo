# https://github.com/m-bain/whisperX
import time

import whisperx
from loguru import logger

device = "cpu"
audio_file = "test/Eclypxe_-_Black_Roses_ft_Annamarie_Rosanio_Copyright_Free_Music.mp3"
batch_size = 4  # reduce if low on GPU mem
compute_type = "int8"  # change to "int8" if low on GPU mem (may reduce accuracy)

# 1. Transcribe with original whisper (batched)
# model = whisperx.load_model("base", device, compute_type=compute_type)

# save model to local path (optional)
model_dir = "whisper_models"
model = whisperx.load_model("medium", device, compute_type=compute_type, download_root=model_dir)

audio = whisperx.load_audio(audio_file)
t0 = time.time()
result = model.transcribe(audio, batch_size=batch_size)
# result = model.transcribe(audio, batch_size=batch_size, language="en")
logger.info(result["segments"])  # before alignment

# delete model if low on GPU resources
# import gc; gc.collect(); torch.cuda.empty_cache(); del model

# 2. Align whisper output
t1 = time.time()
model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
t2 = time.time()
result2 = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
t3 = time.time()

logger.info(f"Transcribing took {t1-t0:.2f}\nLoading align model took {t2-t1:.2f}\nAlignin took {t3-t2:.2f}")

logger.info(result["segments"])  # after alignment
1
