#!/usr/bin/env python3
"""Semantic Linker — Obsidian vault 노트 간 의미적 유사도 기반 연결 후보 추출.

Usage:
    python semantic-linker.py [--threshold 0.75] [--top-k 3] [--cache-only]

독립 실행: 임베딩 + 유사도 계산 + 후보 JSON 출력
vault-linter 통합: /vault-linter --semantic 으로 Claude Code가 호출
"""

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import requests

VAULT = os.environ.get(
    "VAULT",
    os.path.expanduser(
        "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note"
    ),
)
CACHE_PATH = Path(__file__).parent / "embeddings-cache.json"
OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "bge-m3"

EXCLUDE_DIRS = {"99.Template", ".obsidian"}
EXCLUDE_PREFIXES = ("Vault-Lint-Report", "Vault-Semantic-Report")


def load_notes() -> dict[str, dict]:
    """Vault에서 노트를 로드. {nfc_name: {path, content, hash, tags, links}}"""
    notes = {}
    vault = Path(VAULT)
    for md in vault.rglob("*.md"):
        if any(ex in md.parts for ex in EXCLUDE_DIRS):
            continue
        if any(md.name.startswith(p) for p in EXCLUDE_PREFIXES):
            continue

        name = unicodedata.normalize("NFC", md.stem)
        try:
            content = md.read_text(encoding="utf-8")
        except Exception:
            continue

        content_hash = hashlib.md5(content.encode()).hexdigest()

        # Extract tags from frontmatter
        tags = []
        in_fm, in_tags = False, False
        for line in content.split("\n"):
            if line.strip() == "---" and not in_fm:
                in_fm = True
                continue
            if line.strip() == "---" and in_fm:
                break
            if in_fm and line.startswith("tags:"):
                in_tags = True
                continue
            if in_fm and in_tags and re.match(r"^[^ ]", line):
                in_tags = False
            if in_fm and in_tags and line.strip().startswith("- "):
                tag = line.strip()[2:].strip()
                if tag:
                    tags.append(tag)

        # Extract existing wikilinks (body + related_notes)
        links = set()
        for m in re.findall(r"\[\[([^|\]]+)", content):
            links.add(unicodedata.normalize("NFC", m))

        notes[name] = {
            "path": str(md),
            "content": content,
            "hash": content_hash,
            "tags": tags,
            "links": links,
        }

    return notes


def load_cache() -> dict:
    """임베딩 캐시 로드. {name: {hash, embedding}}"""
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache: dict) -> None:
    """임베딩 캐시 저장."""
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False), encoding="utf-8"
    )


def get_embedding(text: str) -> list[float]:
    """ollama bge-m3로 텍스트 임베딩 생성."""
    text = text[:8000]
    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "input": text},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"][0]


def build_embeddings(notes: dict[str, dict]) -> tuple[dict, int, int]:
    """모든 노트의 임베딩을 생성/캐시. Returns (cache, new_count, cached_count)."""
    cache = load_cache()
    new_count = 0
    cached_count = 0

    for name, note in notes.items():
        if name in cache and cache[name]["hash"] == note["hash"]:
            cached_count += 1
            continue

        try:
            embedding = get_embedding(note["content"])
            cache[name] = {"hash": note["hash"], "embedding": embedding}
            new_count += 1
            if new_count % 50 == 0:
                print(f"  Embedded {new_count} new notes...", file=sys.stderr)
                save_cache(cache)
        except Exception as e:
            print(f"  WARN: Failed to embed '{name}': {e}", file=sys.stderr)
            continue

    save_cache(cache)
    print(
        f"Embeddings: {new_count} new, {cached_count} cached", file=sys.stderr
    )
    return cache, new_count, cached_count


def find_candidates(
    notes: dict[str, dict],
    cache: dict,
    threshold: float,
    top_k: int,
) -> list[dict]:
    """코사인 유사도 기반 연결 후보 추출."""
    names = [n for n in notes if n in cache]
    if not names:
        return []

    matrix = np.array([cache[n]["embedding"] for n in names])
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    matrix = matrix / norms
    similarity = matrix @ matrix.T

    seen_pairs = set()
    candidates = []

    for i, name_a in enumerate(names):
        scores = similarity[i].copy()
        scores[i] = -1
        top_indices = np.argsort(scores)[-top_k:][::-1]

        for j in top_indices:
            score = float(scores[j])
            if score < threshold:
                continue

            name_b = names[j]
            pair_key = tuple(sorted([name_a, name_b]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            if name_b in notes[name_a]["links"] or name_a in notes[name_b]["links"]:
                continue

            candidates.append({
                "note_a": name_a,
                "note_b": name_b,
                "similarity": round(score, 4),
                "path_a": notes[name_a]["path"],
                "path_b": notes[name_b]["path"],
            })

    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    return candidates


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Semantic Linker")
    parser.add_argument("--threshold", type=float, default=0.75)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Only build embeddings, skip similarity",
    )
    args = parser.parse_args()

    print("Loading notes...", file=sys.stderr)
    notes = load_notes()
    print(f"Loaded {len(notes)} notes", file=sys.stderr)

    print("Building embeddings...", file=sys.stderr)
    cache, new_count, cached_count = build_embeddings(notes)

    if args.cache_only:
        print("Cache-only mode. Done.", file=sys.stderr)
        sys.exit(0)

    print("Computing similarities...", file=sys.stderr)
    candidates = find_candidates(notes, cache, args.threshold, args.top_k)
    print(f"Found {len(candidates)} candidate pairs", file=sys.stderr)

    result = {
        "total_notes": len(notes),
        "new_embeddings": new_count,
        "cached_embeddings": cached_count,
        "candidate_pairs": candidates,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
