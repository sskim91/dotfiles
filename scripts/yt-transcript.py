#!/usr/bin/env python3
"""YouTube 트랜스크립트 다운로드 스크립트.

Usage:
    python yt-transcript.py <URL> [-l kr|en] [-f json|text]

Examples:
    python yt-transcript.py "https://youtu.be/abc123"
    python yt-transcript.py "https://youtube.com/watch?v=abc123" -l kr
    python yt-transcript.py "https://youtu.be/abc123" -f json
"""

import argparse
import json
import re
import sys

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    """YouTube URL에서 video ID 추출."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    print(f"Error: Invalid YouTube URL: {url}", file=sys.stderr)
    sys.exit(1)


def fetch_transcript(video_id: str, lang: str) -> list[dict]:
    """트랜스크립트 가져오기. lang 우선, 실패 시 대체 언어 시도."""
    ytt_api = YouTubeTranscriptApi()
    fallback = "en" if lang == "ko" else "ko"

    try:
        return ytt_api.fetch(video_id, languages=[lang, fallback])
    except Exception:
        try:
            return ytt_api.fetch(video_id, languages=[fallback, lang])
        except Exception as e:
            print(f"Error: Failed to fetch transcript: {e}", file=sys.stderr)
            sys.exit(1)


def format_timestamp(seconds: float) -> str:
    """초를 HH:MM:SS 또는 MM:SS 형식으로 변환."""
    h, remainder = divmod(int(seconds), 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def output_text(transcript: list[dict]) -> str:
    """타임스탬프 포함 텍스트 형식."""
    lines = []
    for entry in transcript:
        ts = format_timestamp(entry.start)
        lines.append(f"[{ts}] {entry.text}")
    return "\n".join(lines)


def output_json(transcript: list[dict], video_id: str) -> str:
    """JSON 형식 출력."""
    data = {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "segments": [
            {
                "start": entry.start,
                "duration": entry.duration,
                "timestamp": format_timestamp(entry.start),
                "text": entry.text,
            }
            for entry in transcript
        ],
        "full_text": " ".join(entry.text for entry in transcript),
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="YouTube 트랜스크립트 다운로드")
    parser.add_argument("url", help="YouTube URL 또는 video ID")
    parser.add_argument(
        "-l", "--lang", default="ko", choices=["ko", "kr", "en"],
        help="언어 (기본: ko)"
    )
    parser.add_argument(
        "-f", "--format", default="text", choices=["text", "json"],
        help="출력 형식 (기본: text)"
    )
    args = parser.parse_args()

    lang = "ko" if args.lang in ("ko", "kr") else args.lang
    video_id = extract_video_id(args.url)
    transcript = fetch_transcript(video_id, lang)

    if args.format == "json":
        print(output_json(transcript, video_id))
    else:
        print(output_text(transcript))


if __name__ == "__main__":
    main()
