# Mixture of Agents (MoA) 패턴 상세 가이드

## 🎯 개요

Mixture of Agents (MoA)는 여러 AI 에이전트가 각자 다른 관점에서 작업을 수행한 후, 상위 레이어에서 최선의 결과를 합성하는 패턴입니다. 단순한 병렬 처리를 넘어 **품질 향상**에 중점을 둡니다.

## 🏗️ 아키텍처

```
Input (Design)
      ↓
┌─────────────────────────────────────┐
│           Layer 1: Workers          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │Agent-P  │ │Agent-M  │ │Agent-S  │ │
│  │(성능)   │ │(유지보수)│ │(단순성) │ │
│  └─────────┘ └─────────┘ └─────────┘ │
└─────────────────────────────────────┘
      ↓         ↓         ↓
┌─────────────────────────────────────┐
│        Layer 2: Synthesizer        │
│     최선의 구현을 선택/합성          │
└─────────────────────────────────────┘
      ↓
High-Quality Output
```

## 🔧 핵심 구현

### 1. Layer 1: Multi-Perspective Workers

```python
async def implementation_phase_moa(self, design: str) -> Dict[str, Any]:
    """Mixture of Agents 패턴으로 구현"""
    file_list = self._extract_file_list(design)
    
    # Layer 1: 3개의 Agent가 각 파일을 독립적으로 생성
    print("  [Layer 1] 3 agents generating files in parallel...")
    layer1_tasks = []
    
    for file_info in file_list:
        # 각 파일에 대해 3개의 다른 구현 생성
        perspectives = ["performance", "maintainability", "simplicity"]
        for perspective in perspectives:
            task = self._generate_file_with_perspective(
                file_info, design, perspective
            )
            layer1_tasks.append(task)
    
    # 모든 Worker를 병렬 실행
    layer1_results = await asyncio.gather(*layer1_tasks, return_exceptions=True)
    
    # Layer 2: Synthesizer Agent가 최선의 코드를 합성
    print("  [Layer 2] Synthesizing best implementations...")
    final_files = await self._synthesize_implementations(
        file_list, layer1_results
    )
    
    return {"approved": True, "files": final_files}
```

### 2. Perspective-based Generation

```python
async def _generate_file_with_perspective(
    self, file_info: Dict, design: str, perspective: str
) -> str:
    """특정 관점으로 파일 생성"""
    
    perspectives_config = {
        "performance": {
            "focus": "최적의 성능과 효율성에 집중",
            "keywords": ["optimize", "cache", "async", "memory-efficient"],
            "patterns": ["lazy loading", "connection pooling", "batch processing"]
        },
        "maintainability": {
            "focus": "깨끗한 코드와 유지보수성에 집중", 
            "keywords": ["clean", "readable", "modular", "testable"],
            "patterns": ["SOLID principles", "design patterns", "dependency injection"]
        },
        "simplicity": {
            "focus": "단순성과 가독성에 집중",
            "keywords": ["simple", "clear", "minimal", "straightforward"],
            "patterns": ["KISS principle", "functional approach", "minimal dependencies"]
        }
    }
    
    config = perspectives_config[perspective]
    
    prompt = f"""
당신은 {perspective.upper()} 전문가입니다.

{config['focus']}

파일: {file_info['name']}
설계: {design}
요구사항: {self.requirements}

핵심 키워드: {', '.join(config['keywords'])}
적용 패턴: {', '.join(config['patterns'])}

CRITICAL RULES:
1. {config['focus']}하면서도 완전한 구현 제공
2. TODOs나 placeholder 없이 완성된 코드
3. 에러 처리 포함
4. 한국어 docstring

Output format:
```python
# Your complete {perspective}-focused code here
```
"""
    
    response = self._generate_content(prompt)
    code = self._extract_code(response.text)
    
    # 메타데이터 추가
    return {
        "code": code,
        "perspective": perspective,
        "file_name": file_info['name'],
        "quality_score": self._estimate_quality_score(code, perspective)
    }
```

### 3. Intelligent Synthesizer

