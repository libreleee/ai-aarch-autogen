"""
Worker Agent 패턴 예제

AutoGen의 Worker Agent 패턴을 구현한 예제입니다.
각 Worker가 독립적으로 작업을 수행하고, Orchestrator가 작업을 분배하고 결과를 집계합니다.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import random


@dataclass
class WorkerTask:
    """Worker에게 할당되는 작업"""
    task_id: str
    file_name: str
    description: str
    complexity: str
    priority: int = 1


@dataclass
class WorkerResult:
    """Worker의 작업 결과"""
    worker_id: int
    task_id: str
    file_name: str
    status: str  # 'success', 'failed'
    processing_time: float
    lines_generated: int
    quality_score: float
    error: Optional[str] = None


class WorkerAgent:
    """개별 Worker Agent"""
    
    def __init__(self, worker_id: int, specialization: str = "general"):
        self.worker_id = worker_id
        self.specialization = specialization
        self.tasks_completed = 0
        self.total_time = 0.0
        self.success_rate = 1.0
        
        # Worker별 특성화
        self.specializations = {
            "performance": {"speed_boost": 1.2, "quality_bonus": 0.1},
            "quality": {"speed_boost": 0.8, "quality_bonus": 0.3},
            "general": {"speed_boost": 1.0, "quality_bonus": 0.0}
        }
    
    async def execute_task(self, task: WorkerTask) -> WorkerResult:
        """작업 실행"""
        
        start_time = time.time()
        
        print(f"    [Worker-{self.worker_id}] 🔄 Starting {task.file_name}")
        
        try:
            # 특성화에 따른 처리 시간 조정
            spec_config = self.specializations.get(self.specialization, self.specializations["general"])
            
            base_time = self._get_base_processing_time(task.complexity)
            actual_time = base_time / spec_config["speed_boost"]
            
            # 작업 시뮬레이션
            await asyncio.sleep(actual_time)
            
            # 가끔 실패 시뮬레이션 (5% 확률)
            if random.random() < 0.05:
                raise Exception(f"Random failure in {task.file_name}")
            
            # 결과 생성
            processing_time = time.time() - start_time
            lines_generated = random.randint(50, 200)
            base_quality = random.uniform(7.0, 9.0)
            quality_score = min(10.0, base_quality + spec_config["quality_bonus"])
            
            # 통계 업데이트
            self.tasks_completed += 1
            self.total_time += processing_time
            
            print(f"    [Worker-{self.worker_id}] ✅ Completed {task.file_name} "
                  f"({processing_time:.1f}s, Q:{quality_score:.1f})")
            
            return WorkerResult(
                worker_id=self.worker_id,
                task_id=task.task_id,
                file_name=task.file_name,
                status="success",
                processing_time=processing_time,
                lines_generated=lines_generated,
                quality_score=quality_score
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            print(f"    [Worker-{self.worker_id}] ❌ Failed {task.file_name}: {error_msg}")
            
            return WorkerResult(
                worker_id=self.worker_id,
                task_id=task.task_id,
                file_name=task.file_name,
                status="failed",
                processing_time=processing_time,
                lines_generated=0,
                quality_score=0.0,
                error=error_msg
            )
    
    def _get_base_processing_time(self, complexity: str) -> float:
        """복잡도별 기본 처리 시간"""
        times = {
            "simple": 0.5,
            "medium": 1.0, 
            "complex": 2.0,
            "critical": 3.0
        }
        return times.get(complexity, 1.0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Worker 통계"""
        return {
            "worker_id": self.worker_id,
            "specialization": self.specialization,
            "tasks_completed": self.tasks_completed,
            "total_time": self.total_time,
            "avg_time_per_task": self.total_time / max(1, self.tasks_completed),
            "estimated_success_rate": self.success_rate
        }


