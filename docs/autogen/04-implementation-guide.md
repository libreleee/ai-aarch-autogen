# 실제 구현 가이드

## 🎯 개요

본 가이드는 AutoGen 패턴을 현재 `actor_critic.py` 프로젝트에 **단계별로 적용**하는 실무 중심의 가이드입니다. 즉시 적용 가능한 방법부터 고급 패턴까지 순차적으로 다룹니다.

## 📋 적용 로드맵

### Phase 1: 즉시 적용 (1-2일) ✅
- [x] 기본 병렬 처리 (완료)
- [ ] Worker Agent 패턴 강화
- [ ] 에러 처리 및 로깅 개선

### Phase 2: 품질 향상 (1주)
- [ ] Mixture of Agents 부분 적용
- [ ] 핵심 파일 다중 생성
- [ ] 자동 품질 검증

### Phase 3: 완전 통합 (2-3주)
- [ ] AutoGen 프레임워크 도입
- [ ] 고급 협업 패턴
- [ ] 자동 튜닝 시스템

## 🚀 Phase 1: 즉시 적용

### 1. Worker Agent 패턴 강화

현재 `actor_critic.py`에 바로 추가 가능한 개선안:

```python
# actor_critic.py에 추가

class WorkerAgentMixin:
    """Worker Agent 기능을 제공하는 Mixin"""
    
    async def implementation_phase_enhanced(self, design: str) -> Dict[str, Any]:
        """강화된 구현 단계 (Worker Agent 패턴)"""
        print("\n💻 Phase 2: IMPLEMENTATION (Enhanced Workers)")
        print("-" * 80)
        
        file_list = self._extract_file_list(design)
        print(f"  [Orchestrator] Dispatching {len(file_list)} files to workers...")
        
        # Worker Agent 상태 추적
        worker_stats = {
            "total": len(file_list),
            "completed": 0,
            "failed": 0,
            "start_time": time.time()
        }
        
        async def enhanced_worker_agent(worker_id: int, file_info: Dict) -> Dict:
            """개선된 Worker Agent"""
            worker_name = f"Worker-{worker_id}"
            file_name = file_info['name']
            
            try:
                print(f"  [{worker_name}] 🔄 Processing {file_name}...")
                start_time = time.time()
                
                # 파일 생성
                code = await self._generate_file_with_context(
                    file_info, design, worker_id
                )
                
                # 품질 검증
                quality_score = self._quick_quality_check(code, file_name)
                
                # 파일 저장
                file_path = self.project_path / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(code, encoding='utf-8')
                
                elapsed = time.time() - start_time
                worker_stats["completed"] += 1
                
                print(f"  [{worker_name}] ✅ Completed {file_name} "
                      f"({len(code)} bytes, {elapsed:.1f}s, Q:{quality_score:.1f})")
                
                return {
                    "worker_id": worker_id,
                    "file_name": file_name,
                    "status": "success",
                    "code": code,
                    "quality_score": quality_score,
                    "elapsed": elapsed,
                    "error": None
                }
                
            except Exception as e:
                worker_stats["failed"] += 1
                error_msg = str(e)
                
                print(f"  [{worker_name}] ❌ Failed {file_name}: {error_msg}")
                
                return {
                    "worker_id": worker_id,
                    "file_name": file_name,
                    "status": "failed",
                    "code": None,
                    "quality_score": 0.0,
                    "elapsed": 0.0,
                    "error": error_msg
                }
        
        # 모든 Worker 동시 실행
        worker_tasks = [
            enhanced_worker_agent(i, file_info)
            for i, file_info in enumerate(file_list)
        ]
        
        results = await asyncio.gather(*worker_tasks, return_exceptions=True)
        
        # 결과 분석 및 보고
        total_time = time.time() - worker_stats["start_time"]
        success_results = [r for r in results if r.get("status") == "success"]
        failed_results = [r for r in results if r.get("status") == "failed"]
        
        print(f"\n  [Orchestrator] Summary:")
        print(f"    ✅ Successful: {len(success_results)}/{len(file_list)}")
        print(f"    ❌ Failed: {len(failed_results)}")
        print(f"    ⏱️ Total time: {total_time:.2f}s")
        print(f"    📊 Avg quality: {np.mean([r['quality_score'] for r in success_results]):.1f}")
        
        return {
            "approved": len(failed_results) == 0,
            "files": [r["file_name"] for r in success_results],
            "failed": [(r["file_name"], r["error"]) for r in failed_results],
            "stats": {
                "total_files": len(file_list),
                "successful": len(success_results),
                "failed": len(failed_results),
                "total_time": total_time,
                "avg_quality": np.mean([r['quality_score'] for r in success_results]) if success_results else 0
            }
        }
    
    async def _generate_file_with_context(
        self, file_info: Dict, design: str, worker_id: int
    ) -> str:
        """Worker 컨텍스트가 포함된 파일 생성"""
        
        # Worker별 특성화
        worker_traits = {
            0: "최적화에 중점을 둔",
            1: "가독성에 중점을 둔", 
            2: "안정성에 중점을 둔"
        }
        
        trait = worker_traits.get(worker_id % 3, "균형잡힌")
        
        enhanced_prompt = f"""
당신은 {trait} 개발자입니다.

[Worker-{worker_id}] {file_info['name']} 파일을 구현하세요.

설계: {design}
요구사항: {self.requirements}

파일 역할: {file_info.get("description", "구현 파일")}

{trait} 특성을 살려서:
- 완전하고 실행 가능한 코드
- TODOs나 placeholder 없음
- 적절한 에러 처리
- 한국어 docstring

Output format:
```python
# Complete implementation here
```
"""
        
        response = self._generate_content(enhanced_prompt)
        return self._extract_code(response.text)
    
    def _quick_quality_check(self, code: str, file_name: str) -> float:
        """빠른 코드 품질 체크 (0-10점)"""
        
        score = 10.0
        
        # 기본 체크
        if len(code) < 100:
            score -= 3.0  # 너무 짧음
        
        if "TODO" in code or "FIXME" in code:
            score -= 2.0  # placeholder 존재
            
        if not re.search(r'""".*?"""', code, re.DOTALL):
            score -= 1.0  # docstring 없음
            
        if "try:" not in code and "except:" not in code:
            score -= 1.0  # 에러 처리 없음
            
        # 파일 특성별 체크
        if file_name.endswith('.py'):
            if not re.search(r'def |class ', code):
                score -= 2.0  # 함수/클래스 없음
                
        return max(0.0, score)

# ActorCriticTeam에 Mixin 적용
class ActorCriticTeam(WorkerAgentMixin, ActorCriticTeam):
    """Worker Agent 패턴이 적용된 Actor-Critic 팀"""
    
    async def implementation_phase(self, design: str) -> Dict[str, Any]:
        """강화된 구현 단계 사용"""
        return await self.implementation_phase_enhanced(design)
```

