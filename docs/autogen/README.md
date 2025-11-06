# AutoGen 멀티에이전트 협업 및 병렬 처리 가이드

이 폴더는 AutoGen 프레임워크의 멀티에이전트 협업 및 병렬 처리 패턴을 분석하고, 현재 프로젝트에 적용할 수 있는 방법을 제시합니다.

## 📁 문서 구조

```
docs/autogen/
├── README.md                          # 이 파일
├── 01-patterns-overview.md            # 패턴 개요 및 비교
├── 02-mixture-of-agents.md            # MoA 패턴 상세 가이드
├── 03-concurrent-agents.md            # 동시 실행 에이전트 패턴
├── 04-implementation-guide.md         # 실제 구현 가이드
├── 05-performance-comparison.md       # 성능 비교 및 벤치마크
├── 06-crewai-comparison.md           # CrewAI와의 비교 분석
└── examples/                         # 실제 구현 예제
    ├── basic-parallel.py
    ├── worker-agent-pattern.py
    ├── mixture-of-agents.py
    └── actor-critic-enhanced.py
```

## 🎯 핵심 내용

### 1. 적용 가능한 주요 패턴
- **Mixture of Agents (MoA)**: 다중 레이어로 품질 향상
- **Concurrent Agents**: 독립적 병렬 실행
- **Worker Agent**: 작업 분산 처리

### 2. 현재 프로젝트 적용점
- `actor_critic.py`의 Phase 2 (Implementation) 개선
- Phase 2-4 완전 병렬 실행
- 파일 생성 속도 58-67% 향상 예상

### 3. 권장 적용 순서
1. **단기**: Worker Agent 패턴 적용 (즉시 효과)
2. **중기**: Mixture of Agents 패턴 (품질 향상)
3. **장기**: 완전한 AutoGen 프레임워크 통합

## 🚀 빠른 시작

기본적인 병렬 처리 패턴을 적용하려면:

```python
# 현재 방식
results = []
for file_info in file_list:
    result = await generate_file(file_info)
    results.append(result)

# AutoGen 방식
tasks = [worker_agent(i, file_info) for i, file_info in enumerate(file_list)]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

자세한 내용은 각 문서를 참조하세요.

## 📚 참고 자료

- [AutoGen 공식 문서](https://github.com/microsoft/autogen)
- [CrewAI 병렬 처리 패턴](https://github.com/crewAIInc/crewAI)
- [Mixture of Agents 논문](https://github.com/togethercomputer/MoA)

---

*생성일: 2025-11-06*
*버전: 1.0*