"""TIL의 로컬 Markdown 이미지를 vault 첨부 파일로 내보낸다.

계획 단계는 읽기 전용. 파일명에 원본 경로·내용 해시를 넣어 서로 다른
그림과 갱신본을 분리한다. 기존 첨부 파일은 덮거나 삭제하지 않는다.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from .tilsync import _sub_outside_code

IMAGE_SUFFIXES = {'.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.bmp'}
# Inline Markdown images, angle-bracket destinations and optional quoted titles.
_IMAGE = re.compile(
    r'!\[(?:\\.|[^\]\\])*\]\(\s*(?P<url><[^>\n]+>|(?:[^\s()]+|\([^()\n]*\))+)'
    r'(?P<title>\s+(?:"[^"\n]*"|\x27[^\x27\n]*\x27))?\s*\)'
)


@dataclass(frozen=True)
class Image:
    destination: Path
    data: bytes


def attachment_directory(wiki: Path) -> Path:
    root = wiki.resolve().parent
    config = root / '.obsidian/app.json'
    folder = json.loads(config.read_text()).get('attachmentFolderPath', 'Attachments/images') if config.exists() else 'Attachments/images'
    if not isinstance(folder, str):
        raise ValueError('attachmentFolderPath는 문자열이어야 함')
    if folder == '.' or folder.startswith('./'):
        directory = wiki / folder
    else:
        directory = root / folder
    directory = directory.resolve()
    if not directory.is_relative_to(root):
        raise ValueError('첨부 폴더가 vault 밖을 가리킴')
    return directory


def plan(body: str, source: Path, til_root: Path, wiki: Path) -> tuple[str, list[Image]]:
    images: dict[Path, Image] = {}

    def replace(match, _text):
        raw = match.group('url').removeprefix('<').removesuffix('>')
        url = urlsplit(raw)
        if url.scheme or url.netloc or not url.path:
            return match.group(0)
        path = Path(unquote(url.path))
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            return match.group(0)
        origin = (source.parent / path).resolve()
        if path.is_absolute() or not origin.is_relative_to(til_root.resolve()):
            raise ValueError(f'TIL 밖 이미지 참조: {raw}')
        data = origin.read_bytes()  # missing image: leave note and state untouched
        relative = origin.relative_to(til_root.resolve()).as_posix()
        digest = hashlib.sha256(relative.encode() + b'\0' + data).hexdigest()[:20]
        label = re.sub(r'[^a-zA-Z0-9_-]+', '-', str(Path(relative).with_suffix(''))).strip('-')[:90]
        destination = attachment_directory(wiki) / f'til-{label}-{digest}{origin.suffix.lower()}'
        if destination.exists() and destination.read_bytes() != data:
            raise ValueError(f'기존 첨부 파일 내용 충돌: {destination.name}')
        images[destination] = Image(destination, data)
        target = quote(Path(os.path.relpath(destination, wiki.resolve())).as_posix(), safe='/.-_')
        if url.fragment:
            target += '#' + url.fragment
        start, end = match.span('url')
        return match.group(0)[:start-match.start()] + target + match.group(0)[end-match.start():]

    return _sub_outside_code(body, _IMAGE, replace), list(images.values())


def copy(images: list[Image]) -> int:
    """완성된 임시 파일을 원자적으로 연결하며, 기존 파일은 덮지 않는다."""
    count = 0
    for image in images:
        dest = image.destination
        if dest.exists():
            if dest.read_bytes() != image.data:
                raise ValueError(f'기존 첨부 파일 내용 충돌: {dest.name}')
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix='.til-image-')
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(image.data)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(tmp, 0o644)
            try:
                os.link(tmp, dest)  # atomic, no overwrite even if another sync races
                count += 1
            except FileExistsError:
                if dest.read_bytes() != image.data:
                    raise ValueError(f'기존 첨부 파일 내용 충돌: {dest.name}')
        finally:
            os.unlink(tmp)
    return count
