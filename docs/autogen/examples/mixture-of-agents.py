"""
Mixture of Agents (MoA) 패턴 예제

AutoGen의 핵심 패턴인 MoA를 구현한 예제입니다.
여러 Agent가 다른 관점에서 작업한 후, Synthesizer가 최선의 결과를 합성합니다.
"""

import asyncio
import time
import json
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class Perspective(Enum):
    """Agent 관점"""
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"  
    SIMPLICITY = "simplicity"
    SECURITY = "security"


@dataclass
class Implementation:
    """단일 구현 결과"""
    perspective: Perspective
    file_name: str
    code: str
    quality_score: float
    reasoning: str
    strengths: List[str]
    weaknesses: List[str]


@dataclass
class SynthesizedResult:
    """합성된 최종 결과"""
    file_name: str
    final_code: str
    quality_score: float
    source_perspectives: List[Perspective]
    synthesis_reasoning: str
    improvement_over_best: float


class PerspectiveAgent:
    """특정 관점의 전문 Agent"""
    
    def __init__(self, perspective: Perspective):
        self.perspective = perspective
        self.completed_tasks = 0
        
        # 관점별 특성 정의
        self.characteristics = {
            Perspective.PERFORMANCE: {
                "focus": "최적의 성능과 효율성",
                "keywords": ["optimize", "cache", "async", "memory-efficient"],
                "patterns": ["lazy loading", "connection pooling", "batch processing"],
                "quality_weight": {"speed": 0.4, "memory": 0.3, "scalability": 0.3}
            },
            Perspective.MAINTAINABILITY: {
                "focus": "깨끗한 코드와 유지보수성", 
                "keywords": ["clean", "readable", "modular", "testable"],
                "patterns": ["SOLID principles", "design patterns", "dependency injection"],
                "quality_weight": {"readability": 0.4, "modularity": 0.3, "testability": 0.3}
            },
            Perspective.SIMPLICITY: {
                "focus": "단순성과 가독성",
                "keywords": ["simple", "clear", "minimal", "straightforward"],
                "patterns": ["KISS principle", "functional approach", "minimal dependencies"],
                "quality_weight": {"simplicity": 0.5, "clarity": 0.3, "minimal_deps": 0.2}
            },
            Perspective.SECURITY: {
                "focus": "보안성과 안전성",
                "keywords": ["secure", "validate", "sanitize", "encrypt"],
                "patterns": ["input validation", "secure coding", "encryption"],
                "quality_weight": {"security": 0.5, "validation": 0.3, "safety": 0.2}
            }
        }
    
    async def generate_implementation(
        self, 
        file_name: str, 
        requirements: str,
        complexity: str = "medium"
    ) -> Implementation:
        """관점별 구현 생성"""
        
        char = self.characteristics[self.perspective]
        
        print(f"    [{self.perspective.value.title()}] 🧠 Analyzing {file_name}")
        
        # 관점별 처리 시간 (복잡도에 따라)
        processing_times = {
            Perspective.PERFORMANCE: {"simple": 1.5, "medium": 2.0, "complex": 3.0},
            Perspective.MAINTAINABILITY: {"simple": 1.0, "medium": 1.5, "complex": 2.5},
            Perspective.SIMPLICITY: {"simple": 0.8, "medium": 1.2, "complex": 2.0},
            Perspective.SECURITY: {"simple": 1.2, "medium": 1.8, "complex": 2.8}
        }
        
        processing_time = processing_times[self.perspective].get(complexity, 1.5)
        
        # 구현 생성 시뮬레이션
        await asyncio.sleep(processing_time)
        
        # 코드 생성 (시뮬레이션)
        code = self._generate_perspective_code(file_name, requirements, char)
        
        # 품질 점수 계산
        quality_score = self._calculate_quality_score(code, char)
        
        # 강점/약점 분석
        strengths, weaknesses = self._analyze_implementation(code, char)
        
        # 추론 설명
        reasoning = self._generate_reasoning(file_name, char)
        
        print(f"    [{self.perspective.value.title()}] ✅ Generated {file_name} "
              f"(Q:{quality_score:.1f}, {len(code)} chars)")
        
        self.completed_tasks += 1
        
        return Implementation(
            perspective=self.perspective,
            file_name=file_name,
            code=code,
            quality_score=quality_score,
            reasoning=reasoning,
            strengths=strengths,
            weaknesses=weaknesses
        )
    
    def _generate_perspective_code(
        self, 
        file_name: str, 
        requirements: str, 
        characteristics: Dict
    ) -> str:
        """관점별 코드 생성 (시뮬레이션)"""
        
        # 실제로는 LLM API 호출
        template_parts = []
        
        # 파일 타입에 따른 기본 구조
        if "model" in file_name.lower():
            template_parts.append("class UserModel:")
        elif "service" in file_name.lower():
            template_parts.append("class AuthService:")
        elif "controller" in file_name.lower():
            template_parts.append("class ApiController:")
        else:
            template_parts.append("class Component:")
        
        # 관점별 특성 반영
        for keyword in characteristics["keywords"][:2]:
            template_parts.append(f"    # {keyword.title()} implementation")
            template_parts.append(f"    def {keyword}_method(self): pass")
        
        # 관점별 패턴 반영
        for pattern in characteristics["patterns"][:1]:
            template_parts.append(f"    # {pattern}")
            
        code = "\n".join(template_parts)
        
        # 관점별 코드 길이 조정
        perspective_multipliers = {
            Perspective.PERFORMANCE: 1.2,  # 최적화 코드로 더 길어짐
            Perspective.MAINTAINABILITY: 1.5,  # 문서화로 더 길어짐
            Perspective.SIMPLICITY: 0.8,  # 단순화로 더 짧아짐
            Perspective.SECURITY: 1.3   # 검증 로직으로 더 길어짐
        }
        
        multiplier = perspective_multipliers.get(self.perspective, 1.0)
        code = code * int(multiplier)
        
        return code
    
    def _calculate_quality_score(self, code: str, characteristics: Dict) -> float:
        """관점별 품질 점수 계산"""
        
        base_score = random.uniform(7.0, 9.5)
        
        # 관점별 가중치 적용
        perspective_bonuses = {
            Perspective.PERFORMANCE: random.uniform(0.2, 0.8),
            Perspective.MAINTAINABILITY: random.uniform(0.1, 0.6), 
            Perspective.SIMPLICITY: random.uniform(0.3, 0.7),
            Perspective.SECURITY: random.uniform(0.2, 0.9)
        }
        
        bonus = perspective_bonuses.get(self.perspective, 0.0)
        final_score = min(10.0, base_score + bonus)
        
        return final_score
    
    def _analyze_implementation(self, code: str, characteristics: Dict) -> tuple:
        """구현 분석: 강점과 약점"""
        
        perspective_analysis = {
            Perspective.PERFORMANCE: {
                "strengths": ["Optimized algorithms", "Efficient memory usage", "Fast execution"],
                "weaknesses": ["Complex to understand", "Hard to modify", "May sacrifice readability"]
            },
            Perspective.MAINTAINABILITY: {
                "strengths": ["Clean structure", "Well documented", "Easy to test", "Follows standards"],
                "weaknesses": ["May be verbose", "Could be slower", "More complex setup"]
            },
            Perspective.SIMPLICITY: {
                "strengths": ["Easy to understand", "Minimal dependencies", "Quick to implement"],
                "weaknesses": ["May lack advanced features", "Not optimized", "Limited flexibility"]
            },
            Perspective.SECURITY: {
                "strengths": ["Secure coding practices", "Input validation", "Error handling"],
                "weaknesses": ["May be slower", "More complex", "Additional dependencies"]
            }
        }
        
        analysis = perspective_analysis.get(self.perspective, {"strengths": [], "weaknesses": []})
        return analysis["strengths"], analysis["weaknesses"]
    
    def _generate_reasoning(self, file_name: str, characteristics: Dict) -> str:
        """추론 과정 설명"""
        
        focus = characteristics["focus"]
        keywords = ", ".join(characteristics["keywords"][:3])
        
        return f"""
{self.perspective.value.title()} 관점으로 {file_name} 구현:

핵심 초점: {focus}
적용 키워드: {keywords}
설계 철학: {characteristics['patterns'][0] if characteristics['patterns'] else 'Standard approach'}

이 관점에서는 {focus}을/를 최우선으로 고려하여 구현했습니다.
"""


