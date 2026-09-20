#!/usr/bin/env python3
"""북스캔 PDF의 페이지 누락을 인쇄된 쪽번호(folio) 기준으로 점검한다.

원리: offset = folio - PDF페이지번호. 스캔에서 페이지가 빠지면 offset이 계단식으로 증가한다.
OCR 오독에 견디도록 개별 페이지가 아니라 offset의 "구간"을 추적한다.

의존: poppler (pdftotext, pdfinfo). 표준 라이브러리만 사용.

사용:
    bookscan_check.py [--json] [--min-dense N] FILE.pdf [FILE.pdf ...]
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter

# 쪽번호 후보: 앞뒤가 숫자/구두점이 아닌 1~4자리 정수 (IP·버전·소수점 제외용)
DIGIT = re.compile(r'(?<![\d.,\-/:])(\d{1,4})(?![\d.,\-/:])')

# 장/부/부록 도비라 표식. OCR이 깨지는 경우가 많아 느슨하게 잡는다.
DIVIDER = re.compile(
    r'(C\s?[HlIㅔ]\s?A\s?[PE]\s?T\s?[EㅌF]\s?R|P\s?A\s?R\s?[TI]\b|APPEND'
    r'|부\s*록|찾아보기|색인|에필로그|프롤로그'
    r'|^\s*\d{1,2}\s*[장부]\s|^\s*\d{1,2}\s+\S{2,12}\s*$)',
    re.MULTILINE | re.IGNORECASE)

OFFSET_WINDOW = 15   # 지배 offset 기준 ±범위 밖의 숫자는 쪽번호 후보에서 제외
MIN_RUN = 3          # 한 offset 구간으로 인정할 최소 확정 페이지 수


def pdf_pages(path):
    r = subprocess.run(['pdfinfo', path], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f'pdfinfo 실패: {path}')
    return int(r.stdout.decode('utf-8', 'replace').split('Pages:')[1].split()[0])


def pages_text(path):
    r = subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True)
    return r.stdout.decode('utf-8', 'replace').split('\f')


def folio_candidates(page, limit):
    """머리말/꼬리말(첫 3줄 + 끝 3줄)에서만 쪽번호 후보를 뽑는다."""
    lines = [l for l in page.split('\n') if l.strip()]
    out = set()
    for line in lines[:3] + lines[-3:]:
        for m in DIGIT.finditer(unicodedata.normalize('NFKC', line)):
            v = int(m.group(1))
            if 1 <= v <= limit + 60:
                out.add(v)
    return out


def segment(hits, window=MIN_RUN):
    """(page, {offsets}) 목록을 offset이 일정한 구간들로 자른다.

    새 offset은 뒤따르는 window개 페이지가 동의할 때만 채택한다. 단발 오독은 건너뛴다.
    """
    segs, cur, i = [], None, 0
    while i < len(hits):
        p, offs = hits[i]
        if cur is not None and cur[2] in offs:
            cur[1], cur[3] = p, cur[3] + 1
            i += 1
            continue
        chosen = None
        for o in sorted(offs, key=lambda x: abs(x - (cur[2] if cur else x))):
            if sum(1 for _, o2 in hits[i:i + window + 3] if o in o2) >= window:
                chosen = o
                break
        if chosen is None:
            i += 1
            continue
        if cur is not None and chosen == cur[2]:
            cur[1], cur[3] = p, cur[3] + 1
        else:
            cur = [p, p, chosen, 1]
            segs.append(cur)
        i += 1
    return [s for s in segs if s[3] >= window]


def analyze(path, min_dense=700):
    total = pdf_pages(path)
    raw = pages_text(path)[:total]

    compact = [len(re.sub(r'\s+', '', unicodedata.normalize('NFKC', p))) for p in raw]
    no_text = [i for i, c in enumerate(compact, 1) if c == 0]

    # 꼬리쪽 무텍스트 구간은 folio 추적 대상에서 제외하되 별도로 보고한다
    work = list(raw)
    while work and not work[-1].strip():
        work.pop()
    n = len(work)
    if n == 0:
        raise RuntimeError(f'텍스트층이 전혀 없다 (OCR 미적용): {path}')

    cands = [folio_candidates(p, n) for p in work]

    hist = Counter()
    for i, cs in enumerate(cands, 1):
        for c in cs:
            hist[c - i] += 1
    dominant = hist.most_common(1)[0][0]
    allowed = set(range(dominant - OFFSET_WINDOW, dominant + OFFSET_WINDOW + 1))

    hits = []
    for i, cs in enumerate(cands, 1):
        offs = {o for o in allowed if i + o in cs and i + o >= 1}
        if offs:
            hits.append((i, offs))
    segs = segment(hits)

    # 앞뒤 구간의 offset이 같은 짧은 중간 구간은 오독으로 보고 버린다
    changed = True
    while changed and len(segs) >= 3:
        changed = False
        for k in range(1, len(segs) - 1):
            if segs[k - 1][2] == segs[k + 1][2] and segs[k][3] < 12:
                segs.pop(k)
                changed = True
                break
    # 로마자 쪽번호를 쓰는 앞머리 구간 제거
    while len(segs) > 1 and segs[0][3] < 12 and segs[0][1] < max(12, n * 0.06):
        segs.pop(0)

    # --- 검사 1: offset 불연속 구간의 성격 판정 ---
    gaps = []
    for a, b in zip(segs, segs[1:]):
        delta = b[2] - a[2]
        if delta <= 0:
            continue
        win = []
        for p in range(a[1], b[0] + 1):
            head = '\n'.join([l for l in work[p - 1].split('\n') if l.strip()][:5])
            body = unicodedata.normalize('NFKC', work[p - 1])[:400]
            win.append({'page': p, 'chars': compact[p - 1],
                        'divider': bool(DIVIDER.search(head) or DIVIDER.search(body))})
        # 앞 앵커를 뺀 나머지가 전부 조밀한 본문이고 도비라가 없으면 본문 손실 의심
        rest = win[1:]
        suspect = bool(rest) and all(w['chars'] >= min_dense and not w['divider'] for w in rest)
        gaps.append({'pdf': [a[1], b[0]], 'folio': [a[1] + a[2], b[0] + b[2]],
                     'missing': delta, 'suspect': suspect, 'window': win})

    # --- 검사 2: 인접 본문 페이지 간 쪽번호 점프 직접 탐색 ---
    folio = {}
    for i, cs in enumerate(cands, 1):
        near = [c for c in cs if abs((c - i) - dominant) <= OFFSET_WINDOW]
        if len(near) == 1:            # 후보가 하나뿐일 때만 신뢰
            folio[i] = near[0]
    jumps = []
    for p in sorted(folio):
        if p + 1 in folio and folio[p + 1] - folio[p] >= 2 \
                and compact[p - 1] >= min_dense and compact[p] >= min_dense:
            jumps.append({'pdf': [p, p + 1], 'folio': [folio[p], folio[p + 1]],
                          'delta': folio[p + 1] - folio[p]})

    runs = []
    for p in no_text:
        if runs and p == runs[-1][1] + 1:
            runs[-1][1] = p
        else:
            runs.append([p, p])

    return {
        'file': path.split('/')[-1],
        'total_pages': total,
        'ocr_pages': n,
        'dominant_offset': dominant,
        'folio_range': [segs[0][0] + segs[0][2], segs[-1][1] + segs[-1][2]] if segs else None,
        'segments': [[s[0], s[1], s[2]] for s in segs],
        'gaps': gaps,
        'jumps': jumps,
        'no_text_runs': runs,
        'no_text_count': len(no_text),
    }


def render(r):
    print('=' * 72)
    print(f"{r['file']}  ({r['total_pages']}p, folio {r['folio_range']})")
    if r['ocr_pages'] != r['total_pages']:
        print(f"  ! 뒤쪽 {r['total_pages'] - r['ocr_pages']}p 에 OCR 텍스트층 없음 — folio 대조 불가")
    if r['no_text_runs']:
        runs = ', '.join(f'{a}-{b}' if a != b else str(a) for a, b in r['no_text_runs'])
        print(f"  텍스트 없는 페이지 {r['no_text_count']}개: {runs}")

    if not r['gaps']:
        print('  [검사1] folio 불연속 없음')
    for g in r['gaps']:
        tag = '>>> 본문 손실 의심 — 육안 확인 필요' if g['suspect'] else '공백/도비라 구간'
        print(f"  [검사1] folio {g['folio'][0]}→{g['folio'][1]} "
              f"(pdf {g['pdf'][0]}~{g['pdf'][1]}, -{g['missing']}p)  {tag}")
        if g['suspect']:
            for w in g['window']:
                print(f"          p{w['page']}: chars={w['chars']} divider={w['divider']}")

    if not r['jumps']:
        print('  [검사2] 인접 본문 페이지 간 쪽번호 점프 없음')
    for j in r['jumps']:
        print(f"  [검사2] pdf {j['pdf'][0]}→{j['pdf'][1]}: folio {j['folio'][0]}→{j['folio'][1]} "
              f"(+{j['delta']})  — 육안 확인 필요")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--json', action='store_true', help='JSON으로 출력')
    ap.add_argument('--min-dense', type=int, default=700,
                    help='본문 페이지로 볼 최소 글자 수 (기본 700)')
    args = ap.parse_args()

    out = []
    for f in args.files:
        try:
            out.append(analyze(f, args.min_dense))
        except Exception as e:                      # noqa: BLE001
            out.append({'file': f, 'error': str(e)})

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    for r in out:
        if 'error' in r:
            print('=' * 72)
            print(f"{r['file']}: ERROR {r['error']}")
        else:
            render(r)


if __name__ == '__main__':
    sys.exit(main())
