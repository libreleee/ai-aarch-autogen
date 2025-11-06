"""
Actor-Critic 팀 강화 예제

현재 actor_critic.py에 AutoGen 패턴들을 적용한 통합 예제입니다.
Worker Agent 패턴과 선택적 MoA 패턴을 결합하여 실무에 바로 적용할 수 있습니다.
"""

import asyncio
import time
import json
import random
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import logging


class QualityLevel(Enum):
    """품질 레벨"""
    BASIC = "basic"
    ENHANCED = "enhanced"
    PREMIUM = "premium"


class FileType(Enum):
    """파일 유형"""
    CRITICAL = "critical"    # 핵심 비즈니스 로직
    IMPORTANT = "important"  # 중요한 기능
    STANDARD = "standard"    # 일반적인 파일
    UTILITY = "utility"      # 유틸리티 함수


@dataclass
class FileTask:
    """파일 작업 정의"""
    name: str
    description: str
    complexity: str = "medium"
    file_type: FileType = FileType.STANDARD
    priority: int = 1
    quality_target: QualityLevel = QualityLevel.BASIC


@dataclass
class GenerationResult:
    """생성 결과"""
    file_name: str
    content: str
    quality_score: float
    generation_method: str  # 'worker', 'moa', 'enhanced'
    processing_time: float
    lines_of_code: int
    success: bool = True
    error: Optional[str] = None


