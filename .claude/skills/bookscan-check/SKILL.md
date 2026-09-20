---
name: bookscan-check
description: Check book-scanned PDFs for pages the scanner skipped, by tracking printed page numbers (folio) against PDF page index. Use when the user says "북스캔 점검", "페이지 누락 확인", "스캔 빠진 페이지", "pdf 페이지 검사", "책 스캔 확인", mentions newly scanned PDFs in their OneDrive 30_책 folder, or asks whether a scanned book is missing pages. Do NOT use for OCR quality review, PDF merging/splitting, or reading a PDF's contents (use the pdf skill).
---

# Book Scan Page-Loss Check

북스캔한 PDF에서 스캐너가 빼먹은 페이지를 찾는다. 사용자가 직접 재단·스캔한 기술서적 수십 권을
한 번에 검사하는 용도이고, 사람이 페이지를 넘겨 보는 시간을 대신한다.

## 판정 원리

`offset = 인쇄된 쪽번호(folio) − PDF 페이지 번호`

스캔이 온전하면 offset은 책 전체에서 일정하다. 페이지가 빠지면 그 지점부터 offset이 계단식으로
**증가**한다 (반대로 감소하면 중복 스캔·삽입). 개별 페이지의 OCR은 자주 깨지므로 페이지 단위가 아니라
offset **구간**을 추적한다.

## 핵심 구분: 공백면 누락 vs 본문 손실

실제 검사에서 나오는 불연속은 대부분 **장/부/부록 도비라 앞뒤의 공백면**이다. 읽는 데 지장이 없다.
사용자가 알고 싶은 건 **글씨가 있는 본문 페이지가 사라진 경우**다. 둘을 반드시 구분해서 보고한다.

전형적 패턴 — 장 마지막 본문(홀수 면) → **공백면(짝수) 누락** → 다음 장 도비라(홀수).
빠진 면 앞뒤 2~4페이지 안에 도비라나 빈 페이지가 있으면 공백면 누락이다.

## 실행

```bash
SKILL=~/.claude/skills/bookscan-check
python3 "$SKILL/scripts/bookscan_check.py" "책1.pdf" "책2.pdf" ...
```

- poppler 필요 (`pdftotext`, `pdfinfo`, 육안 확인용 `pdftoppm`). 없으면 `brew install poppler`.
- 대용량(100~300MB) 파일이 많으므로 5권 내외로 나눠 백그라운드 병렬 실행한다.
- `--json` 으로 기계 판독 출력, `--min-dense N` 으로 본문 판정 기준 글자 수 조정.

스크립트가 두 가지 검사를 함께 돌린다.

- **검사 1** — offset 불연속 구간의 성격 판정. 구간 안 모든 페이지가 조밀한 본문(기본 700자 이상)이고
  도비라 표식이 없으면 `본문 손실 의심` 으로 표시한다.
- **검사 2** — 인접한 두 PDF 페이지가 둘 다 본문인데 쪽번호가 2 이상 뛰는 경우를 직접 탐색한다.
  사용자가 말하는 "279 → 282" 형태를 그대로 구현한 것.

## 육안 확인은 생략하지 않는다

`육안 확인 필요` 로 표시된 건은 전부 렌더링해서 직접 본다. 지금까지 검사 2 후보는 **전부 OCR 오독**이었다.

```bash
pdftoppm -f 224 -l 224 -r 55 -png "책.pdf" /tmp/out   # → /tmp/out-224.png 를 Read 로 열기
bash "$SKILL/scripts/page-context.sh" "책.pdf" 222 225  # 머리말/꼬리말만 빠르게 덤프
```

판별 보조 근거: 후보 지점이 진짜 누락이라면 **그 책의 offset이 거기서부터 영구히 틀어져야 한다.**
검사 1이 해당 지점에 불연속을 보고하지 않았다면 오독일 가능성이 매우 높다.

실제로 걸러낸 오독 사례:

| 증상 | 실제 |
|---|---|
| `이것이 스프링 AI다` 224p folio 231 | 실제 **230**. 렌더링으로 확인 |
| `스프링 시큐리티 인 액션` 47p folio 25 | 실제 **26**. 머리말 좌측 숫자 오독 |
| 쪽번호가 `1n`, `1케0`, `04그.`, `330`(←339) 으로 깨짐 | 한 자리 오독. 앞뒤 offset으로 교차 확인 |

## OCR 미적용 구간

`뒤쪽 N p 에 OCR 텍스트층 없음` 이 나오면 folio 대조가 불가능한 구간이다. 페이지가 빠진 게 아니라
OCR만 안 걸린 것일 수 있으니 `pdfimages -list` 로 스캔 이미지 존재를 확인하고 구분해서 보고한다.
(실제 사례: `엘라스틱서치 실무 가이드` 708p 중 230p가 이미지만 있고 텍스트층 없음 → 재-OCR 권고)

무텍스트 구간이 책 중간이면 앞뒤 확정 페이지의 folio 차이와 PDF 페이지 수를 비교해 누락 여부를
산술로 확정할 수 있다. 맨 뒤 구간은 대조 기준이 없어 **미확인**으로 남긴다.

## 보고 형식

결론을 먼저 쓴다 — **본문이 사라진 책이 있는지 / 없는지**. 그다음 권별 표.

| 책 | PDF | folio 불연속 | OCR 없는 면 |

- 불연속은 `N곳 / M면` 으로 쓴다 (2면 이상 빠지는 지점이 있다).
- 육안 확인한 건과 추정인 건을 구분해서 쓴다.
- 확인 못 한 범위를 명시한다: 앞머리 로마자 쪽번호 구간, 맨 뒤 판권지 등 쪽번호 없는 부분.

리포트는 scratchpad에 markdown으로 남기고, 사용자가 원하면 PDF 폴더 옆에 복사한다.

## 검사 대상 찾기

사용자 책 폴더는 `~/OneDrive/30_책` (실제 경로 `~/Library/CloudStorage/OneDrive-개인/30_책`).
"어제 넣은", "오후 6시 이후" 같은 요청은 mtime으로 추린다.

```bash
find ~/OneDrive/30_책 -maxdepth 1 -name '*.pdf' -newermt "2026-09-20 18:00"
```

OneDrive는 온디맨드 동기화라 클라우드에만 있는 파일이 있을 수 있다. 시작 전에 `pdfinfo`로
전부 열리는지 확인하고, 실패한 파일은 정상으로 보고하지 말고 따로 알린다.