### 2. 에러 처리 강화

```python
class ErrorHandlingMixin:
    """강화된 에러 처리 기능"""
    
    async def implementation_phase_with_recovery(self, design: str) -> Dict[str, Any]:
        """복구 메커니즘이 있는 구현 단계"""
        
        # 첫 번째 시도
        primary_result = await self.implementation_phase_enhanced(design)
        
        # 실패한 파일들에 대한 복구 시도
        if primary_result.get("failed"):
            print("\n🔄 Attempting recovery for failed files...")
            
            failed_files = [
                (file_name, error) 
                for file_name, error in primary_result["failed"]
            ]
            
            recovery_results = await self._attempt_recovery(
                failed_files, design
            )
            
            # 결과 병합
            primary_result["files"].extend(recovery_results["recovered"])
            primary_result["failed"] = recovery_results["still_failed"]
            primary_result["approved"] = len(recovery_results["still_failed"]) == 0
        
        return primary_result
    
    async def _attempt_recovery(
        self, failed_files: List[tuple], design: str
    ) -> Dict[str, List]:
        """실패한 파일들에 대한 복구 시도"""
        
        async def recovery_worker(file_name: str, original_error: str) -> tuple:
            try:
                print(f"  [Recovery] Retrying {file_name}...")
                
                # 단순화된 프롬프트로 재시도
                simplified_prompt = f"""
간단하고 기본적인 {file_name} 파일을 구현하세요.

원본 에러: {original_error}

설계: {design[:500]}...

요구사항:
- 최소한의 기본 구조만 구현
- 복잡한 기능은 제외
- 안전하고 단순한 코드

Output format:
```python
# Simple implementation
```
"""
                
                response = self._generate_content(simplified_prompt)
                code = self._extract_code(response.text)
                
                # 파일 저장
                file_path = self.project_path / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(code, encoding='utf-8')
                
                return (file_name, "recovered")
                
            except Exception as e:
                return (file_name, f"recovery_failed: {e}")
        
        # 복구 작업 병렬 실행
        recovery_tasks = [
            recovery_worker(file_name, error) 
            for file_name, error in failed_files
        ]
        
        recovery_results = await asyncio.gather(*recovery_tasks, return_exceptions=True)
        
        recovered = [r[0] for r in recovery_results if r[1] == "recovered"]
        still_failed = [(r[0], r[1]) for r in recovery_results if r[1] != "recovered"]
        
        print(f"  [Recovery] ✅ Recovered: {len(recovered)}, ❌ Still failed: {len(still_failed)}")
        
        return {
            "recovered": recovered,
            "still_failed": still_failed
        }
```