class SynthesizerAgent:
    """여러 구현을 합성하는 Agent"""
    
    def __init__(self):
        self.synthesis_count = 0
    
    async def synthesize_implementations(
        self, 
        implementations: List[Implementation]
    ) -> SynthesizedResult:
        """여러 구현을 분석하여 최적 결과 합성"""
        
        if not implementations:
            raise ValueError("No implementations to synthesize")
        
        file_name = implementations[0].file_name
        print(f"  [Synthesizer] 🔬 Analyzing {len(implementations)} implementations of {file_name}")
        
        # 합성 시간 (구현 수에 비례)
        synthesis_time = 0.5 + (len(implementations) * 0.2)
        await asyncio.sleep(synthesis_time)
        
        # 각 구현 분석
        analysis = await self._analyze_implementations(implementations)
        
        # 최적 코드 합성
        final_code = await self._create_synthesized_code(implementations, analysis)
        
        # 품질 점수 계산 (최고 구현보다 향상)
        best_score = max([impl.quality_score for impl in implementations])
        synthesis_bonus = random.uniform(0.2, 0.8)
        final_score = min(10.0, best_score + synthesis_bonus)
        
        improvement = final_score - best_score
        
        # 합성 추론
        reasoning = self._generate_synthesis_reasoning(implementations, analysis, improvement)
        
        print(f"  [Synthesizer] ✨ Synthesized {file_name} "
              f"(Q:{final_score:.1f}, +{improvement:.1f} improvement)")
        
        self.synthesis_count += 1
        
        return SynthesizedResult(
            file_name=file_name,
            final_code=final_code,
            quality_score=final_score,
            source_perspectives=[impl.perspective for impl in implementations],
            synthesis_reasoning=reasoning,
            improvement_over_best=improvement
        )
    
    async def _analyze_implementations(self, implementations: List[Implementation]) -> Dict:
        """구현들 분석"""
        
        analysis = {
            "best_practices": [],
            "common_patterns": [],
            "unique_approaches": [],
            "quality_rankings": []
        }
        
        # 품질 순으로 정렬
        sorted_impls = sorted(implementations, key=lambda x: x.quality_score, reverse=True)
        
        for impl in sorted_impls:
            analysis["quality_rankings"].append({
                "perspective": impl.perspective.value,
                "score": impl.quality_score,
                "strengths": impl.strengths[:2],  # 상위 2개만
                "key_weakness": impl.weaknesses[0] if impl.weaknesses else "None"
            })
        
        return analysis
    
    async def _create_synthesized_code(
        self, 
        implementations: List[Implementation], 
        analysis: Dict
    ) -> str:
        """최적 코드 합성"""
        
        # 실제로는 복잡한 LLM 기반 합성 로직
        # 여기서는 시뮬레이션
        
        # 가장 좋은 구현을 베이스로
        best_impl = max(implementations, key=lambda x: x.quality_score)
        base_code = best_impl.code
        
        # 다른 구현들의 좋은 부분을 통합
        enhanced_parts = []
        for impl in implementations:
            if impl != best_impl and impl.quality_score > 8.0:
                enhanced_parts.append(f"    # From {impl.perspective.value}: {impl.strengths[0] if impl.strengths else 'Enhancement'}")
        
        synthesized_code = base_code + "\n" + "\n".join(enhanced_parts)
        synthesized_code += "\n\n    # Synthesized: Combined best practices from all perspectives"
        
        return synthesized_code
    
    def _generate_synthesis_reasoning(
        self, 
        implementations: List[Implementation], 
        analysis: Dict, 
        improvement: float
    ) -> str:
        """합성 추론 과정"""
        
        perspectives = [impl.perspective.value for impl in implementations]
        best_score = max([impl.quality_score for impl in implementations])
        
        return f"""
Synthesis Analysis:

Input Perspectives: {', '.join(perspectives)}
Quality Scores: {[f'{impl.quality_score:.1f}' for impl in implementations]}

Best Individual Score: {best_score:.1f}
Synthesized Score: {best_score + improvement:.1f}
Improvement: +{improvement:.1f}

Synthesis Strategy:
1. Used {max(implementations, key=lambda x: x.quality_score).perspective.value} as base (highest quality)
2. Integrated strengths from other perspectives
3. Addressed common weaknesses
4. Applied cross-perspective optimization

The synthesized implementation combines the best aspects of each perspective
while mitigating individual weaknesses through cross-perspective integration.
"""


