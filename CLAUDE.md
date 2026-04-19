# NMS (Network Monitoring System) - ai100 통합 설계

## 프로젝트 개요

**목적**: 사무실 네트워크(192.168.219.x) 전체 서버/장비를 모니터링하고, 긴급 상황 발생 시 갤럭시 워치8로 즉시 알림 전송
**위치**: `~/projects/nms/`
**포트**: 8300
**통합**: CPM (Claude Prompt Manager, port 9200)과 연동, CCTV(port 8200) 카메라 상태 연동
**DB**: MySQL 192.168.219.200:3306 (기존 인프라 활용)

---

## 사무실 네트워크 전체 현황

### 아키텍처

```
┌──────────────────────────────────────────────────────────────────────┐
│                    사무실 네트워크 (192.168.219.x)                    │
│                                                                      │
│  [공유기 x3]  .1(Router) / .2(AP) / .3(AP)                          │
│       │                                                              │
│  ┌────┴─────────────────────────────────────────────────────┐       │
│  │                        스위치                             │       │
│  └──┬──────┬──────┬──────┬──────┬──────┬──────┬─────────────┘       │
│    .80    .100   .200  .201  .202   .203   .210                      │
│   AI서버  lohas  DB서버 NAS1  NAS2   Mac   주문관리                  │
│                                                                      │
│  CCTV 5대: .221(Hik) .222(Hik) .223(Mer) .224(Mer) .225(Mer)       │
└──────────────────────────────────────────────────────────────────────┘
         │
    NMS(:8300) ← 전체 모니터링
         │ FCM Push
         ▼
  갤럭시 워치8 (긴급알림)
```

### 서버 장비 목록 (CPM DB + CCTV DB 확인 완료)

| IP | 호스트명 | 역할 | 주요 서비스 |
|----|----------|------|-------------|
| 192.168.219.80 | ai80 (80서버) | AI/RTX 3080 서버 (64GB) | Open WebUI(:8080), Ollama(:11434), MyVoice FastAPI(:9090) |
| 192.168.219.100 | lohas (100서버) | 메인 서버 | 아래 서비스 포트 맵 참조 |
| 192.168.219.200 | dbsrv | MySQL/파일 서버 | MySQL(:3306) - 21개 DB 운용 |
| 192.168.219.201 | nassrv1 | Synology NAS #1 | 웹 UI, CCTV 녹화 저장소 |
| 192.168.219.202 | nassrv2 | Synology NAS #2 | 웹 UI |
| 192.168.219.203 | macmini | M1 Mac Mini (개발) | SSH(:22) |
| 192.168.219.210 | ordersrv | 주문관리 서버 | order web(:8989) |

### 100서버 (lohas) 서비스 포트 맵 (CPM DB 실측)

| 포트 | 서비스 | 프로젝트 | 타입 | 상태 |
|------|--------|----------|------|------|
| 3000 | ntplanic Next.js | 901플래너 | dev | active |
| 3307 | MariaDB | - | db | active |
| 5173 | ai100 Vite | 사내직원업무시스템 | dev | active |
| 6379 | Redis | - | cache | active |
| 8001 | ai100 Django API | 사내직원업무시스템 | api | active |
| 8900 | naverterms Vite | 네이버순위추적 v3.0 | dev | active |
| 8901 | naverterms Django API | 네이버순위추적 v3.0 | api | active |
| 8989 | order web (Docker) | 주문관리 | dev | active |
| 8021 | cliphub FastAPI | 유튜브동영상관리 | dev | active |
| 8080 | jebudo Next.js | 제부도 물때검색 | dev | active |
| 8200 | CCTV Django | CCTV 모니터링 | dev | active |
| 8300 | **NMS Django** | **본 프로젝트 (신규)** | dev | planned |
| 9200 | CPM Django | 프롬프트매니져 | dev | active |

### 80서버 (ai80) 서비스 포트 맵 (CPM DB 실측)

| 포트 | 서비스 | 타입 | 상태 |
|------|--------|------|------|
| 8080 | Open WebUI | dev | active |
| 9090 | MyVoice FastAPI | prod | active |
| 11434 | Ollama LLM | api | active |

### 외부 서비스 (프로덕션 배포)

