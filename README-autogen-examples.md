# AutoGen Framework Examples - 실행 체크리스트

**작성일**: 2025년 11월 8일  
**기준 버전**: AutoGen 0.7.5+, AgentChat API (신)  
**상태**: ✅ 설계 완료, 예제 개발 중

---

## 📋 개요

Microsoft AutoGen은 멀티에이전트 AI 애플리케이션 구축을 위한 프레임워크입니다. 

### 주요 특징
- **이벤트 기반 메시지 패싱**: Core API로 유연한 통신
- **AgentChat API**: 빠른 프로토타이핑 (Simplified)
- **MCP 통합**: Model Context Protocol 지원
- **분산 런타임**: 로컬/분산 실행 지원
- **마이크로서비스**: gRPC 기반 분산 아키텍처

---

## 🔧 환경 설정

### 설치

```bash
# 기본 설치 (AgentChat + OpenAI)
pip install "autogen-agentchat" "autogen-ext[openai]"

# 전체 설치 (모든 LLM 클라이언트 포함)
pip install "autogen-agentchat" "autogen-ext[all]"

# 개발 버전
git clone https://github.com/microsoft/autogen.git
cd autogen/python
pip install -e .
```

### .env 설정

```env
# OpenAI API
OPENAI_API_KEY=sk-...

# 또는 Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your_deployment

# 또는 Google Gemini
GOOGLE_API_KEY=your_key

# 또는 Anthropic
ANTHROPIC_API_KEY=your_key
```

### 가상환경 활성화

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING="utf-8"