## 🔄 Phase 2: 품질 향상

### 핵심 파일 MoA 적용

```python
class SelectiveMoAMixin:
    """선택적 MoA 패턴 적용"""
    
    async def implementation_phase_selective_moa(self, design: str) -> Dict[str, Any]:
        """핵심 파일에만 MoA 적용"""
        
        file_list = self._extract_file_list(design)
        
        # 핵심 파일 식별
        critical_files, regular_files = self._categorize_files(file_list)
        
        print(f"  [Selective MoA] Critical: {len(critical_files)}, Regular: {len(regular_files)}")
        
        # 병렬 실행: 핵심 파일은 MoA, 일반 파일은 단순 생성
        critical_task = self._generate_critical_files_moa(critical_files, design)
        regular_task = self._generate_regular_files_parallel(regular_files, design)
        
        critical_result, regular_result = await asyncio.gather(
            critical_task, regular_task, return_exceptions=True
        )
        
        return self._merge_selective_results(critical_result, regular_result)
    
    def _categorize_files(self, file_list: List[Dict]) -> tuple:
        """파일을 핵심/일반으로 분류"""
        
        critical_patterns = [
            r'.*service.*\.py$',
            r'.*model.*\.py$', 
            r'.*controller.*\.py$',
            r'.*manager.*\.py$',
            r'.*handler.*\.py$'
        ]
        
        critical_files = []
        regular_files = []
        
        for file_info in file_list:
            file_name = file_info['name']
            
            is_critical = any(
                re.match(pattern, file_name, re.IGNORECASE)
                for pattern in critical_patterns
            )
            
            if is_critical:
                critical_files.append(file_info)
            else:
                regular_files.append(file_info)
        
        return critical_files, regular_files
    
    async def _generate_critical_files_moa(
        self, critical_files: List[Dict], design: str
    ) -> Dict[str, Any]:
        """핵심 파일을 MoA 패턴으로 생성"""
        
        print(f"  [MoA] Processing {len(critical_files)} critical files...")
        
        async def moa_for_file(file_info: Dict) -> Dict:
            # Layer 1: 3가지 관점으로 생성
            perspectives = ["performance", "maintainability", "simplicity"]
            
            layer1_tasks = [
                self._generate_with_perspective(file_info, design, perspective)
                for perspective in perspectives
            ]
            
            implementations = await asyncio.gather(*layer1_tasks)
            
            # Layer 2: 최선 합성
            best_code = await self._synthesize_implementations(
                file_info, implementations
            )
            
            return {
                "file_name": file_info['name'],
                "code": best_code,
                "method": "moa"
            }
        
        moa_tasks = [moa_for_file(f) for f in critical_files]
        results = await asyncio.gather(*moa_tasks, return_exceptions=True)
        
        return {"critical_files": results, "method": "moa"}
```

## 📊 Phase 3: 완전 통합

### AutoGen 프레임워크 통합