| 도메인 | 서비스 | 비고 |
|--------|--------|------|
| 901planner.cloud | 901플래너 (ntplanic) | 100서버 Docker |
| jebudo.pages.dev | 제부도 물때검색 | Cloudflare Pages |
| myvoice.901planner.cloud | 내목소리 TTS | 80서버 Docker |
| cpm.901planner.cloud | CPM | 100서버 Docker |

### 공유기 (3대 확인 완료)

| IP | 역할 | 모드 |
|----|------|------|
| 192.168.219.1 | 메인 공유기 (LG) | Router |
| 192.168.219.2 | 서브 공유기 | AP 모드 |
| 192.168.219.3 | 서브 공유기 | AP 모드 |

### CCTV 5대 (CCTV MySQL DB 확인 완료)

| IP | 이름 | 제조사 | 모델 | 포트 | 상태 |
|----|------|--------|------|------|------|
| 192.168.219.221 | 입구카메라 (NAS) | Hikvision | - | RTSP:554 | online |
| 192.168.219.222 | 복도 (NAS) | Hikvision | - | RTSP:554 | online |
| 192.168.219.223 | 포장룸 | Mercury | MIPC3312P | RTSP:554 | online |
| 192.168.219.224 | 큰창고방 | Mercury | MIPC3312P | RTSP:554 | online |
| 192.168.219.225 | 거실 | Mercury | MIPC3312P | RTSP:554 | online |

> CCTV 시스템 부가 포트: go2rtc RTSP 프록시(:8554), go2rtc API(:1984), NTP 서버(:123)

### MySQL 서버 (.200) 데이터베이스 목록

```
ads, ai_platform, betona, bitwing, cctv, cupang, django_shop_db,
joacham, lohas, myproduct, naverdb, nest, owimagedb, ownerDB,
sms2, tax, test, tetris
```

---

## 프로젝트 디렉토리 구조

```
~/projects/nms/                   # NMS 독립 Django 프로젝트
├── CLAUDE.md                     # 본 설계문서
├── config/                       # Django 프로젝트 설정
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── nms/                          # NMS Django 앱
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                 # MonitorTarget, AlertRule, Alert, DeviceToken, StatusLog
│   ├── views.py                  # API 뷰
│   ├── serializers.py            # DRF 시리얼라이저
│   ├── monitor.py                # 모니터링 로직 (ping, port, http, resource)
│   ├── fcm.py                    # Firebase FCM 발송
│   ├── tasks.py                  # 스케줄 태스크 (APScheduler)
│   ├── urls.py
│   └── templates/nms/
│       └── dashboard.html        # 웹 대시보드
├── firebase-key.json             # Firebase 서비스 계정 키 (git 제외)
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env
```

> 참고: ai100 프로젝트(`~/projects/ai100`)와는 독립 프로젝트로 운용. 같은 MySQL(.200) DB 서버 공유.

---

## DB 모델 설계

### MonitorTarget (모니터링 대상)

| 필드 | 타입 | 설명 |
|------|------|------|
| name | CharField | 표시명 (예: AI서버, NAS) |
| host | CharField | IP 또는 hostname |
| port | IntegerField | 체크할 포트 (null=ping only) |
| check_type | CharField | ping / port / http / resource |
| interval | IntegerField | 체크 주기 (초, 기본 60) |
| is_active | BooleanField | 활성화 여부 |
| last_status | CharField | up / down / warn |
| last_checked | DateTimeField | 마지막 체크 시각 |
| fail_count | IntegerField | 연속 실패 횟수 (consecutive 알림 판단용, 기본 0) |

### AlertRule (알림 규칙)

| 필드 | 타입 | 설명 |
|------|------|------|
| target | ForeignKey(MonitorTarget) | 대상 |
| condition | CharField | down / cpu_over / mem_over / disk_over |
| threshold | IntegerField | 임계값 (%, 초) |
| level | CharField | info / warning / critical |
| consecutive | IntegerField | 연속 실패 횟수 후 알림 (기본 3) |
| cooldown | IntegerField | 재알림 방지 시간 (초, 기본 300) |

### Alert (알림 이력)