# Linux/Mac
python -m venv venv
source venv/bin/activate
export PYTHONIOENCODING=utf-8
```

---

## 🎯 예제 카테고리

### 1️⃣ AgentChat API (권장 - 신규)

**특징**: 간단한 API, 빠른 프로토타이핑, v0.2 호환성

#### 1.1 기본 예제

- [ ] **01-hello-world.py** - Hello World
  ```bash
  python examples/agentchat/01-hello-world.py
  ```
  ```python
  import asyncio
  from autogen_agentchat.agents import AssistantAgent
  from autogen_ext.models.openai import OpenAIChatCompletionClient
  
  async def main():
      client = OpenAIChatCompletionClient(model="gpt-4o")
      agent = AssistantAgent("assistant", model_client=client)
      result = await agent.run(task="Say 'Hello World!'")
      print(result)
      await client.close()
  
  asyncio.run(main())
  ```
  **예상 결과**: ✅ "Hello World!" 응답

- [ ] **02-simple-chat.py** - 간단한 대화
  - 사용자와 에이전트의 상호작용
  - 다중 턴(turn) 대화 지원

- [ ] **03-agent-with-tools.py** - 도구를 가진 에이전트
  - 함수/도구 사용
  - 외부 API 통합
  - 코드 실행

#### 1.2 멀티에이전트 협업 (🌟 핵심)

- [ ] **04-two-agent-chat.py** - 두 에이전트 대화
  ```python
  # 수학 에이전트와 화학 에이전트 협업
  math_agent = AssistantAgent(
      "math_expert",
      system_message="You are a math expert.",
      model_client=client
  )
  
  chem_agent = AssistantAgent(
      "chemistry_expert",
      system_message="You are a chemistry expert.",
      model_client=client
  )
  
  # 협업 실행
  result = await agent_team.run(task="...")
  ```

- [ ] **05-group-chat.py** - 그룹 채팅 (3명 이상)
  ```python
  # 여러 에이전트가 토론
  group_chat = GroupChat(
      agents=[analyst, researcher, coder],
      model_client=client,
      max_turns=10
  )
  ```

- [ ] **06-hierarchical-agents.py** - 계층 구조 에이전트
  ```python
  # 관리자 에이전트가 여러 작업자 에이전트 관리
  manager = AssistantAgent(
      "manager",
      system_message="Delegate tasks to experts"
  )
  
  workers = [data_agent, code_agent, test_agent]
  ```

- [ ] **07-agent-orchestration.py** - 에이전트 오케스트레이션
  ```python
  # AgentTool을 사용한 네스팅
  math_tool = AgentTool(math_agent)
  chem_tool = AgentTool(chem_agent)
  
  orchestrator = AssistantAgent(
      "orchestrator",
      tools=[math_tool, chem_tool]
  )
  ```

#### 1.3 병렬 처리 & 동시성 (🌟 고급)

- [ ] **08-concurrent-tasks.py** - 동시 작업 실행
  ```python
  # 여러 에이전트가 동시에 독립적인 작업 수행
  tasks = [
      agent1.run(task="analyze data"),
      agent2.run(task="generate report"),
      agent3.run(task="create summary")
  ]
  results = await asyncio.gather(*tasks)
  ```
  **특징**:
  - 비동기 실행
  - 지연 시간 최소화
  - 자원 활용 극대화

- [ ] **09-parallel-stream.py** - 병렬 스트림 처리
  ```python
  # 여러 입력을 병렬로 처리
  async def process_multiple():
      tasks = [
          agent.run_stream(task=f"Process {item}")
          for item in items
      ]
      async for result in asyncio.as_completed(tasks):
          print(result)
  ```

- [ ] **10-map-reduce.py** - Map-Reduce 패턴
  ```python
  # Map: 여러 에이전트가 독립적 처리
  # Reduce: 결과 통합
  ```

- [ ] **11-fan-out-fan-in.py** - Fan-Out/Fan-In 패턴
  ```python
  # 한 에이전트에서 여러 서브태스크로 분산
  # 결과를 다시 수집해 통합 처리
  ```

#### 1.4 에이전트 통신 (🌟 네트워킹)

- [ ] **12-inter-agent-messaging.py** - 에이전트 간 메시징
  ```python
  # 에이전트A → 에이전트B로 메시지 전송
  # 비동기 통신
  ```

- [ ] **13-message-queue.py** - 메시지 큐 패턴
  ```python
  # 에이전트 간 메시지 큐 기반 통신
  # 느슨한 결합(Loose Coupling)
  ```

- [ ] **14-pub-sub.py** - Pub/Sub 패턴
  ```python
  # 발행-구독 모델
  # 이벤트 기반 통신
  ```

- [ ] **15-agent-registry.py** - 에이전트 레지스트리
  ```python
  # 중앙 에이전트 관리
  # 동적 에이전트 등록/해제
  ```

#### 1.5 상태 관리 & 메모리 (🌟 고급)

- [ ] **16-agent-memory.py** - 에이전트 메모리
  ```python
  # 대화 히스토리 유지
  # 컨텍스트 기억
  ```

- [ ] **17-shared-state.py** - 공유 상태
  ```python
  # 여러 에이전트가 공유 상태 접근
  # 동시성 제어
  ```

- [ ] **18-persistence.py** - 상태 영속성
  ```python
  # 상태를 파일/DB에 저장
  # 재시작 시 복구
  ```

#### 1.6 실시간 처리 & 스트리밍

- [ ] **19-streaming-output.py** - 스트리밍 출력
  ```python
  # 토큰 단위로 실시간 출력
  from autogen_agentchat.ui import Console
  
  async with Console(agent.run_stream(task)) as stream:
      async for chunk in stream:
          print(chunk, end="", flush=True)
  ```

- [ ] **20-websocket-agent.py** - WebSocket 에이전트
  ```python
  # 실시간 양방향 통신
  # 웹 프론트엔드 연동
  ```

### 2️⃣ Core API (고급 - 저수준)

**특징**: 더 나은 제어, 메시지 패싱, 분산 런타임

#### 2.1 기본 사용법

- [ ] **21-core-hello-world.py** - Core API Hello World
  ```python
  from autogen_core import Runtime
  from autogen_core import SingleThreadedAgentRuntime
  
  async def main():
      runtime = SingleThreadedAgentRuntime()
      # 에이전트 정의 및 등록
      await runtime.run()
  ```

- [ ] **22-event-loop.py** - 이벤트 루프
  - 메시지 기반 통신
  - 비동기 처리

- [ ] **23-agent-composition.py** - 에이전트 조합
  - 복잡한 에이전트 구조
  - 동적 라우팅

#### 2.2 분산 실행

- [ ] **24-grpc-distributed.py** - gRPC 분산 실행
  ```python
  # 여러 프로세스/머신에서 실행
  # 마이크로서비스 아키텍처
  ```

- [ ] **25-worker-pool.py** - 워커 풀
  ```python
  # 여러 워커 에이전트
  # 작업 분산 처리
  ```

### 3️⃣ MCP (Model Context Protocol) 통합

- [ ] **26-mcp-basic.py** - MCP 기본
  ```python
  from autogen_ext.tools.mcp import McpWorkbench
  
  async def main():
      server_params = StdioServerParams(
          command="npx",
          args=["@playwright/mcp@latest"]
      )
      async with McpWorkbench(server_params) as mcp:
          agent = AssistantAgent(
              "web_agent",
              workbench=mcp
          )
  ```

- [ ] **27-mcp-web-browsing.py** - MCP 웹 브라우징
  - Playwright MCP 서버 사용
  - 웹 페이지 분석

- [ ] **28-mcp-filesystem.py** - MCP 파일시스템
  - 파일 읽기/쓰기
  - 디렉토리 조작

- [ ] **29-mcp-multi-server.py** - 여러 MCP 서버
  ```python
  async with McpWorkbench([
      web_server_params,
      fs_server_params,
      custom_server_params
  ]) as mcp:
      agent = AssistantAgent("multi_tool_agent", workbench=mcp)
  ```

### 4️⃣ 실무 예제

- [ ] **30-code-review-team.py** - 코드 리뷰 팀
  ```python
  # 여러 에이전트가 협력해 코드 리뷰 수행
  ```

- [ ] **31-data-pipeline.py** - 데이터 파이프라인
  ```python
  # 데이터 수집 → 분석 → 보고서 생성
  ```

- [ ] **32-customer-support.py** - 고객 지원 시스템
  ```python
  # 여러 레벨의 지원 에이전트
  # 에스컬레이션 처리
  ```

- [ ] **33-research-team.py** - 연구 팀
  ```python
  # 문헌 수집 → 분석 → 보고서 작성
  ```

- [ ] **34-api-integration.py** - API 통합
  ```python
  # 여러 외부 API 통합
  # 데이터 조화
  ```

---

## 🌟 2025년 11월 최신 기능

### 1. 향상된 병렬 처리

```python
# 여러 에이전트가 동시에 작업
async def parallel_processing():
    results = await asyncio.gather(
        agent1.run(task1),
        agent2.run(task2),
        agent3.run(task3)
    )
    return combine_results(results)
