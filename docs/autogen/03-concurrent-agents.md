# Concurrent Agents 패턴 가이드

## 🎯 개요

Concurrent Agents 패턴은 **독립적인 작업을 수행하는 여러 에이전트를 동시에 실행**하는 방식입니다. MoA 패턴보다 단순하면서도 효과적인 성능 향상을 제공합니다.

## 🏗️ 아키텍처

```
Input Tasks
     ↓
┌─────────────────────────────────────┐
│        Task Distribution            │
└─────────────────────────────────────┘
     ↓         ↓         ↓
┌─────────┐ ┌─────────┐ ┌─────────┐
│Agent A  │ │Agent B  │ │Agent C  │
│(Task 1) │ │(Task 2) │ │(Task 3) │
└─────────┘ └─────────┘ └─────────┘
     ↓         ↓         ↓
┌─────────────────────────────────────┐
│        Result Aggregation           │
└─────────────────────────────────────┘
     ↓
Final Output
```

## 🔧 핵심 구현 패턴

### 1. Topic-based Routing 패턴

```python
from dataclasses import dataclass
from typing import Protocol, Any
import asyncio

# Task 정의
@dataclass
class ImplementationTask:
    design: str
    file_list: List[Dict]
    worker_id: int = 0

@dataclass  
class TestingTask:
    files: List[str]
    test_type: str = "unit"

@dataclass
class DocumentationTask:
    requirements: str
    files: List[str]
    format: str = "markdown"

# Agent Protocol 정의
class TaskAgent(Protocol):
    async def execute(self, task: Any) -> Dict[str, Any]:
        ...

class ConcurrentAgentOrchestrator:
    """동시 실행 에이전트 오케스트레이터"""
    
    def __init__(self):
        self.agents = {
            "implementation": ImplementationAgent(),
            "testing": TestingAgent(), 
            "documentation": DocumentationAgent()
        }
    
    async def run_phases_concurrent(
        self, 
        design: str, 
        requirements: str
    ) -> Dict[str, Any]:
        """Phase 2-4를 완전히 독립적으로 병렬 실행"""
        
        print("\n🚀 [CONCURRENT] Executing Phase 2-4 simultaneously...")
        
        # Task 생성
        impl_task = ImplementationTask(
            design=design,
            file_list=self._extract_file_list(design)
        )
        
        test_task = TestingTask(
            files=[],  # 파일 목록은 런타임에 결정
            test_type="comprehensive"
        )
        
        docs_task = DocumentationTask(
            requirements=requirements,
            files=[],
            format="markdown"
        )
        
        # 완전히 독립적으로 실행
        start_time = time.time()
        
        results = await asyncio.gather(
            self.agents["implementation"].execute(impl_task),
            self.agents["testing"].execute(test_task),
            self.agents["documentation"].execute(docs_task),
            return_exceptions=True
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ All phases completed in {execution_time:.2f}s")
        
        return self._aggregate_results(results, execution_time)
```

### 2. Agent 구현체

