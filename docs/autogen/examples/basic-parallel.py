"""
기본 병렬 처리 예제

현재 actor_critic.py에서 사용중인 기본 병렬 처리 방식의 예제입니다.
asyncio.gather()를 사용한 단순하고 효과적인 병렬 처리를 보여줍니다.
"""

import asyncio
import time
from typing import List, Dict, Any
from pathlib import Path


class BasicParallelProcessor:
    """기본 병렬 처리 클래스"""
    
    def __init__(self, project_path: Path, requirements: str):
        self.project_path = project_path
        self.requirements = requirements
    
    async def process_files_parallel(self, file_list: List[Dict]) -> Dict[str, Any]:
        """파일들을 병렬로 처리하는 기본 방식"""
        
        print(f"\n🔄 Processing {len(file_list)} files in parallel...")
        start_time = time.time()
        
        # 각 파일에 대한 작업을 비동기 태스크로 생성
        tasks = [
            self._process_single_file(file_info) 
            for file_info in file_list
        ]
        
        # 모든 태스크를 동시에 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        # 결과 분석
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]
        
        print(f"✅ Completed in {elapsed:.2f}s")
        print(f"   Success: {len(successful)}, Failed: {len(failed)}")
        
        return {
            "total_time": elapsed,
            "successful": len(successful),
            "failed": len(failed),
            "results": successful
        }
    
    async def _process_single_file(self, file_info: Dict) -> Dict[str, Any]:
        """단일 파일 처리 (시뮬레이션)"""
        
        file_name = file_info.get('name', 'unknown.py')
        complexity = file_info.get('complexity', 'medium')
        
        # 복잡도에 따른 처리 시간 시뮬레이션
        processing_times = {
            'simple': 0.5,
            'medium': 1.0,
            'complex': 2.0
        }
        
        processing_time = processing_times.get(complexity, 1.0)
        
        print(f"  🔨 Processing {file_name} ({complexity})...")
        
        # 실제 작업 시뮬레이션 (비동기 대기)
        await asyncio.sleep(processing_time)
        
        # 가끔 실패 시뮬레이션 (10% 확률)
        import random
        if random.random() < 0.1:
            raise Exception(f"Processing failed for {file_name}")
        
        # 성공적인 결과 반환
        return {
            "file_name": file_name,
            "complexity": complexity,
            "processing_time": processing_time,
            "lines_generated": random.randint(50, 200),
            "status": "success"
        }


# 사용 예제
async def main():
    """기본 병렬 처리 데모"""
    
    # 테스트용 파일 목록
    test_files = [
        {"name": "models/user.py", "complexity": "simple"},
        {"name": "services/auth.py", "complexity": "medium"},
        {"name": "controllers/api.py", "complexity": "complex"},
        {"name": "utils/helpers.py", "complexity": "simple"},
        {"name": "handlers/event.py", "complexity": "medium"},
        {"name": "managers/cache.py", "complexity": "complex"},
        {"name": "validators/input.py", "complexity": "simple"},
        {"name": "middleware/auth.py", "complexity": "medium"}
    ]
    
    processor = BasicParallelProcessor(
        project_path=Path("./test_project"),
        requirements="Sample project requirements"
    )
    
    # 기본 병렬 처리 실행
    result = await processor.process_files_parallel(test_files)
    
    print(f"\n📊 Final Results:")
    print(f"   Total files: {len(test_files)}")
    print(f"   Processing time: {result['total_time']:.2f}s")
    print(f"   Success rate: {result['successful']}/{len(test_files)}")
    
    # 순차 처리와 비교
    print(f"\n⚡ Performance comparison:")
    sequential_time = sum([1.0 for _ in test_files])  # 순차 처리 예상 시간
    speedup = sequential_time / result['total_time']
    print(f"   Sequential time estimate: {sequential_time:.2f}s")
    print(f"   Parallel speedup: {speedup:.1f}x")


if __name__ == "__main__":
    asyncio.run(main())