```

### 2. 동적 에이전트 생성

```python
# 런타임에 에이전트 생성/제거
async def create_agents_dynamically():
    agents = []
    for i in range(5):
        agent = AssistantAgent(
            f"agent_{i}",
            model_client=client
        )
        agents.append(agent)
    return agents
```

### 3. 상태 기반 라우팅

```python
# 에이전트 상태에 따라 메시지 라우팅
async def route_message(message, agent_state):
    if agent_state == "busy":
        return await queue.put(message)
    else:
        return await agent.run(message)
```

### 4. 자동 실패 복구

```python
# 실패 시 자동 재시도 + 다른 에이전트 시도
async def robust_execution():
    for agent in agent_pool:
        try:
            return await agent.run(task, timeout=10)
        except Exception:
            continue
    raise AllAgentsFailed()
```

### 5. 메트릭 수집

```python
# 성능 메트릭 자동 수집
metrics = {
    "response_time": measure_time(),
    "tokens_used": track_tokens(),
    "errors": track_errors()
}
```

---

## 📊 실행 체크리스트

### Phase 1: 기본 학습 (1주)

- [ ] 01-hello-world.py ✅
- [ ] 02-simple-chat.py
- [ ] 03-agent-with-tools.py
- [ ] README 작성

### Phase 2: 멀티에이전트 협업 (2주)

- [ ] 04-two-agent-chat.py
- [ ] 05-group-chat.py
- [ ] 06-hierarchical-agents.py
- [ ] 예제 문서 작성

### Phase 3: 병렬 처리 & 통신 (3주)

- [ ] 08-concurrent-tasks.py
- [ ] 09-parallel-stream.py
- [ ] 12-inter-agent-messaging.py
- [ ] 14-pub-sub.py

### Phase 4: 고급 기능 (4주)

- [ ] 24-grpc-distributed.py
- [ ] 26-mcp-basic.py
- [ ] 30-code-review-team.py

### Phase 5: 통합 테스트 (5주)

- [ ] 모든 예제 검증
- [ ] 성능 벤치마크
- [ ] 문서 완성

---

## 🚀 빠른 시작

### 1단계: 기본 설정

```bash
pip install "autogen-agentchat" "autogen-ext[openai]"
export OPENAI_API_KEY="sk-..."
```

### 2단계: Hello World 실행

```bash
python examples/01-hello-world.py
```

### 3단계: 두 에이전트 협업

```bash
python examples/04-two-agent-chat.py
```

### 4단계: 병렬 작업

```bash
python examples/08-concurrent-tasks.py
```

---

## 📚 리소스

- **공식 문서**: https://microsoft.github.io/autogen/
- **GitHub**: https://github.com/microsoft/autogen
- **Discord**: https://aka.ms/autogen-discord
- **블로그**: https://devblogs.microsoft.com/autogen/

---

## 🔄 마이그레이션 (v0.2 → 신버전)

### 주요 변경사항

| 항목 | v0.2 | 신버전 |
|------|------|--------|
| **API** | GroupChat | AgentChat (권장) |
| **런타임** | ThreadPoolExecutor | AsyncIO + gRPC |
| **메시징** | HTTP | gRPC (분산) |
| **MCP** | ❌ | ✅ (완전 지원) |
| **병렬성** | 제한적 | 진정한 비동기 |

### 마이그레이션 가이드

```python
# v0.2 스타일 (레거시)
from autogen import AssistantAgent, GroupChat
group_chat = GroupChat(agents=[...])
manager = GroupChatManager(groupchat=group_chat)

# 신 스타일 (권장)
from autogen_agentchat.agents import AssistantAgent
team = SelectorGroupChat(agents=[...], model_client=client)
```

---

## ⚠️ 주의사항

1. **API 비용**: OpenAI/Azure 사용 시 비용 발생
   - 해결책: Gemini/Ollama 같은 무료 옵션 사용

2. **Rate Limiting**: API 속도 제한 주의
   - 해결책: 동시 요청 수 제한

3. **MCP 설치**: `npm install -g @playwright/mcp@latest` 필요

4. **Python 버전**: 3.10 이상 필요

---

## 🎓 학습 경로

```
기본 개념
   ↓
단일 에이전트 (03-agent-with-tools)
   ↓
두 에이전트 협업 (04-two-agent-chat)
   ↓
그룹 채팅 (05-group-chat)
   ↓
병렬 처리 (08-concurrent-tasks)
   ↓
분산 실행 (24-grpc-distributed)
   ↓
프로덕션 배포 (30-code-review-team)
```

---

**작성자**: GitHub Copilot  
**상태**: ✅ 설계 완료  
**버전**: 1.0.0  
**마지막 업데이트**: 2025년 11월 8일