class WorkerOrchestrator:
    """Worker들을 관리하는 Orchestrator"""
    
    def __init__(self, num_workers: int = 3):
        self.workers = self._create_workers(num_workers)
        self.task_queue = asyncio.Queue()
        self.results = []
    
    def _create_workers(self, num_workers: int) -> List[WorkerAgent]:
        """Worker 생성 (전문화별로)"""
        workers = []
        specializations = ["performance", "quality", "general"]
        
        for i in range(num_workers):
            spec = specializations[i % len(specializations)]
            worker = WorkerAgent(worker_id=i, specialization=spec)
            workers.append(worker)
        
        return workers
    
    async def process_tasks_parallel(self, tasks: List[WorkerTask]) -> Dict[str, Any]:
        """Worker Agent 패턴으로 작업 처리"""
        
        print(f"\n💼 [Orchestrator] Distributing {len(tasks)} tasks to {len(self.workers)} workers")
        start_time = time.time()
        
        # 작업 우선순위별 정렬
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        # 각 Worker에게 작업 분배
        worker_assignments = self._distribute_tasks(sorted_tasks)
        
        # 모든 Worker 동시 실행
        worker_coroutines = [
            self._run_worker_batch(worker, assigned_tasks)
            for worker, assigned_tasks in worker_assignments.items()
        ]
        
        batch_results = await asyncio.gather(*worker_coroutines, return_exceptions=True)
        
        # 결과 집계
        all_results = []
        for batch_result in batch_results:
            if isinstance(batch_result, list):
                all_results.extend(batch_result)
        
        total_time = time.time() - start_time
        
        # 통계 계산
        successful_results = [r for r in all_results if r.status == "success"]
        failed_results = [r for r in all_results if r.status == "failed"]
        
        avg_quality = sum([r.quality_score for r in successful_results]) / max(1, len(successful_results))
        total_lines = sum([r.lines_generated for r in successful_results])
        
        print(f"\n📊 [Orchestrator] Execution Summary:")
        print(f"    Total time: {total_time:.2f}s")
        print(f"    Successful: {len(successful_results)}/{len(tasks)}")
        print(f"    Average quality: {avg_quality:.1f}/10")
        print(f"    Total lines generated: {total_lines}")
        
        # Worker별 성능 리포트
        print(f"\n👥 Worker Performance:")
        for worker in self.workers:
            stats = worker.get_stats()
            print(f"    Worker-{stats['worker_id']} ({stats['specialization']}): "
                  f"{stats['tasks_completed']} tasks, "
                  f"{stats['avg_time_per_task']:.1f}s avg")
        
        return {
            "total_time": total_time,
            "successful": len(successful_results),
            "failed": len(failed_results), 
            "avg_quality": avg_quality,
            "total_lines": total_lines,
            "results": all_results,
            "worker_stats": [w.get_stats() for w in self.workers]
        }
    
    def _distribute_tasks(self, tasks: List[WorkerTask]) -> Dict[WorkerAgent, List[WorkerTask]]:
        """작업을 Worker들에게 분배"""
        
        assignments = {worker: [] for worker in self.workers}
        
        # Round-robin으로 분배 (우선순위 고려)
        for i, task in enumerate(tasks):
            worker = self.workers[i % len(self.workers)]
            assignments[worker].append(task)
        
        # 분배 결과 출력
        for worker, assigned_tasks in assignments.items():
            task_names = [t.file_name for t in assigned_tasks]
            print(f"    [Worker-{worker.worker_id}] Assigned {len(assigned_tasks)} tasks: {', '.join(task_names[:3])}")
            if len(task_names) > 3:
                print(f"        ... and {len(task_names) - 3} more")
        
        return assignments
    
    async def _run_worker_batch(self, worker: WorkerAgent, tasks: List[WorkerTask]) -> List[WorkerResult]:
        """단일 Worker의 작업 배치 실행"""
        
        results = []
        for task in tasks:
            result = await worker.execute_task(task)
            results.append(result)
        
        return results


# 사용 예제
async def main():
    """Worker Agent 패턴 데모"""
    
    # 테스트용 작업 목록
    test_tasks = [
        WorkerTask("task_1", "models/user.py", "User model", "simple", priority=1),
        WorkerTask("task_2", "services/auth.py", "Authentication service", "medium", priority=3),
        WorkerTask("task_3", "controllers/api.py", "API controllers", "complex", priority=2),
        WorkerTask("task_4", "utils/helpers.py", "Helper utilities", "simple", priority=1),
        WorkerTask("task_5", "handlers/event.py", "Event handlers", "medium", priority=2),
        WorkerTask("task_6", "managers/cache.py", "Cache manager", "complex", priority=4),
        WorkerTask("task_7", "validators/input.py", "Input validators", "simple", priority=1),
        WorkerTask("task_8", "middleware/auth.py", "Auth middleware", "medium", priority=3),
        WorkerTask("task_9", "processors/data.py", "Data processors", "complex", priority=4),
        WorkerTask("task_10", "connectors/db.py", "Database connectors", "critical", priority=5)
    ]
    
    # Orchestrator 생성 (3명의 Worker)
    orchestrator = WorkerOrchestrator(num_workers=3)
    
    print("=== Worker Agent Pattern Demo ===")
    
    # Worker Agent 패턴으로 실행
    result = await orchestrator.process_tasks_parallel(test_tasks)
    
    # 성능 분석
    print(f"\n🎯 Performance Analysis:")
    estimated_sequential_time = sum([2.0 for _ in test_tasks])  # 순차 처리 예상
    speedup = estimated_sequential_time / result['total_time']
    print(f"    Estimated sequential time: {estimated_sequential_time:.1f}s")
    print(f"    Actual parallel time: {result['total_time']:.1f}s") 
    print(f"    Speedup: {speedup:.1f}x")
    print(f"    Success rate: {result['successful']}/{len(test_tasks)} ({result['successful']/len(test_tasks)*100:.1f}%)")


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    asyncio.run(main())