| 필드 | 타입 | 설명 |
|------|------|------|
| target | ForeignKey | 대상 |
| rule | ForeignKey(null=True) | 트리거된 규칙 (수동 발송 시 null) |
| level | CharField | info / warning / critical |
| title | CharField | 알림 제목 |
| message | TextField | 상세 메시지 |
| sent_at | DateTimeField | 발송 시각 |
| resolved_at | DateTimeField | 복구 시각 (null=미복구) |
| fcm_result | CharField | FCM 응답 결과 |

### StatusLog (상태 변경 이력)

| 필드 | 타입 | 설명 |
|------|------|------|
| target | ForeignKey(MonitorTarget) | 대상 |
| status | CharField | up / down / warn |
| response_time | FloatField | 응답 시간 (ms, null 가능) |
| detail | TextField | 상세 정보 (에러 메시지 등) |
| created_at | DateTimeField | 기록 시각 |

### DeviceToken (FCM 토큰)

| 필드 | 타입 | 설명 |
|------|------|------|
| device | CharField | 기기명 (watch8, phone) |
| token | TextField | FCM 토큰 |
| updated_at | DateTimeField | 마지막 갱신 |

---

## 모니터링 항목

### 네트워크 모니터링 (전 장비)

| 대상 | IP | 체크 방식 | 주기 |
|------|-----|-----------|------|
| 메인 공유기 | .1 | ping | 60s |
| 서브 공유기 x2 | .2, .3 | ping | 60s |
| 80서버 (AI) | .80 | ping + port(8080,9090,11434) | 60s |
| 100서버 (lohas) | .100 | ping + http(/health/) + 포트 전체 | 30s |
| DB 서버 | .200 | ping + port(3306) | 30s |
| NAS | .201 | ping + http | 60s |
| Mac Mini | .203 | ping + port(22) | 120s |
| 주문관리 서버 | .210 | ping + http(8989) | 60s |
| CCTV 입구 (Hik) | .221 | ping | 60s |
| CCTV 복도 (Hik) | .222 | ping | 60s |
| CCTV 포장룸 (Mer) | .223 | ping | 60s |
| CCTV 큰창고방 (Mer) | .224 | ping | 60s |
| CCTV 거실 (Mer) | .225 | ping | 60s |

### 100서버 서비스 포트 모니터링

| 포트 | 서비스 | 체크 방식 |
|------|--------|-----------|
| 3000 | ntplanic Next.js | http |
| 3307 | MariaDB | port |
| 5173 | ai100 Vite | http |
| 6379 | Redis | port |
| 8001 | ai100 Django API | http |
| 8900 | naverterms Vite | http |
| 8901 | naverterms Django API | port |
| 8989 | order web | http |
| 8021 | cliphub FastAPI | http |
| 8080 | jebudo Next.js | http |
| 8200 | CCTV Django | http |
| 9200 | CPM Django | http |

### 서버 리소스 모니터링

| 항목 | warning | critical | 대상 서버 |
|------|---------|----------|-----------|
| CPU 사용률 | > 85% | > 95% | .100(lohas) |
| 메모리 사용률 | > 80% | > 90% | .100(lohas) |
| 디스크 사용률 | > 80% | > 90% | .100(lohas) |
| GPU 온도 | > 80°C | > 90°C | .80(ai80, RTX 3080) |
| MySQL 연결 수 | > 100 | > 150 | .200(dbsrv) |

> 원격 서버(.80) 리소스 수집: SSH + psutil 또는 agent 방식 결정 필요

---

## FCM 알림 레벨

| 레벨 | 색상 | 진동 패턴 | 사용 예 |
|------|------|-----------|---------|
| info | 파랑 | 1회 짧게 | 서비스 복구, 정보 |
| warning | 주황 | 2회 중간 | CPU 85%, 디스크 80% |
| critical | 빨강 | 3회 강하게 | 서버 다운, 디스크 90% |

---

## CPM 통합 방식

### CPM ServicePort 모델 연동

CPM에 이미 `ServicePort` 모델이 있어 전체 서비스/포트 정보를 관리 중:

```python
# CPM core/models.py - ServicePort
# 필드: server_name, ip, port, service_name, service_type, protocol, status
# DB 테이블: service_ports (unique: ip + port)
```

NMS는 CPM의 `ServicePort` 데이터를 API로 읽어서 모니터링 대상 자동 동기화:
```
GET http://192.168.219.100:9200/api/services/  → 전체 서비스 목록
POST http://192.168.219.100:9200/api/discover/  → 포트 스캔 트리거
```