class EnhancedWorkerAgent:
    """강화된 Worker Agent (AutoGen 패턴 적용)"""
    
    def __init__(self, worker_id: int, specialization: str = "general"):
        self.worker_id = worker_id
        self.specialization = specialization
        self.tasks_completed = 0
        self.total_processing_time = 0.0
        
        # 전문화별 특성
        self.specializations = {
            "performance": {
                "speed_multiplier": 1.2,
                "quality_bonus": 0.1,
                "focus": "성능 최적화"
            },
            "maintainability": {
                "speed_multiplier": 0.9,
                "quality_bonus": 0.3,
                "focus": "유지보수성"
            },
            "security": {
                "speed_multiplier": 0.8,
                "quality_bonus": 0.2,
                "focus": "보안성"
            },
            "general": {
                "speed_multiplier": 1.0,
                "quality_bonus": 0.0,
                "focus": "일반적 구현"
            }
        }
    
    async def generate_file(
        self, 
        task: FileTask, 
        context: Dict[str, Any]
    ) -> GenerationResult:
        """파일 생성 (Worker Agent 방식)"""
        
        start_time = time.time()
        
        try:
            print(f"    [Worker-{self.worker_id}] 🔨 Generating {task.name} ({self.specialization})")
            
            # 전문화에 따른 처리 시간 조정
            spec_config = self.specializations[self.specialization]
            base_time = self._get_processing_time(task.complexity)
            actual_time = base_time / spec_config["speed_multiplier"]
            
            # 작업 시뮬레이션
            await asyncio.sleep(actual_time)
            
            # 코드 생성
            content = await self._generate_content(task, context, spec_config)
            
            # 품질 점수 계산
            base_quality = random.uniform(7.0, 9.0)
            quality_score = min(10.0, base_quality + spec_config["quality_bonus"])
            
            processing_time = time.time() - start_time
            lines_of_code = len(content.split('\n'))
            
            # 통계 업데이트
            self.tasks_completed += 1
            self.total_processing_time += processing_time
            
            print(f"    [Worker-{self.worker_id}] ✅ Completed {task.name} "
                  f"({processing_time:.1f}s, Q:{quality_score:.1f}, {lines_of_code} lines)")
            
            return GenerationResult(
                file_name=task.name,
                content=content,
                quality_score=quality_score,
                generation_method="worker",
                processing_time=processing_time,
                lines_of_code=lines_of_code,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            print(f"    [Worker-{self.worker_id}] ❌ Failed {task.name}: {error_msg}")
            
            return GenerationResult(
                file_name=task.name,
                content="",
                quality_score=0.0,
                generation_method="worker",
                processing_time=processing_time,
                lines_of_code=0,
                success=False,
                error=error_msg
            )
    
    def _get_processing_time(self, complexity: str) -> float:
        """복잡도별 기본 처리 시간"""
        times = {
            "simple": 0.8,
            "medium": 1.5,
            "complex": 2.5,
            "critical": 3.5
        }
        return times.get(complexity, 1.5)
    
    async def _generate_content(
        self, 
        task: FileTask, 
        context: Dict[str, Any], 
        spec_config: Dict
    ) -> str:
        """컨텐츠 생성 (시뮬레이션)"""
        
        # 실제로는 LLM API 호출
        focus = spec_config["focus"]
        
        template = f'''"""
{task.description}

Generated by Worker-{self.worker_id} ({self.specialization})
Focus: {focus}
Quality Target: {task.quality_target.value}
"""

class {self._extract_class_name(task.name)}:
    """
    {task.description}
    
    Specialized for: {focus}
    Complexity: {task.complexity}
    """
    
    def __init__(self):
        # {focus} 초점의 초기화
        self.initialized = True
    
    def main_method(self):
        """핵심 기능 구현"""
        # {focus}를 고려한 구현
        pass
    
    def helper_method(self):
        """보조 기능"""
        # 전문화된 보조 로직
        pass
'''
        
        # 복잡도에 따른 추가 내용
        if task.complexity in ["complex", "critical"]:
            template += f'''
    
    def advanced_feature(self):
        """고급 기능 ({focus})"""
        # {focus} 최적화된 고급 로직
        pass
        
    def error_handling(self):
        """에러 처리"""
        # 안전한 에러 처리
        pass
'''
        
        return template
    
    def _extract_class_name(self, file_name: str) -> str:
        """파일명에서 클래스명 추출"""
        name = Path(file_name).stem
        return ''.join(word.capitalize() for word in name.split('_'))
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Worker 성능 통계"""
        avg_time = self.total_processing_time / max(1, self.tasks_completed)
        
        return {
            "worker_id": self.worker_id,
            "specialization": self.specialization,
            "tasks_completed": self.tasks_completed,
            "total_time": self.total_processing_time,
            "average_time": avg_time,
            "efficiency": min(2.0, 2.0 / avg_time) if avg_time > 0 else 0
        }


class SelectiveMoAProcessor:
    """선택적 MoA 처리기 (핵심 파일용)"""
    
    def __init__(self):
        self.processed_files = 0
        
        # MoA용 전문 관점들
        self.perspectives = [
            {"name": "performance", "focus": "성능 최적화", "weight": 0.3},
            {"name": "maintainability", "focus": "유지보수성", "weight": 0.4},
            {"name": "security", "focus": "보안성", "weight": 0.3}
        ]
    
    async def generate_with_moa(
        self, 
        task: FileTask, 
        context: Dict[str, Any]
    ) -> GenerationResult:
        """MoA 패턴으로 고품질 생성"""
        
        print(f"  [MoA] 🎭 High-quality generation for {task.name}")
        start_time = time.time()
        
        try:
            # Layer 1: 다중 관점 생성
            perspective_results = await self._generate_multiple_perspectives(task, context)
            
            # Layer 2: 최적 합성
            synthesized_content = await self._synthesize_best_implementation(
                task, perspective_results
            )
            
            # 품질 점수 (MoA는 더 높은 품질)
            base_quality = random.uniform(8.5, 9.8)
            quality_score = min(10.0, base_quality + 0.2)  # MoA 보너스
            
            processing_time = time.time() - start_time
            lines_of_code = len(synthesized_content.split('\n'))
            
            print(f"  [MoA] ✨ Synthesized {task.name} "
                  f"({processing_time:.1f}s, Q:{quality_score:.1f}, {lines_of_code} lines)")
            
            self.processed_files += 1
            
            return GenerationResult(
                file_name=task.name,
                content=synthesized_content,
                quality_score=quality_score,
                generation_method="moa",
                processing_time=processing_time,
                lines_of_code=lines_of_code,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            print(f"  [MoA] ❌ Failed {task.name}: {error_msg}")
            
            return GenerationResult(
                file_name=task.name,
                content="",
                quality_score=0.0,
                generation_method="moa",
                processing_time=processing_time,
                lines_of_code=0,
                success=False,
                error=error_msg
            )
    
    async def _generate_multiple_perspectives(
        self, 
        task: FileTask, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """다중 관점으로 생성"""
        
        # 각 관점별로 생성 (병렬)
        perspective_tasks = [
            self._generate_perspective_implementation(task, context, perspective)
            for perspective in self.perspectives
        ]
        
        results = await asyncio.gather(*perspective_tasks)
        return results
    
    async def _generate_perspective_implementation(
        self, 
        task: FileTask, 
        context: Dict[str, Any], 
        perspective: Dict[str, Any]
    ) -> Dict[str, Any]:
        """특정 관점으로 구현 생성"""
        
        # 관점별 처리 시간
        await asyncio.sleep(0.8 + random.uniform(0.2, 0.5))
        
        focus = perspective["focus"]
        perspective_name = perspective["name"]
        
        # 관점별 템플릿
        content = f'''"""
{task.description}

Perspective: {focus}
Approach: {perspective_name.title()}-focused implementation
"""

class {self._extract_class_name(task.name)}:
    """
    {task.description}
    
    Implementation Focus: {focus}
    """
    
    def __init__(self):
        # {focus} 중심 설계
        self.{perspective_name}_optimized = True
    
    def core_functionality(self):
        """핵심 기능 - {focus} 최적화"""
        # {focus}를 위한 특별한 구현
        pass
    
    def {perspective_name}_specific_method(self):
        """{focus} 전용 메서드"""
        # {perspective_name} 관점의 특화된 로직
        pass
'''
        
        return {
            "perspective": perspective_name,
            "focus": focus,
            "content": content,
            "quality_estimate": random.uniform(8.0, 9.5),
            "strengths": [f"Excellent {focus}", f"Optimized for {perspective_name}"],
            "areas_for_improvement": ["Could be more balanced", "May need other perspectives"]
        }
    
    async def _synthesize_best_implementation(
        self, 
        task: FileTask, 
        perspective_results: List[Dict[str, Any]]
    ) -> str:
        """최적 구현 합성"""
        
        # 합성 시간
        await asyncio.sleep(0.5)
        
        # 가장 좋은 관점을 베이스로
        best_perspective = max(perspective_results, key=lambda x: x["quality_estimate"])
        
        synthesized = f'''"""
{task.description}

SYNTHESIZED IMPLEMENTATION
Combining best practices from: {', '.join([r["perspective"] for r in perspective_results])}

Base approach: {best_perspective["focus"]}
Enhanced with insights from all perspectives
"""

class {self._extract_class_name(task.name)}:
    """
    {task.description}
    
    High-quality implementation synthesized from multiple expert perspectives:
    - {perspective_results[0]["focus"]}
    - {perspective_results[1]["focus"]} 
    - {perspective_results[2]["focus"]}
    """
    
    def __init__(self):
        """통합된 초기화 로직"""
        # 모든 관점을 고려한 최적 설계
        self.performance_optimized = True
        self.maintainable_structure = True
        self.security_compliant = True
    
    def core_functionality(self):
        """핵심 기능 - 다관점 최적화"""
        # 성능, 유지보수성, 보안성을 모두 고려한 구현
        pass
    
    def performance_critical_method(self):
        """성능 중요 메서드"""
        # 성능 최적화된 로직
        pass
    
    def maintainable_helper(self):
        """유지보수 친화적 헬퍼"""
        # 깨끗하고 이해하기 쉬운 로직
        pass
    
    def secure_operation(self):
        """보안 처리"""
        # 안전하고 검증된 로직
        pass
    
    def integrated_workflow(self):
        """통합 워크플로우"""
        # 모든 관점의 장점을 결합한 완전한 구현
        try:
            self.performance_critical_method()
            self.maintainable_helper() 
            self.secure_operation()
        except Exception as e:
            # 모든 관점을 고려한 에러 처리
            logging.error(f"Integrated workflow error: {{e}}")
            raise
'''
        
        return synthesized
    
    def _extract_class_name(self, file_name: str) -> str:
        """파일명에서 클래스명 추출"""
        name = Path(file_name).stem
        return ''.join(word.capitalize() for word in name.split('_'))


class EnhancedActorCriticTeam:
    """AutoGen 패턴이 적용된 강화된 Actor-Critic 팀"""
    
    def __init__(self, project_path: Path, requirements: str):
        self.project_path = project_path
        self.requirements = requirements
        
        # Worker Agent 풀
        self.workers = [
            EnhancedWorkerAgent(0, "performance"),
            EnhancedWorkerAgent(1, "maintainability"),
            EnhancedWorkerAgent(2, "security"),
            EnhancedWorkerAgent(3, "general")
        ]
        
        # MoA 프로세서 (고품질 파일용)
        self.moa_processor = SelectiveMoAProcessor()
        
        # 통계
        self.total_files_processed = 0
        self.execution_stats = {
            "worker_processed": 0,
            "moa_processed": 0,
            "total_time": 0.0,
            "average_quality": 0.0
        }
    
    async def implementation_phase_enhanced(
        self, 
        file_tasks: List[FileTask]
    ) -> Dict[str, Any]:
        """강화된 구현 단계 (Worker + 선택적 MoA)"""
        
        print(f"\n🚀 [Enhanced Implementation] Processing {len(file_tasks)} files")
        print("-" * 80)
        
        start_time = time.time()
        
        # 파일을 중요도별로 분류
        critical_files, standard_files = self._categorize_files(file_tasks)
        
        print(f"  📊 File categorization:")
        print(f"    Critical files (MoA): {len(critical_files)}")
        print(f"    Standard files (Workers): {len(standard_files)}")
        
        # 병렬 처리: 중요 파일은 MoA, 일반 파일은 Worker
        critical_task = self._process_critical_files_moa(critical_files)
        standard_task = self._process_standard_files_workers(standard_files)
        
        critical_results, standard_results = await asyncio.gather(
            critical_task, 
            standard_task,
            return_exceptions=True
        )
        
        # 결과 통합
        all_results = []
        if isinstance(critical_results, list):
            all_results.extend(critical_results)
        if isinstance(standard_results, list):
            all_results.extend(standard_results)
        
        total_time = time.time() - start_time
        
        # 통계 계산
        successful_results = [r for r in all_results if r.success]
        failed_results = [r for r in all_results if not r.success]
        
        avg_quality = sum([r.quality_score for r in successful_results]) / max(1, len(successful_results))
        total_lines = sum([r.lines_of_code for r in successful_results])
        
        # 방법별 통계
        worker_results = [r for r in successful_results if r.generation_method == "worker"]
        moa_results = [r for r in successful_results if r.generation_method == "moa"]
        
        # 최종 보고서
        print(f"\n📈 [Enhanced Implementation] Final Report:")
        print(f"    Total time: {total_time:.2f}s")
        print(f"    Success rate: {len(successful_results)}/{len(file_tasks)} ({len(successful_results)/len(file_tasks)*100:.1f}%)")
        print(f"    Average quality: {avg_quality:.1f}/10")
        print(f"    Total lines generated: {total_lines:,}")
        print(f"")
        print(f"    Method breakdown:")
        print(f"      Worker Agent: {len(worker_results)} files, avg quality {sum([r.quality_score for r in worker_results])/max(1,len(worker_results)):.1f}")
        print(f"      MoA Pattern: {len(moa_results)} files, avg quality {sum([r.quality_score for r in moa_results])/max(1,len(moa_results)):.1f}")
        
        # Worker 성능 리포트
        print(f"\n👥 Worker Performance:")
        for worker in self.workers:
            stats = worker.get_performance_stats()
            print(f"    Worker-{stats['worker_id']} ({stats['specialization']}): "
                  f"{stats['tasks_completed']} tasks, "
                  f"{stats['average_time']:.1f}s avg, "
                  f"efficiency {stats['efficiency']:.1f}")
        
        # 통계 업데이트
        self.execution_stats.update({
            "worker_processed": len(worker_results),
            "moa_processed": len(moa_results),
            "total_time": total_time,
            "average_quality": avg_quality
        })
        
        return {
            "success": len(failed_results) == 0,
            "total_files": len(file_tasks),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "total_time": total_time,
            "average_quality": avg_quality,
            "total_lines": total_lines,
            "method_breakdown": {
                "worker_agent": len(worker_results),
                "moa_pattern": len(moa_results)
            },
            "results": successful_results,
            "worker_stats": [w.get_performance_stats() for w in self.workers]
        }
    
    def _categorize_files(self, file_tasks: List[FileTask]) -> tuple:
        """파일을 중요도별로 분류"""
        
        critical_files = []
        standard_files = []
        
        for task in file_tasks:
            # 중요한 파일 패턴들
            if (task.file_type in [FileType.CRITICAL] or
                task.quality_target in [QualityLevel.PREMIUM] or
                task.complexity in ["complex", "critical"] or
                any(keyword in task.name.lower() for keyword in ["service", "controller", "manager", "handler", "core"])):
                critical_files.append(task)
            else:
                standard_files.append(task)
        
        return critical_files, standard_files
    
    async def _process_critical_files_moa(self, critical_files: List[FileTask]) -> List[GenerationResult]:
        """중요 파일들을 MoA 패턴으로 처리"""
        
        if not critical_files:
            return []
        
        print(f"  🎭 [MoA] Processing {len(critical_files)} critical files...")
        
        moa_tasks = [
            self.moa_processor.generate_with_moa(task, {"requirements": self.requirements})
            for task in critical_files
        ]
        
        results = await asyncio.gather(*moa_tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, GenerationResult)]
    
    async def _process_standard_files_workers(self, standard_files: List[FileTask]) -> List[GenerationResult]:
        """일반 파일들을 Worker Agent로 처리"""
        
        if not standard_files:
            return []
        
        print(f"  👥 [Workers] Processing {len(standard_files)} standard files...")
        
        # 작업 분배
        worker_assignments = self._distribute_tasks_to_workers(standard_files)
        
        # Worker별 병렬 실행
        worker_tasks = [
            self._run_worker_batch(worker, assigned_tasks)
            for worker, assigned_tasks in worker_assignments.items()
        ]
        
        batch_results = await asyncio.gather(*worker_tasks, return_exceptions=True)
        
        # 결과 평탄화
        all_results = []
        for batch_result in batch_results:
            if isinstance(batch_result, list):
                all_results.extend(batch_result)
        
        return all_results
    
    def _distribute_tasks_to_workers(self, tasks: List[FileTask]) -> Dict[EnhancedWorkerAgent, List[FileTask]]:
        """작업을 Worker들에게 분배"""
        
        assignments = {worker: [] for worker in self.workers}
        
        # 우선순위별로 정렬 후 Round-robin 분배
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        for i, task in enumerate(sorted_tasks):
            worker = self.workers[i % len(self.workers)]
            assignments[worker].append(task)
        
        return assignments
    
    async def _run_worker_batch(
        self, 
        worker: EnhancedWorkerAgent, 
        tasks: List[FileTask]
    ) -> List[GenerationResult]:
        """단일 Worker의 작업 배치 실행"""
        
        results = []
        context = {"requirements": self.requirements, "project_path": str(self.project_path)}
        
        for task in tasks:
            result = await worker.generate_file(task, context)
            results.append(result)
        
        return results
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """종합 통계"""
        
        return {
            "execution_stats": self.execution_stats,
            "worker_stats": [w.get_performance_stats() for w in self.workers],
            "moa_files_processed": self.moa_processor.processed_files,
            "total_files_processed": self.total_files_processed
        }


# 사용 예제
async def main():
    """Enhanced Actor-Critic 데모"""
    
    # 테스트용 파일 작업들
    test_tasks = [
        # 중요한 파일들 (MoA 처리)
        FileTask("services/auth_service.py", "Authentication service", "complex", FileType.CRITICAL, 5, QualityLevel.PREMIUM),
        FileTask("controllers/user_controller.py", "User API controller", "complex", FileType.CRITICAL, 4, QualityLevel.ENHANCED),
        FileTask("managers/payment_manager.py", "Payment processing", "critical", FileType.CRITICAL, 5, QualityLevel.PREMIUM),
        
        # 일반 파일들 (Worker 처리)
        FileTask("models/user.py", "User data model", "medium", FileType.STANDARD, 2, QualityLevel.BASIC),
        FileTask("utils/helpers.py", "Helper utilities", "simple", FileType.UTILITY, 1, QualityLevel.BASIC),
        FileTask("validators/input.py", "Input validators", "simple", FileType.STANDARD, 1, QualityLevel.BASIC),
        FileTask("handlers/event.py", "Event handlers", "medium", FileType.IMPORTANT, 3, QualityLevel.ENHANCED),
        FileTask("middleware/cors.py", "CORS middleware", "simple", FileType.UTILITY, 1, QualityLevel.BASIC),
        FileTask("processors/data.py", "Data processors", "medium", FileType.STANDARD, 2, QualityLevel.BASIC),
        FileTask("connectors/database.py", "Database connections", "medium", FileType.IMPORTANT, 3, QualityLevel.ENHANCED)
    ]
    
    print("=== Enhanced Actor-Critic Team Demo ===")
    
    # Enhanced Actor-Critic 팀 생성
    team = EnhancedActorCriticTeam(
        project_path=Path("./enhanced_project"),
        requirements="Advanced web application with authentication, payments, and data processing"
    )
    
    # 강화된 구현 단계 실행
    result = await team.implementation_phase_enhanced(test_tasks)
    
    # 성능 비교
    print(f"\n⚡ Performance Comparison:")
    estimated_sequential = len(test_tasks) * 2.0  # 순차 처리 예상 시간
    actual_time = result['total_time']
    speedup = estimated_sequential / actual_time
    
    print(f"    Estimated sequential time: {estimated_sequential:.1f}s")
    print(f"    Enhanced parallel time: {actual_time:.1f}s")
    print(f"    Speedup: {speedup:.1f}x")
    print(f"    Quality improvement: {result['average_quality'] - 7.0:.1f} points (baseline 7.0)")
    
    # 방법별 효과성
    moa_count = result['method_breakdown']['moa_pattern']
    worker_count = result['method_breakdown']['worker_agent']
    
    print(f"\n📊 Method Effectiveness:")
    print(f"    High-quality MoA: {moa_count} files (critical components)")
    print(f"    Efficient Workers: {worker_count} files (standard components)")
    print(f"    Overall success rate: {result['successful']}/{result['total_files']} ({result['successful']/result['total_files']*100:.1f}%)")
    
    # 종합 통계
    comprehensive_stats = team.get_comprehensive_stats()
    print(f"\n🎯 Comprehensive Statistics:")
    print(json.dumps(comprehensive_stats, indent=2, default=str))


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())