# drug-detection-crawler

AI 기반 마약 유해 게시글 탐지를 위한 데이터 수집용 크롤러입니다.  
X/Twitter 게시글 데이터를 수집하고, 원본 HTML을 JSON으로 저장한 뒤 파싱 및 CSV 변환, 이미지/미디어 다운로드까지 이어지는 데이터 수집 파이프라인을 제공합니다.

## 주요 기능

- Chrome 디버그 세션 기반 X/Twitter 게시글 크롤링
- 게시글 원본 HTML 수집 및 JSON 저장
- `item_key` 기반 중복 데이터 저장 방지
- 스크롤 기반 추가 게시글 수집
- 새 데이터가 일정 횟수 이상 발견되지 않을 경우 자동 종료
- 수집된 HTML에서 게시글 본문, 작성자, 작성일, 이미지 URL, 해시태그, 반응 수 등 파싱
- 파싱 결과를 CSV로 변환
- CSV에 포함된 이미지/미디어 URL 다운로드
- 수집 데이터와 코드 저장소 분리 관리

## 프로젝트 구조

```text
src/drug_detection_crawler
├── config
│   └── settings.py
├── crawlers
│   ├── chrome_debug_launcher.py
│   └── scroll_crawler.py
├── parsers
│   └── tweet_parser.py
├── pipelines
│   ├── crawling_pipeline.py
│   ├── parsing_pipeline.py
│   ├── save_csv_pipeline.py
│   └── download_media_pipeline.py
└── storage
    ├── save_json.py
    └── save_tools.py
```

## 주요 모듈

### `config/settings.py`

크롤링과 저장에 필요한 공통 설정을 관리합니다.

- 데이터 저장 경로
- Chrome 실행 경로
- 디버그 포트
- HTML selector 설정
- 미디어 다운로드 경로, 재시도 횟수, 타임아웃

수집 데이터는 기본적으로 `initial_crawling_data` 폴더에 저장됩니다.

### `pipelines/crawling_pipeline.py`

크롤링 핵심 로직을 담당합니다.

- Chrome 디버그 세션 연결
- X/Twitter 게시글 요소 탐색
- 게시글 원본 HTML 수집
- SHA-256 기반 `item_key` 생성
- 중복 게시글 스킵
- 스크롤 반복 수집
- 수집 결과를 `collected_elements.json`으로 저장

### `parsers/tweet_parser.py`

수집된 원본 HTML을 분석 가능한 구조화 데이터로 변환합니다.

- 닉네임
- 사용자 ID
- 작성일
- 게시글 URL
- 게시글 본문
- 댓글, 리트윗, 좋아요, 조회수
- 이미지 URL
- 해시태그
- 비디오 관련 URL

### `storage/save_json.py`, `storage/save_tools.py`

수집 및 파싱 결과 저장을 담당합니다.

- JSON 읽기/쓰기
- 임시 파일 기반 안전 저장
- CSV 변환
- 이미지 및 미디어 저장
- 기존 데이터 중복 확인

## 데이터 저장 정책

크롤링으로 수집된 데이터에는 게시글 원문, 사용자 ID, 이미지 URL 등 민감할 수 있는 정보가 포함될 수 있습니다.  
따라서 본 프로젝트는 수집 데이터를 코드와 분리된 `initial_crawling_data` 폴더에 저장합니다.

해당 폴더는 상위 저장소의 `.gitignore`에 포함되어 있어 public 코드 저장소에 업로드되지 않도록 관리됩니다.

```text
initial_crawling_data/
├── collected_elements.json
├── tweet_datas.json
├── x_crawling_drugs_text.csv
├── x_crawling_drugs_text_originals.json
└── downloaded_image/
```

## 환경 설정

`.env.example`을 참고하여 `.env` 파일을 생성할 수 있습니다.

```env
CHROME_PATH=
DEBUG_PORT=9222
HTML_TAG=article
SOURCE_NAME=twitter_feed
```

주요 환경 변수는 다음과 같습니다.

- `CHROME_PATH`: Chrome 실행 파일 경로
- `DEBUG_PORT`: Chrome 디버그 포트
- `USER_DATA_DIR`: Selenium용 Chrome 사용자 프로필 경로
- `HTML_TAG`: 크롤링 대상 HTML 태그
- `SOURCE_NAME`: 수집 데이터 출처 이름
- `MEDIA_DOWNLOAD_RETRY_COUNT`: 미디어 다운로드 재시도 횟수
- `MEDIA_DOWNLOAD_TIMEOUT`: 미디어 다운로드 타임아웃

## 실행 흐름

### 1. 크롤링 실행

```bash
python -m drug_detection_crawler.pipelines.crawling_pipeline
```

실행 후 Chrome 브라우저에서 수집 대상 X/Twitter 페이지를 직접 열고, 터미널 안내에 따라 Enter를 입력하면 크롤링이 시작됩니다.

### 2. 원본 HTML 파싱

```bash
python -m drug_detection_crawler.pipelines.parsing_pipeline
```

`collected_elements.json`의 원본 HTML을 파싱하여 `tweet_datas.json`으로 저장합니다.

### 3. CSV 변환

```bash
python -m drug_detection_crawler.pipelines.save_csv_pipeline
```

파싱된 JSON 데이터를 텍스트 분석 및 모델 학습에 활용 가능한 CSV 파일로 변환합니다.

### 4. 이미지 및 미디어 다운로드

```bash
python -m drug_detection_crawler.pipelines.download_media_pipeline
```

CSV에 포함된 이미지/미디어 URL을 읽어 로컬 폴더에 저장합니다.

## 크롤링 방식의 한계

현재 크롤링 기능은 실제 서비스 운영 환경에서 자동으로 주기적 수집을 수행하는 구조가 아니라, 사용자가 Chrome 브라우저에서 직접 로그인하고 수집 대상 페이지를 열어 둔 상태에서 Selenium이 해당 화면에 연결하는 방식입니다.

따라서 다음과 같은 한계가 있습니다.

- 완전 자동화된 서버 기반 크롤링 구조는 아님
- 로그인 상태와 사용자가 열어 둔 페이지에 따라 수집 가능 여부가 달라질 수 있음
- X/Twitter의 HTML 구조나 selector가 변경될 경우 크롤링 로직 수정이 필요할 수 있음
- 수집 데이터에 개인정보 또는 민감 정보가 포함될 수 있어 별도 관리가 필요함

## 후속 개선 계획

- selector 변경에 대응 가능한 크롤링 구조 개선
- 예외 처리 및 실패 로그 강화
- 수집 데이터 정제 및 라벨링 프로세스 고도화
- 텍스트/이미지 탐지 모델 학습 데이터와 연계
- 수집 데이터 익명화 및 접근 권한 관리 검토
- 실제 서비스 환경에 적합한 주기적 수집, 상태 관리, 재시도 로직 검토
