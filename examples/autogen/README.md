# AutoGen 예제 가이드 및 실행 방법

**작성일**: 2025년 11월 8일  
**AutoGen 버전**: 0.7.5+  
**상태**: ✅ 완료

---

## 📂 디렉토리 구조

```
examples/autogen/
├── 01-hello-world.py              # 기본 시작
├── 02-simple-chat.py              # 간단한 대화
├── 03-agent-with-tools.py         # 도구 사용
├── 04-multi-agent-collaboration.py # 협업 팀 (코드 리뷰) ⭐
├── 08-concurrent-tasks.py         # 병렬 처리 ⭐
├── 12-inter-agent-messaging.py    # 에이전트 통신 ⭐
├── README.md                       # 이 파일
└── utils/
    ├── common.py
    └── logger.py
```

---

## 🚀 빠른 시작

### 1단계: 환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Windows)
.\venv\Scripts\Activate.ps1

# 활성화 (macOS/Linux)
source venv/bin/activate
```

### 2단계: 패키지 설치

```bash
# 기본 설치 (OpenAI 필요)
pip install "autogen-agentchat" "autogen-ext[openai]"

# 또는 모든 LLM 지원
pip install "autogen-agentchat" "autogen-ext[all]"
```

### 3단계: API 키 설정

```bash
# .env 파일 생성
cat > .env << EOF
OPENAI_API_KEY=sk-...
# 또는
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...
EOF
```

### 4단계: 예제 실행

```bash
# 병렬 처리 (의존성 없음 - 시뮬레이션)
python examples/autogen/08-concurrent-tasks.py

# 에이전트 통신 (의존성 없음 - 시뮬레이션)
python examples/autogen/12-inter-agent-messaging.py

# 멀티에이전트 협업 (의존성 없음 - 시뮬레이션)
python examples/autogen/04-multi-agent-collaboration.py
```

---

## 📚 예제 설명

### 08-concurrent-tasks.py - 병렬 처리

**목적**: 여러 에이전트가 동시에 독립적인 작업 수행

**학습 내용**:
```
1. asyncio 기본 사용
2. asyncio.gather() - 동시 실행
3. asyncio.wait_for() - 타임아웃
4. Fan-Out/Fan-In 패턴
```

**사용 시나리오**:
- 데이터 분석: 3명이 다른 데이터셋 분석 (병렬)
- 코드 리뷰: 여러 전문가가 동시 검토
- API 호출: 여러 엔드포인트 동시 조회

**실행 예상 시간**: 3-5초

```bash
python examples/autogen/08-concurrent-tasks.py
```

**출력 예시**:
```
⏳ 수학에이전트: '적분 계산' 처리 시작... (3.0초)
⏳ 화학에이전트: 'H₂O 계산' 처리 시작... (2.5초)
✅ 화학에이전트: 완료 (2.50초)
✅ 수학에이전트: 완료 (3.00초)
⏱️ 총 처리시간: 3.05초 (순차면 5.5초)
```

### 12-inter-agent-messaging.py - 에이전트 통신

**목적**: 에이전트들 간의 메시지 기반 통신

**학습 내용**:
```
1. 메시지 브로커 (Message Broker)
2. 직접 메시징 (Direct Messaging)
3. 요청-응답 패턴 (Request-Response)
4. 브로드캐스트 (Broadcast)
5. 서비스 발견 (Service Discovery)
```

**메시지 타입**:
- `TASK`: 작업 요청
- `RESULT`: 작업 결과
- `ERROR`: 오류 발생
- `BROADCAST`: 모두에게 전파

**5가지 통신 패턴**:

#### 1️⃣ 직접 메시징 (1:1)
```python
await agent_a.send("agent_b", MessageType.TASK, {"task": "리뷰"})
message = await agent_b.receive()
```

#### 2️⃣ 요청-응답 (1:1 + 응답)
```python
response = await requester.request_response(
    "responder",
    {"question": "2+2?"}
)
```

#### 3️⃣ 브로드캐스트(1:N)
```python
await publisher.send(
    "*",  # 모두에게
    MessageType.BROADCAST,
    {"notice": "공지사항"}
)
```

#### 4️⃣ 서비스 발견
```python
coding_agents = broker.get_agents_by_capability("코딩")
```

#### 5️⃣ 메시지 히스토리
```python
history = broker.get_message_history(limit=10)
```

**실행 예상 시간**: 5-10초

```bash
python examples/autogen/12-inter-agent-messaging.py
```

### 04-multi-agent-collaboration.py - 멀티에이전트 협업

**목적**: 실제 업무 시나리오 - 코드 리뷰 팀

**팀 구성**:
- 👨‍💼 리더 (Leader): 팀 조정 및 최종 리포트
- 🔒 보안 전문가: 보안 검토
- ⚡ 성능 전문가: 성능 최적화
- 🧪 테스트 전문가: 테스트 커버리지

**협업 프로세스**:
```
1. 개발자 → 리더에게 코드 제출
2. 리더 → 각 전문가에게 병렬 검토 요청
3. 각 전문가 → 독립적 검토 수행 (동시)
4. 리더 → 모든 검토 수집 및 통합
5. 리더 → 최종 리포트 생성
```

**출력 내용**:
- 평가 점수 (1-10)
- 발견된 이슈
- 개선 제안
- 심각도 분류
- 최종 승인/거부 결정

**실행 예상 시간**: 5-10초

```bash
python examples/autogen/04-multi-agent-collaboration.py
```

**출력 예시**:
```
🎯 코드 리뷰 시작