```python
class ImplementationAgent:
    """파일 구현 전담 에이전트"""
    
    async def execute(self, task: ImplementationTask) -> Dict[str, Any]:
        print(f"  [Impl-Agent] Processing {len(task.file_list)} files...")
        
        # Worker Agent 패턴 적용
        async def file_worker(worker_id: int, file_info: Dict) -> tuple:
            try:
                print(f"    [Worker-{worker_id}] Generating {file_info['name']}...")
                
                code = await self._generate_file_code(file_info, task.design)
                
                # 파일 저장
                await self._save_file(file_info['name'], code)
                
                return (file_info['name'], code, None)
                
            except Exception as e:
                return (file_info['name'], None, e)
        
        # 모든 파일을 병렬 생성
        worker_tasks = [
            file_worker(i, file_info)
            for i, file_info in enumerate(task.file_list)
        ]
        
        results = await asyncio.gather(*worker_tasks, return_exceptions=True)
        
        # 결과 분석
        successful = [r for r in results if r[2] is None]
        failed = [r for r in results if r[2] is not None]
        
        return {
            "agent": "implementation",
            "successful_files": [r[0] for r in successful],
            "failed_files": [(r[0], str(r[2])) for r in failed],
            "total_files": len(task.file_list),
            "success_rate": len(successful) / len(task.file_list)
        }

class TestingAgent:
    """테스트 생성 전담 에이전트"""
    
    async def execute(self, task: TestingTask) -> Dict[str, Any]:
        print(f"  [Test-Agent] Generating {task.test_type} tests...")
        
        # 동적으로 파일 목록 발견
        project_files = await self._discover_python_files()
        
        # 병렬 테스트 생성
        test_tasks = [
            self._generate_test_for_file(file_path, task.test_type)
            for file_path in project_files
        ]
        
        test_results = await asyncio.gather(*test_tasks, return_exceptions=True)
        
        successful_tests = [r for r in test_results if not isinstance(r, Exception)]
        
        return {
            "agent": "testing",
            "test_files_generated": len(successful_tests),
            "test_type": task.test_type,
            "coverage_target": "80%"
        }

class DocumentationAgent:
    """문서화 전담 에이전트"""
    
    async def execute(self, task: DocumentationTask) -> Dict[str, Any]:
        print(f"  [Docs-Agent] Generating {task.format} documentation...")
        
        # 병렬 문서 생성
        doc_tasks = [
            self._generate_readme(),
            self._generate_api_docs(),
            self._generate_user_guide(),
            self._generate_deployment_guide()
        ]
        
        doc_results = await asyncio.gather(*doc_tasks, return_exceptions=True)
        
        return {
            "agent": "documentation", 
            "documents_generated": len([r for r in doc_results if not isinstance(r, Exception)]),
            "format": task.format
        }
```

### 3. 에러 격리 및 복구

```python
class ConcurrentAgentManager:
    """동시 실행 에이전트 관리자 (에러 처리 강화)"""
    
    async def run_with_fallback(self, tasks: List[Any]) -> Dict[str, Any]:
        """Fallback 메커니즘이 있는 동시 실행"""
        
        primary_results = await asyncio.gather(
            *[agent.execute(task) for agent, task in tasks],
            return_exceptions=True
        )
        
        # 실패한 작업 식별
        failed_tasks = []
        successful_results = []
        
        for i, result in enumerate(primary_results):
            if isinstance(result, Exception):
                failed_tasks.append((i, tasks[i]))
                print(f"  [Error] Task {i} failed: {result}")
            else:
                successful_results.append(result)
        
        # 실패한 작업에 대한 Fallback 실행
        if failed_tasks:
            print(f"  [Fallback] Retrying {len(failed_tasks)} failed tasks...")
            
            fallback_results = await self._run_fallback_tasks(failed_tasks)
            successful_results.extend(fallback_results)
        
        return {
            "successful": len(successful_results),
            "failed": len(failed_tasks),
            "results": successful_results
        }
    
    async def _run_fallback_tasks(self, failed_tasks: List[tuple]) -> List[Dict]:
        """실패한 작업에 대한 Fallback 처리"""
        
        fallback_results = []
        
        for task_id, (agent, task) in failed_tasks:
            try:
                # 단순화된 버전으로 재시도
                simplified_task = self._simplify_task(task)
                result = await agent.execute_simple(simplified_task)
                fallback_results.append(result)
                
            except Exception as e:
                print(f"  [Fallback Failed] Task {task_id}: {e}")
        
        return fallback_results
```

## 📊 CrewAI 스타일 적용

AutoGen의 Concurrent 패턴을 CrewAI 스타일로 단순화:

```python
class CrewAIStyleConcurrent:
    """CrewAI 스타일의 간단한 동시 실행"""
    
    def __init__(self):
        self.agents = {
            "coder": {"role": "Senior Developer", "async_execution": True},
            "tester": {"role": "QA Engineer", "async_execution": True}, 
            "documenter": {"role": "Technical Writer", "async_execution": True}
        }
    
    async def execute_crew(self, project_requirements: str):
        """CrewAI 방식의 async_execution"""
        
        # Task 정의 (CrewAI Task와 유사)
        tasks = [
            {
                "agent": "coder",
                "description": "Implement all required files",
                "async_execution": True
            },
            {
                "agent": "tester", 
                "description": "Generate comprehensive tests",
                "async_execution": True
            },
            {
                "agent": "documenter",
                "description": "Create project documentation", 
                "async_execution": True
            }
        ]
        
        # 모든 Task를 병렬 실행 (CrewAI의 async_execution과 동일)
        async def execute_task(task_config: Dict):
            agent_name = task_config["agent"]
            description = task_config["description"]
            
            return await self._run_agent_task(agent_name, description, project_requirements)
        
        results = await asyncio.gather(
            *[execute_task(task) for task in tasks if task["async_execution"]],
            return_exceptions=True
        )
        
        return self._format_crew_results(results)
```

## 🎯 현재 프로젝트 적용

### actor_critic.py 통합

```python
class ActorCriticConcurrent(ActorCriticTeam):
    """Concurrent Agents 패턴이 적용된 Actor-Critic"""
    
    def __init__(self, project_path: Path, requirements: str):
        super().__init__(project_path, requirements)
        self.orchestrator = ConcurrentAgentOrchestrator()
    
    async def run_enhanced_workflow(self) -> Dict[str, Any]:
        """개선된 워크플로우 (Concurrent Agents)"""
        
        # Phase 0-1: 순차 실행 (의존성 있음)
        estimate = await self.estimate_cost()
        design_result = await self.design_phase()
        
        # Phase 2-4: 완전 병렬 실행 (독립적)
        concurrent_results = await self.orchestrator.run_phases_concurrent(
            design_result["design"], 
            self.requirements
        )
        
        return {
            "estimate": estimate,
            "design": design_result, 
            "concurrent_phases": concurrent_results
        }
```

## 📈 성능 비교

| 패턴 | 구현 복잡도 | 처리 시간 | 에러 처리 | 확장성 |
|------|-------------|-----------|-----------|--------|
| 순차 실행 | ⭐ | 60초 | 기본 | 낮음 |
| 기본 병렬 | ⭐⭐ | 25초 | 기본 | 중간 |
| Concurrent Agents | ⭐⭐⭐ | 20초 | 강화 | 높음 |
| MoA (품질 중심) | ⭐⭐⭐⭐ | 35초 | 최고 | 최고 |

## ✅ 적용 권장사항

### 즉시 적용 (Worker Agent 강화)
```python
# 현재 구현에 바로 추가 가능
async def implementation_phase_with_workers(self, design: str):
    file_list = self._extract_file_list(design)
    
    # Worker Agent 패턴 적용
    async def enhanced_worker(worker_id: int, file_info: Dict):
        try:
            print(f"  [Worker-{worker_id}] Processing {file_info['name']}...")
            result = await self._generate_file_async(file_info, design)
            print(f"  [Worker-{worker_id}] ✓ Completed")
            return result
        except Exception as e:
            print(f"  [Worker-{worker_id}] ✗ Failed: {e}")
            raise
    
    # 병렬 실행 + 개선된 로깅
    tasks = [enhanced_worker(i, f) for i, f in enumerate(file_list)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return self._process_worker_results(results)
```

## 🔗 다음 단계

- [04-implementation-guide.md](./04-implementation-guide.md): 실제 적용 단계별 가이드
- [examples/concurrent-agents.py](./examples/concurrent-agents.py): 완전한 구현 예제
- [05-performance-comparison.md](./05-performance-comparison.md): 성능 벤치마크

---

*생성일: 2025-11-06*
*업데이트: Concurrent Agents 패턴 완료*