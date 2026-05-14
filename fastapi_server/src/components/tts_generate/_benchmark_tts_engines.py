"""
TTS Engine Benchmark

Benchmarks all 4 TTS engines (edge, kokoro, kitten, tiktok) on a 500-character
test text to compare generation speed. Results show relative speed with the
slowest engine as the baseline (1.00x).
"""

from __future__ import annotations

import asyncio
import time
from typing import TypedDict

from components.tts_generate import generate_audio
from schemas.tts import TTSEngine

# 500-character coherent English test text
BENCHMARK_TEXT = (
    "The quick brown fox jumps over the lazy dog, a timeless phrase that contains "
    "every letter of the alphabet at least once. This sentence has been used by "
    "typesetters and programmers for centuries to showcase fonts and test keyboard "
    "layouts. Its balanced composition makes it ideal for comparing different "
    "systems and measuring performance across various platforms and implementations. "
    "The sample text showcases the natural rhythm and flow of everyday English prose."
)


class BenchmarkResult(TypedDict):
    engine: TTSEngine
    voice_label: str
    time_seconds: float
    duration_seconds: float
    relative_speed: float


async def benchmark_engine(engine: TTSEngine, voice_label: str, text: str) -> BenchmarkResult:
    """Benchmark a single TTS engine and return results."""
    start = time.perf_counter()
    audio_bytes, duration = await generate_audio(engine, voice_label, text)
    elapsed = time.perf_counter() - start

    # Suppress unused variable warning
    assert audio_bytes is not None

    return BenchmarkResult(
        engine=engine,
        voice_label=voice_label,
        time_seconds=elapsed,
        duration_seconds=duration,
        relative_speed=0.0,  # Will be calculated after all benchmarks
    )


async def run_benchmarks() -> list[BenchmarkResult]:
    """Run benchmarks for all 4 TTS engines sequentially."""
    # Voice labels for each engine (valid labels that should exist)
    voices: list[tuple[TTSEngine, str]] = [
        ("edge", "AriaNeural"),
        ("kokoro", "Bella"),
        ("kitten", "Jasper"),
        ("tiktok", "US Female 1"),
    ]

    # Run engines sequentially to get accurate timing
    results: list[BenchmarkResult] = []
    for engine, voice in voices:
        result = await benchmark_engine(engine, voice, BENCHMARK_TEXT)
        results.append(result)

    # Find the slowest engine (longest time)
    slowest_time = max(r["time_seconds"] for r in results)

    # Calculate relative speed compared to slowest engine
    for result in results:
        result["relative_speed"] = slowest_time / result["time_seconds"]

    return results


def print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark results as a formatted table."""
    # Sort by engine name for consistent output
    results_sorted = sorted(results, key=lambda r: r["engine"])

    print("TTS Engine Benchmark (500 characters)")
    print("=" * 46)
    print(f"{'Engine':<10} {'Time (s)':<12} {'Relative Speed':<16}")
    print("(slowest = 1.00x)")
    print("-" * 46)

    for result in results_sorted:
        print(f"{result['engine']:<10} {result['time_seconds']:<12.2f} {result['relative_speed']:<16.2f}x")


if __name__ == "__main__":
    results = asyncio.run(run_benchmarks())
    print_results(results)