class MixtureOfAgentsOrchestrator:
    """MoA 패턴 Orchestrator"""
    
    def __init__(self, perspectives: Optional[List[Perspective]] = None):
        if perspectives is None:
            perspectives = [Perspective.PERFORMANCE, Perspective.MAINTAINABILITY, Perspective.SIMPLICITY]
        
        self.perspective_agents = [PerspectiveAgent(p) for p in perspectives]
        self.synthesizer = SynthesizerAgent()
        self.total_files_processed = 0
    
    async def process_files_moa(
        self, 
        file_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """MoA 패턴으로 파일들 처리"""
        
        print(f"\n🎭 [MoA] Processing {len(file_tasks)} files with {len(self.perspective_agents)} perspectives")
        start_time = time.time()
        
        # Layer 1: 모든 파일에 대해 모든 관점으로 병렬 생성
        layer1_tasks = []
        
        for file_task in file_tasks:
            for agent in self.perspective_agents:
                task = agent.generate_implementation(
                    file_name=file_task["name"],
                    requirements=file_task.get("requirements", ""),
                    complexity=file_task.get("complexity", "medium")
                )
                layer1_tasks.append(task)
        
        print(f"  [Layer 1] Generating {len(layer1_tasks)} implementations...")
        layer1_results = await asyncio.gather(*layer1_tasks, return_exceptions=True)
        
        # 결과를 파일별로 그룹화
        implementations_by_file = self._group_implementations_by_file(layer1_results, file_tasks)
        
        # Layer 2: 파일별로 합성
        print(f"  [Layer 2] Synthesizing {len(implementations_by_file)} files...")
        
        synthesis_tasks = [
            self.synthesizer.synthesize_implementations(implementations)
            for implementations in implementations_by_file.values()
        ]
        
        synthesis_results = await asyncio.gather(*synthesis_tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # 결과 분석
        successful_synthesis = [r for r in synthesis_results if isinstance(r, SynthesizedResult)]
        failed_synthesis = [r for r in synthesis_results if isinstance(r, Exception)]
        
        avg_quality = sum([r.quality_score for r in successful_synthesis]) / max(1, len(successful_synthesis))
        avg_improvement = sum([r.improvement_over_best for r in successful_synthesis]) / max(1, len(successful_synthesis))
        
        # 상세 리포트
        print(f"\n📊 [MoA] Execution Summary:")
        print(f"    Total time: {total_time:.2f}s")
        print(f"    Layer 1 (Generation): {len(layer1_tasks)} implementations")
        print(f"    Layer 2 (Synthesis): {len(successful_synthesis)} successful")
        print(f"    Average quality: {avg_quality:.1f}/10")
        print(f"    Average improvement: +{avg_improvement:.1f}")
        
        # 관점별 성능
        print(f"\n🎯 Perspective Performance:")
        for agent in self.perspective_agents:
            print(f"    {agent.perspective.value.title()}: {agent.completed_tasks} implementations")
        
        self.total_files_processed += len(successful_synthesis)
        
        return {
            "total_time": total_time,
            "files_processed": len(successful_synthesis),
            "failed_files": len(failed_synthesis),
            "avg_quality": avg_quality,
            "avg_improvement": avg_improvement,
            "layer1_implementations": len([r for r in layer1_results if not isinstance(r, Exception)]),
            "synthesized_results": successful_synthesis
        }
    
    def _group_implementations_by_file(
        self, 
        layer1_results: List, 
        file_tasks: List[Dict]
    ) -> Dict[str, List[Implementation]]:
        """구현 결과를 파일별로 그룹화"""
        
        implementations_by_file = {}
        successful_results = [r for r in layer1_results if isinstance(r, Implementation)]
        
        for file_task in file_tasks:
            file_name = file_task["name"]
            file_implementations = [
                impl for impl in successful_results 
                if impl.file_name == file_name
            ]
            if file_implementations:
                implementations_by_file[file_name] = file_implementations
        
        return implementations_by_file


# 사용 예제
async def main():
    """MoA 패턴 데모"""
    
    # 테스트용 파일 작업
    test_files = [
        {
            "name": "models/user.py", 
            "requirements": "User data model with validation",
            "complexity": "medium"
        },
        {
            "name": "services/auth.py",
            "requirements": "Authentication service with JWT",
            "complexity": "complex"
        },
        {
            "name": "controllers/api.py", 
            "requirements": "REST API controllers",
            "complexity": "complex"
        },
        {
            "name": "utils/helpers.py",
            "requirements": "Utility helper functions", 
            "complexity": "simple"
        },
        {
            "name": "handlers/event.py",
            "requirements": "Event handling system",
            "complexity": "medium"
        }
    ]
    
    print("=== Mixture of Agents Pattern Demo ===")
    
    # MoA Orchestrator 생성 (4가지 관점 사용)
    moa_orchestrator = MixtureOfAgentsOrchestrator([
        Perspective.PERFORMANCE,
        Perspective.MAINTAINABILITY, 
        Perspective.SIMPLICITY,
        Perspective.SECURITY
    ])
    
    # MoA 패턴으로 실행
    result = await moa_orchestrator.process_files_moa(test_files)
    
    # 성능 분석
    print(f"\n🎯 Performance Analysis:")
    estimated_single_perspective = len(test_files) * 1.5  # 단일 관점 예상 시간
    quality_improvement = result['avg_improvement']
    
    print(f"    Single perspective time estimate: {estimated_single_perspective:.1f}s")
    print(f"    MoA actual time: {result['total_time']:.1f}s")
    print(f"    Quality improvement: +{quality_improvement:.1f} points")
    print(f"    Files processed: {result['files_processed']}/{len(test_files)}")
    
    # 최고 품질 파일 출력
    if result['synthesized_results']:
        best_result = max(result['synthesized_results'], key=lambda x: x.quality_score)
        print(f"\n🏆 Highest Quality Result:")
        print(f"    File: {best_result.file_name}")
        print(f"    Quality: {best_result.quality_score:.1f}/10")
        print(f"    Perspectives: {[p.value for p in best_result.source_perspectives]}")
        print(f"    Improvement: +{best_result.improvement_over_best:.1f}")


if __name__ == "__main__":
    asyncio.run(main())