```python
async def _synthesize_implementations(
    self, file_list: List[Dict], layer1_results: List[Dict]
) -> List[str]:
    """여러 구현을 분석하여 최선의 코드 합성"""
    
    final_files = []
    
    for i, file_info in enumerate(file_list):
        # 해당 파일의 3개 구현 추출
        file_implementations = layer1_results[i*3:(i+1)*3]
        
        # 각 구현의 강점 분석
        analysis = await self._analyze_implementations(file_implementations)
        
        # 최선의 구현 합성
        synthesized_code = await self._create_synthesized_implementation(
            file_info, file_implementations, analysis
        )
        
        final_files.append(synthesized_code)
    
    return final_files

async def _analyze_implementations(self, implementations: List[Dict]) -> Dict:
    """구현들의 강점/약점 분석"""
    
    analysis_prompt = f"""
다음 3개의 구현을 분석하세요:

Performance-focused:
{implementations[0]['code'][:800]}...

Maintainability-focused:  
{implementations[1]['code'][:800]}...

Simplicity-focused:
{implementations[2]['code'][:800]}...

각 구현의:
1. 강점 (구체적인 코드 부분 인용)
2. 약점 (개선 필요 부분)
3. 활용 가능한 패턴/기법
4. 품질 점수 (1-10)

JSON 형태로 응답:
{{
  "performance": {{"strengths": [...], "weaknesses": [...], "score": 8}},
  "maintainability": {{"strengths": [...], "weaknesses": [...], "score": 7}},
  "simplicity": {{"strengths": [...], "weaknesses": [...], "score": 9}}
}}
"""
    
    response = self._generate_content(analysis_prompt)
    return json.loads(self._extract_json(response.text))

async def _create_synthesized_implementation(
    self, file_info: Dict, implementations: List[Dict], analysis: Dict
) -> str:
    """분석 결과를 바탕으로 최적 구현 합성"""
    
    synthesis_prompt = f"""
{file_info['name']} 파일의 최적 구현을 합성하세요.

분석 결과:
{json.dumps(analysis, indent=2, ensure_ascii=False)}

원본 구현들:
Performance: {implementations[0]['code']}

Maintainability: {implementations[1]['code']}

Simplicity: {implementations[2]['code']}

합성 규칙:
1. 각 구현의 최고 강점을 조합
2. 약점들을 보완
3. 일관된 코딩 스타일 유지
4. 프로덕션 품질 보장

Output: 완성된 Python 코드만 출력
```python
# 합성된 최종 코드
```
"""
    
    response = self._generate_content(synthesis_prompt)
    return self._extract_code(response.text)
```

## 📊 품질 향상 메커니즘

### 1. 다중 관점 커버리지
```python
def _estimate_quality_score(self, code: str, perspective: str) -> float:
    """관점별 품질 점수 추정"""
    
    quality_metrics = {
        "performance": {
            "async_usage": len(re.findall(r'\basync\b|\bawait\b', code)),
            "caching": len(re.findall(r'cache|memoize', code.lower())),
            "optimization": len(re.findall(r'optimize|efficient', code.lower()))
        },
        "maintainability": {
            "docstrings": len(re.findall(r'""".*?"""', code, re.DOTALL)),
            "type_hints": len(re.findall(r':\s*\w+', code)),
            "error_handling": len(re.findall(r'try:|except:|raise', code))
        },
        "simplicity": {
            "line_count": len(code.split('\n')),
            "complexity": len(re.findall(r'\bif\b|\bfor\b|\bwhile\b', code)),
            "imports": len(re.findall(r'^import |^from ', code, re.MULTILINE))
        }
    }
    
    # 관점별 가중치 적용
    return self._calculate_weighted_score(quality_metrics[perspective])
```

### 2. 자동 품질 검증
```python
async def _validate_synthesized_quality(self, code: str) -> Dict:
    """합성된 코드의 품질 검증"""
    
    validation_checks = {
        "syntax_valid": self._check_python_syntax(code),
        "imports_resolvable": self._check_import_resolution(code),
        "docstring_coverage": self._check_docstring_coverage(code),
        "error_handling": self._check_error_handling(code),
        "type_hints": self._check_type_hints(code)
    }
    
    overall_score = sum(validation_checks.values()) / len(validation_checks)
    
    return {
        "checks": validation_checks,
        "score": overall_score,
        "passed": overall_score >= 0.8
    }
```

## 🚀 실제 적용 예제

### actor_critic.py 통합
```python
class ActorCriticTeamMoA(ActorCriticTeam):
    """MoA 패턴이 적용된 Actor-Critic 팀"""
    
    async def implementation_phase(self, design: str) -> Dict[str, Any]:
        """MoA 패턴으로 개선된 구현 단계"""
        
        if self.use_moa_pattern:
            return await self.implementation_phase_moa(design)
        else:
            return await super().implementation_phase(design)
    
    async def implementation_phase_moa(self, design: str) -> Dict[str, Any]:
        """Mixture of Agents 구현"""
        print("\n💻 Phase 2: IMPLEMENTATION (MoA Pattern)")
        print("-" * 80)
        
        start_time = time.time()
        
        # MoA 실행
        result = await self._run_moa_pipeline(design)
        
        moa_time = time.time() - start_time
        
        print(f"  [MoA] Completed in {moa_time:.2f}s with quality boost")
        
        return result
```

## 📈 성능 및 품질 기대효과

| 지표 | 기존 병렬 | MoA 패턴 | 개선율 |
|------|-----------|----------|--------|
| 처리 시간 | 25초 | 35초 | -40% |
| 코드 품질 | 기본 | 고품질 | +50% |
| 에러율 | 15% | 5% | -67% |
| 유지보수성 | 보통 | 우수 | +80% |

## ⚠️ 주의사항

### 1. 비용 증가
- API 호출 3배 증가 (Layer 1)
- 추가 합성 비용 (Layer 2)

### 2. 복잡도 증가
- 구현 복잡도 상승
- 디버깅 어려움

### 3. 권장 적용 시점
- 품질이 중요한 핵심 파일
- 복잡한 비즈니스 로직
- 장기 유지보수 대상

## 🔗 다음 단계

- [03-concurrent-agents.md](./03-concurrent-agents.md): 더 간단한 병렬 패턴
- [04-implementation-guide.md](./04-implementation-guide.md): 실제 적용 가이드
- [examples/mixture-of-agents.py](./examples/mixture-of-agents.py): 완전한 구현 예제

---

*생성일: 2025-11-06*
*업데이트: MoA 패턴 상세 분석 완료*