### CPM 대시보드 위젯 추가
- CPM 웹 UI (9200)에 NMS 상태 요약 위젯 표시
- 현재 서버 상태 (up/down/warn) 실시간 표시
- 최근 알림 5건 표시

### CCTV 시스템 연동

CCTV 프로젝트(`~/projects/cctv`)의 카메라 상태를 NMS에서 통합 모니터링:
```
GET http://192.168.219.100:8200/api/cameras/  → 카메라 목록 + 상태
DB 직접 조회: cctv.cameras_camera 테이블 (MySQL .200)
```

### 공통 API 키 인증
```python
# 내부 서비스 간 통신: X-Internal-Key 헤더 사용
# settings.py: INTERNAL_API_KEY = env('INTERNAL_API_KEY')
```

---

## API 엔드포인트

```
POST /nms/api/alert/register/     # FCM 토큰 등록 (워치 앱 → 서버)
POST /nms/api/alert/send/         # 수동 알림 발송 (테스트/수동)
GET  /nms/api/status/             # 전체 모니터링 대상 상태
GET  /nms/api/alerts/             # 알림 이력 조회
GET  /nms/api/health/             # NMS 자체 헬스체크
GET  /nms/api/targets/            # 모니터링 대상 CRUD
GET  /nms/api/statuslog/          # 상태 변경 이력 조회
POST /nms/api/sync-cpm/           # CPM ServicePort 동기화
GET  /nms/dashboard/              # 웹 대시보드 (관리자용)
```

---

## 갤럭시 워치8 앱

**패키지명**: `com.bitic.ai100alert`
**타겟**: Wear OS 4 (갤럭시 워치8)
**빌드**: Android Studio Hedgehog 이상

### 주요 기능
1. **FCM 수신**: 백그라운드 메시지 수신 (LTE 독립)
2. **긴급 화면**: critical 레벨 시 전체 빨간 화면 + 진동
3. **토큰 자동 등록**: 앱 시작 시 ai100 서버에 FCM 토큰 전송
4. **알림 이력**: 최근 수신 알림 20건 목록

### 파일 구조
```
WearAlert/
├── app/
│   ├── google-services.json      # Firebase 설정
│   ├── src/main/
│   │   ├── AndroidManifest.xml
│   │   └── java/com/bitic/ai100alert/
│   │       ├── MainActivity.kt           # 메인 화면 (알림 목록)
│   │       ├── AlertDetailActivity.kt    # 상세 화면
│   │       ├── MyFirebaseService.kt      # FCM 수신 처리
│   │       └── ServerApiService.kt       # 토큰 등록 API
│   └── build.gradle
└── build.gradle
```

---

## 기술 스택

| 구분 | 기술 | 비고 |
|------|------|------|
| Backend | Django 5.x + DRF | CCTV 프로젝트와 동일 스택 |
| Database | MySQL (192.168.219.200:3306) | DB명: nms (신규 생성) |
| Scheduler | APScheduler | 주기적 모니터링 체크 |
| Push | Firebase FCM (HTTP v1) | firebase-admin SDK |
| Deploy | Docker + Gunicorn | docker-compose, host network |
| Watch App | Kotlin + Wear OS 4 | Android Studio |

---

## 구현 순서

### Phase 0: 사전 준비
```
1. MySQL .200에 nms 데이터베이스 생성
2. Firebase 콘솔에서 프로젝트 생성 (ai100-alert)
   - 서비스 계정 키 JSON → firebase-key.json
   - Android 앱 추가 (com.bitic.ai100alert) → google-services.json
```

### Phase 1: Django 프로젝트 기반 구축
```
1. ~/projects/nms/ Django 프로젝트 생성 (config/ 패턴)
2. settings.py: MySQL .200 연결, TIME_ZONE=Asia/Seoul
3. models.py: MonitorTarget, AlertRule, Alert, StatusLog, DeviceToken
4. makemigrations && migrate
5. fcm.py: Firebase FCM 발송 모듈
6. views.py + serializers.py + urls.py: REST API
7. Dockerfile + docker-compose.yml (port 8300, host network)
```