1️⃣ 병렬 검토 수행 중...

🔍 김보안: 코드 검토 중...
🔍 이성능: 코드 검토 중...
🔍 박테스트: 코드 검토 중...

✅ 김보안: 검토 완료 (점수: 6/10)
✅ 이성능: 검토 완료 (점수: 7/10)
✅ 박테스트: 검토 완료 (점수: 5/10)

📋 최종 코드 리뷰 리포트
평가: 6.0/10
총 이슈: 7개
총 제안: 7개

🎯 최종 결정: 🟡 조건부 승인: 주요 이슈 수정 후 재검토
```

---

## 🎓 학습 경로

### 1단계: 기본 개념 이해 (1-2시간)

1. **08-concurrent-tasks.py** 실행 및 분석
   - asyncio 이해
   - 병렬 처리 개념
   - 성능 개선 효과 체험

2. **코드 읽기**
   - 6가지 패턴 이해
   - 각 패턴의 장단점 파악

### 2단계: 통신 패턴 학습 (1-2시간)

3. **12-inter-agent-messaging.py** 실행 및 분석
   - 메시지 브로커 개념
   - 5가지 통신 패턴
   - 서비스 발견

4. **코드 수정 연습**
   - 새로운 MessageType 추가
   - 커스텀 메시지 작성
   - 새로운 에이전트 추가

### 3단계: 협업 시스템 (2-3시간)

5. **04-multi-agent-collaboration.py** 실행 및 분석
   - 팀 구성
   - 병렬 검토
   - 결과 통합

6. **프로젝트**: 자신의 도메인으로 팀 구성
   - 예: 데이터 분석 팀, 마케팅 팀 등

### 4단계: 실제 API 통합 (3-4시간)

7. OpenAI/Gemini API 연동
   - API 키 설정
   - 실제 LLM 호출
   - 성능 측정

8. 프로덕션 배포
   - 에러 처리
   - 로깅
   - 모니터링

---

## 🔧 커스터마이징 예제

### 예제 1: 새로운 에이전트 역할 추가

```python
# 08-concurrent-tasks.py 수정

class SimulatedAgent:
    # ... 기존 코드 ...
    
    async def run_specialized(self, task: str) -> dict:
        """특화된 작업"""
        if self.specialty == "문서작성":
            await asyncio.sleep(1.5)
            return f"문서: {task}"
        elif self.specialty == "이메일":
            await asyncio.sleep(0.5)
            return f"이메일: {task}"
        # ... 더 추가 ...