```python
# 실제 AutoGen 설치 및 설정
"""
pip install pyautogen
"""

import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

class AutoGenIntegration:
    """AutoGen 프레임워크 완전 통합"""
    
    def __init__(self, project_path: Path, requirements: str):
        self.project_path = project_path
        self.requirements = requirements
        self.setup_autogen_agents()
    
    def setup_autogen_agents(self):
        """AutoGen 에이전트 설정"""
        
        config_list = [
            {
                "model": "gpt-4",
                "api_key": os.getenv("OPENAI_API_KEY")
            }
        ]
        
        # 전문 에이전트들 정의
        self.architect = AssistantAgent(
            name="architect",
            system_message="""
당신은 시니어 소프트웨어 아키텍트입니다.
프로젝트 설계와 전체 구조를 담당합니다.
""",
            llm_config={"config_list": config_list}
        )
        
        self.developer = AssistantAgent(
            name="developer", 
            system_message="""
당신은 시니어 개발자입니다.
고품질의 Python 코드를 작성합니다.
""",
            llm_config={"config_list": config_list}
        )
        
        self.tester = AssistantAgent(
            name="tester",
            system_message="""
당신은 QA 엔지니어입니다.
포괄적인 테스트를 작성합니다.
""",
            llm_config={"config_list": config_list}
        )
        
        self.reviewer = AssistantAgent(
            name="reviewer",
            system_message="""
당신은 코드 리뷰어입니다.
코드 품질과 표준을 검증합니다.
""",
            llm_config={"config_list": config_list}
        )
        
        # 사용자 프록시
        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config={"work_dir": str(self.project_path)}
        )
        
        # 그룹 채팅 설정
        self.group_chat = GroupChat(
            agents=[self.architect, self.developer, self.tester, self.reviewer, self.user_proxy],
            messages=[],
            max_round=20
        )
        
        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config={"config_list": config_list}
        )
    
    async def run_autogen_workflow(self) -> Dict[str, Any]:
        """AutoGen을 이용한 완전한 워크플로우"""
        
        workflow_prompt = f"""
프로젝트 요구사항: {self.requirements}

다음 단계로 프로젝트를 구현하세요:

1. [Architect] 전체 설계 및 파일 구조 정의
2. [Developer] 각 파일 구현 (병렬 가능)
3. [Tester] 테스트 코드 작성
4. [Reviewer] 코드 리뷰 및 품질 검증

각 에이전트는 자신의 전문성을 활용하여 최고 품질의 결과를 제공하세요.
"""
        
        # AutoGen 대화 시작
        chat_result = self.user_proxy.initiate_chat(
            self.manager,
            message=workflow_prompt
        )
        
        return {
            "autogen_result": chat_result,
            "messages": self.group_chat.messages,
            "agents_used": len(self.group_chat.agents)
        }
```

## 📈 적용 순서 및 테스트

### 1. 단계별 적용

```python
async def apply_autogen_patterns_gradually():
    """단계별 패턴 적용"""
    
    # Step 1: Worker Agent 패턴 테스트
    print("=== Step 1: Worker Agent Pattern ===")
    team = ActorCriticTeam(project_path, requirements)
    result1 = await team.implementation_phase_enhanced(design)
    
    # Step 2: 선택적 MoA 테스트  
    print("=== Step 2: Selective MoA Pattern ===")
    result2 = await team.implementation_phase_selective_moa(design)
    
    # Step 3: 완전 AutoGen 통합 테스트
    print("=== Step 3: Full AutoGen Integration ===")
    autogen_integration = AutoGenIntegration(project_path, requirements)
    result3 = await autogen_integration.run_autogen_workflow()
    
    return {
        "step1_worker": result1,
        "step2_selective_moa": result2, 
        "step3_full_autogen": result3
    }
```

### 2. 성능 비교 테스트

```python
async def benchmark_all_patterns():
    """모든 패턴의 성능 벤치마크"""
    
    patterns = {
        "baseline": lambda: team.implementation_phase_original(design),
        "worker_agent": lambda: team.implementation_phase_enhanced(design),
        "selective_moa": lambda: team.implementation_phase_selective_moa(design),
        "full_autogen": lambda: autogen_integration.run_autogen_workflow()
    }
    
    results = {}
    
    for pattern_name, pattern_func in patterns.items():
        print(f"\n=== Benchmarking {pattern_name} ===")
        
        start_time = time.time()
        result = await pattern_func()
        elapsed = time.time() - start_time
        
        results[pattern_name] = {
            "elapsed_time": elapsed,
            "files_generated": len(result.get("files", [])),
            "success_rate": result.get("stats", {}).get("successful", 0) / 
                           result.get("stats", {}).get("total_files", 1),
            "avg_quality": result.get("stats", {}).get("avg_quality", 0)
        }
    
    return results
```

## 🔗 다음 단계

- [05-performance-comparison.md](./05-performance-comparison.md): 상세 성능 비교
- [examples/](./examples/): 완전한 구현 예제들
- [06-crewai-comparison.md](./06-crewai-comparison.md): CrewAI와의 비교

---

*생성일: 2025-11-06*
*업데이트: 실무 적용 가이드 완성*