### Phase 2: 모니터링 엔진
```
1. monitor.py: ping(subprocess), port(socket), http(requests) 체크
2. tasks.py: APScheduler 설정 (대상별 주기 체크)
3. 알림 규칙 평가 + fail_count 관리 + 자동 복구 감지
4. 초기 데이터: 위 모니터링 대상 테이블 기반 시딩
5. CPM ServicePort API 동기화 기능
```

### Phase 3: 대시보드 + 통합
```
1. dashboard.html: 전체 서버 상태 실시간 대시보드
2. CPM 위젯 연동
3. CCTV 카메라 상태 연동 (DB 직접 또는 API)
```

### Phase 4: Wear OS 앱
```
1. Android Studio: Wear OS 프로젝트 생성
2. FCM 수신 + 긴급 알림 UI
3. 갤럭시 워치8 배포 (ADB sideload)
```

---

## 환경변수 (.env)

```env
# Django
DJANGO_SECRET_KEY=change-me-in-production
DEBUG=true
ALLOWED_HOSTS=192.168.219.100,localhost

# Database (MySQL .200 공유)
DB_HOST=192.168.219.200
DB_PORT=3306
DB_NAME=nms
DB_USER=root
DB_PASSWORD=<password>

# Firebase
FIREBASE_KEY_PATH=/home/joacham/projects/nms/firebase-key.json

# NMS 설정
NMS_CHECK_INTERVAL=60
NMS_ALERT_COOLDOWN=300

# 내부 서비스 인증
INTERNAL_API_KEY=your-secret-key-here

# CPM 연동
CPM_BASE_URL=http://192.168.219.100:9200

# CCTV 연동
CCTV_BASE_URL=http://192.168.219.100:8200
```

---

## .gitignore

```
firebase-key.json
google-services.json
.env
*.pyc
__pycache__/
db.sqlite3
media/
```

---

## 관련 프로젝트 경로

| 프로젝트 | 경로 | 포트 | 역할 |
|----------|------|------|------|
| ai100 | ~/projects/ai100 | 5173, 8001, 8003 | 사내업무시스템 |
| cctv | ~/projects/cctv | 8200 | CCTV 모니터링 |
| cpm | ~/projects/cpm | 9200 | 프롬프트 매니저 |
| nms | ~/projects/nms | 8300 | 본 프로젝트 |
| ntplanic | ~/projects/ntplanic | 3000 | 901플래너 |
| cliphub | ~/projects/cliphub | 8021 | 유튜브 관리 |
| order | ~/projects/order | 8989 | 주문관리 |
| naverterms | ~/projects/naverterms | 8900, 8901 | 네이버 순위추적 v3.0 |
| jebudo | ~/projects/jebudo | 8080 | 제부도 물때 |

---

## Oracle Cloud 중계 서버

| 항목 | 값 |
|------|-----|
| IP | 134.185.104.140 |
| 도메인 | joacham.duckdns.org |
| SSH | `ssh ubuntu@134.185.104.140` 또는 `ssh ubuntu@joacham.duckdns.org` |
| OS | Ubuntu 24.04 (Linux 6.17.0-1010-oracle) |
| Python | 3.12.3 |
| Web | nginx(:80) |
| 역할 | NMS → Oracle 중계 → Watch 8 앱 (FCM) |

### 중계 API (nms-relay)
- NMS(100번서버)가 outbound POST로 데이터 전송
- Oracle이 수신하여 캐싱 + FCM으로 Watch 8에 전달
- 엔드포인트: `/api/relay/heartbeat/`, `/api/relay/alert/`, `/api/relay/sync/`
- 인증: `X-NMS-Key` 헤더 (공유 시크릿)

---

## TODO

- [ ] IP타임 외부사용자용 공유기 IP 확인 (joacham 계정)
- [ ] 각 서버 SSH 접근 가능 여부 확인 (원격 리소스 수집용)
- [ ] 주문관리 서버(.210) 실제 서비스 포트 확인 (CPM에 8989 등록됨)
- [ ] Firebase 프로젝트 생성 + 키 파일 준비
- [ ] MySQL .200에 nms DB 생성

---

*최초 작성: 2026-04-16*
*작성자: 김준용 (비트정보통신)*
*연락처: betona1@nate.com*
*데이터 소스: CPM DB(service_ports), CCTV MySQL DB(cameras_camera), go2rtc.yaml*
