# Phase 1: Worker Agent Pattern 적용

**프로젝트**: AArch-AutoGen Multi-Agent Bridge
**Phase**: 1 - Worker Agent Pattern
**작성일**: 2025년 11월 6일
**상태**: 구현 완료, 테스트 준비

---

## 📋 Phase 1 개요

### 목표
AutoGen의 Worker Agent 패턴을 TCP 클라이언트-서버 시스템에 적용하여 멀티 클라이언트 처리를 개선하고 각 연결의 독립성을 보장한다.

### 적용 범위
- **TCPWorkerAgent**: 각 클라이언트 연결을 처리하는 Worker Agent
- **TCPOrchestrator**: 연결을 Worker들에게 분배하는 Orchestrator
- **비동기 처리**: asyncio 기반의 효율적인 동시성 처리

---

## 🏗️ 구현 아키텍처

### TCPWorkerAgent 클래스
```python
class TCPWorkerAgent:
    - worker_id: 고유 Worker 식별자
    - orchestrator: 상위 Orchestrator 참조
    - process_task(): 메인 작업 처리 로직
    - _handle_client_connect(): 연결 처리
    - _handle_client_message(): 메시지 처리
    - _handle_client_disconnect(): 연결 종료 처리
```

### TCPOrchestrator 클래스
```python
class TCPOrchestrator:
    - workers: Worker Agent들 관리
    - task_queue: 작업 큐 (asyncio.Queue)
    - active_connections: 활성 연결 관리
    - _accept_connections(): 새 연결 수락
    - _worker_task_processor(): Worker 작업 분배
    - get_available_worker(): 로드 밸런싱
```

### 지원하는 메시지 타입
1. **JSON 메시지**
   - `{"type": "echo", "data": "..."}` - Echo 요청
   - `{"type": "status"}` - 서버 상태 조회

2. **원시 메시지**
   - 일반 텍스트 메시지 (JSON이 아닌 경우)

---

## 📁 파일 구조

```
phase1-worker-agent/
├── worker_agent_tcp.py      # 메인 Worker Agent 서버 구현
├── test_client.py           # 테스트 클라이언트
├── README.md               # 이 파일
└── requirements.txt        # 의존성 (필요시)
```

---

## 🚀 실행 방법

### 1. 서버 실행
```bash
python worker_agent_tcp.py
```

### 2. 단일 클라이언트 테스트
```bash
python test_client.py --test single
```

### 3. 다중 클라이언트 테스트
```bash
python test_client.py --test multiple --clients 10
```

### 4. 부하 테스트
```bash
python test_client.py --test load --clients 20 --duration 60
```

---

## 🔧 설정 옵션

### 서버 설정 (TCPOrchestrator)
- `host`: 바인딩 호스트 (기본: 'localhost')
- `port`: 바인딩 포트 (기본: 8888)
- `num_workers`: Worker Agent 수 (기본: 4)

### 클라이언트 설정 (WorkerAgentTestClient)
- `host`: 연결할 서버 호스트 (기본: 'localhost')
- `port`: 연결할 서버 포트 (기본: 8888)

---

## 📊 테스트 시나리오

### 1. 기본 연결 테스트
- 클라이언트 연결 → 환영 메시지 수신 → 연결 종료

### 2. Echo 기능 테스트
- JSON echo 요청 → Worker 처리 → 응답 수신

### 3. 상태 조회 테스트
- 상태 요청 → 서버/Worker 정보 수신

### 4. 다중 클라이언트 테스트
- 여러 클라이언트 동시 연결 및 메시지 교환

### 5. 부하 테스트
- 지속적인 요청 발생 → Worker 분배 효율성 검증

---

## 📈 성능 메트릭

### 목표 성능 지표
- **동시 연결 처리**: 100개 이상
- **응답 시간**: < 100ms (Echo)
- **Worker 활용도**: 균등 분배
- **메모리 사용**: 효율적 관리

### 모니터링 포인트
- 각 Worker의 처리량
- 큐 대기 시간
- 연결 유지율
- 에러 발생률

---

## 🔍 로깅 및 디버깅

### 로그 레벨
- `INFO`: 일반적인 작업 진행상황
- `DEBUG`: 상세한 처리 정보
- `ERROR`: 오류 상황

### 로그 파일
- `worker_agent_tcp.log`: 서버 측 로그
- 콘솔 출력: 실시간 모니터링

---

## ✅ 완료된 작업

- [x] **패턴 분석 및 설계**
  - [x] `docs/autogen/examples/worker-agent-pattern.py` 분석 완료
  - [x] TCP 서버 아키텍처에 Worker 패턴 적용 설계
  - [x] `TCPWorkerAgent` 클래스 설계
  - [x] `TCPOrchestrator` 클래스 설계

- [x] **구현 작업**
  - [x] 기존 TCP 서버 코드 분석 (참조용)
  - [x] Worker Agent 기반 리팩토링 시작
  - [x] 멀티 클라이언트 처리 로직 구현
  - [x] 로드 밸런싱 기능 추가

- [x] **통합 및 테스트**
  - [ ] Worker 패턴 적용된 서버 테스트 ← 다음 단계
  - [ ] 기존 클라이언트와의 호환성 검증 ← 다음 단계
  - [ ] 성능 측정 및 비교 (기존 vs Worker 패턴) ← 다음 단계

---

## 🎯 다음 단계

### Phase 1 완료를 위한 작업
1. **서버 실행 테스트**
   - `python worker_agent_tcp.py` 실행
   - 정상 기동 확인

2. **클라이언트 테스트**
   - 단일 클라이언트 연결 테스트
   - 메시지 송수신 검증

3. **다중 클라이언트 테스트**
   - 동시 연결 처리 확인
   - Worker 분배 균등성 검증

4. **성능 측정**
   - 응답 시간 측정
   - 리소스 사용량 모니터링

### Phase 2 준비
- MoA 패턴 분석 및 설계
- 컴포넌트별 전문 Agent 설계

---

## 🔧 기술 세부사항

### 비동기 처리
- `asyncio` 기반 이벤트 루프
- `asyncio.Queue`를 사용한 작업 큐
- Non-blocking 소켓 I/O

### 메시지 프로토콜
- **길이 접두사**: 4바이트 빅엔디안 정수
- **JSON 인코딩**: UTF-8 텍스트
- **원시 데이터**: 바이트 스트림

### 에러 처리
- 네트워크 예외 처리
- JSON 파싱 오류 처리
- 연결 끊김 자동 감지

---

## 📝 참고 자료

- `docs/autogen/examples/worker-agent-pattern.py`: AutoGen Worker 패턴 예제
- `docs/autogen/examples/basic-parallel.py`: 기본 병렬 처리 패턴
- 생성된 TCP 프로젝트: `D:\work\projects\new\tcp_autogen-20251106_145831\`

---

**작성자**: GitHub Copilot
**다음 업데이트**: 테스트 완료 후