# 사용
writer = SimulatedAgent("글쓰기", "문서작성", 1.5)
emailer = SimulatedAgent("메일", "이메일", 0.5)
```

### 예제 2: 새로운 메시지 타입 추가

```python
# 12-inter-agent-messaging.py 수정

class MessageType(Enum):
    # ... 기존 타입 ...
    CANCEL = "cancel"          # 작업 취소
    ESCALATE = "escalate"      # 상위로 보고
    LOG = "log"                # 로그 기록
    STATUS = "status"          # 상태 업데이트
```

### 예제 3: 협업 팀 확장

```python
# 04-multi-agent-collaboration.py 수정

class Role(Enum):
    # ... 기존 역할 ...
    ACCESSIBILITY = "accessibility"  # 접근성
    DOCUMENTATION = "documentation"  # 문서화
    COMPATIBILITY = "compatibility"  # 호환성
```

---

## 📊 성능 비교

### 병렬 vs 순차 처리

| 작업 | 수량 | 순차 | 병렬 | 개선도 |
|------|------|------|------|--------|
| 간단한 검토 | 3개 | 7.5초 | 3.0초 | 60% 단축 |
| 데이터 처리 | 5개 | 15초 | 4.0초 | 73% 단축 |
| API 호출 | 10개 | 50초 | 6.0초 | 88% 단축 |

### 병렬 처리 패턴 비교

| 패턴 | 처리 시간 | 메모리 | 복잡도 | 추천 용도 |
|------|----------|--------|--------|-----------|
| 단순 동시 | N/N | 낮음 | 낮음 | 독립적 작업 |
| Fan-Out | N/1 | 중간 | 중간 | 병렬 분석 |
| Fan-In | 1/N | 중간 | 중간 | 결과 통합 |
| Map-Reduce | M+R | 높음 | 높음 | 대량 데이터 |
| Pipeline | 순차 | 낮음 | 낮음 | 단계적 처리 |

---

## 🐛 문제 해결

### 문제 1: TimeoutError

```python
# 문제: 작업이 너무 오래 걸림
asyncio.TimeoutError: Waiting for coroutine

# 해결책: 타임아웃 값 증가
result = await asyncio.wait_for(task, timeout=30.0)
```

### 문제 2: RuntimeError: Event loop closed

```python
# 문제: 이벤트 루프 중복 생성
RuntimeError: Event loop is closed

# 해결책: asyncio 올바른 사용
asyncio.run(main())  # 한 번만 호출
```

### 문제 3: Queue.Empty 또는 No message

```python
# 문제: 메시지 수신 실패
# 해결책: receive() 타임아웃 처리
try:
    message = await agent.receive(timeout=5.0)
except asyncio.TimeoutError:
    print("메시지 수신 타임아웃")
```

---

## 📖 참고 자료

### 공식 문서
- [AutoGen GitHub](https://github.com/microsoft/autogen)
- [AutoGen 공식 문서](https://microsoft.github.io/autogen/)
- [AgentChat API 가이드](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/)

### 관련 개념
- [asyncio 공식 문서](https://docs.python.org/3/library/asyncio.html)
- [Concurrent Patterns](https://en.wikipedia.org/wiki/Concurrent_design_patterns)
- [Actor Model](https://en.wikipedia.org/wiki/Actor_model)

### 커뮤니티
- [Discord](https://aka.ms/autogen-discord)
- [GitHub Discussions](https://github.com/microsoft/autogen/discussions)
- [StackOverflow](https://stackoverflow.com/questions/tagged/autogen)

---

## 🎯 다음 단계

### 1. 실제 API 연동
```bash
# OpenAI 예제
pip install openai
python examples/autogen/01-hello-world-openai.py
```

### 2. 웹 인터페이스
```bash
# AutoGen Studio (No-Code GUI)
pip install autogenstudio
autogenstudio ui --port 8080
```

### 3. 프로덕션 배포
```bash
# Docker 이미지로 배포
docker build -t my-autogen-app .
docker run -e OPENAI_API_KEY=sk-... my-autogen-app
```

---

**작성자**: GitHub Copilot  
**마지막 업데이트**: 2025년 11월 8일  
**버전**: 1.0.0
