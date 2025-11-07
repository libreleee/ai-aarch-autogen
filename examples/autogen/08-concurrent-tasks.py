"""
AutoGen - 병렬 에이전트 처리 예제 (2025년 11월 기준)

동시에 여러 에이전트가 독립적인 작업을 수행하는 패턴
- 작업 1: 수학 문제 풀기
- 작업 2: 화학 문제 풀기  
- 작업 3: 코드 분석

실행: python examples/autogen/08-concurrent-tasks.py
"""

import asyncio
import time
from datetime import datetime


# =====================================================
# 1️⃣ 에이전트 시뮬레이션 (실제는 OpenAI API 사용)
# =====================================================

class SimulatedAgent:
    """실제 API 호출 없이 에이전트 동작을 시뮬레이션"""
    
    def __init__(self, name: str, specialty: str, processing_time: float = 2.0):
        self.name = name
        self.specialty = specialty
        self.processing_time = processing_time
    
    async def run(self, task: str) -> dict:
        """
        에이전트 작업 실행 (비동기)
        
        Args:
            task: 수행할 작업 설명
            
        Returns:
            {
                "agent": 에이전트명,
                "task": 작업,
                "result": 결과,
                "processing_time": 처리시간,
                "timestamp": 완료 시간
            }
        """
        print(f"⏳ {self.name}: '{task}' 처리 시작... ({self.processing_time}초)")
        
        # 비동기 처리 (실제로는 API 호출)
        start_time = time.time()
        await asyncio.sleep(self.processing_time)
        elapsed = time.time() - start_time
        
        result = f"{self.specialty}에이전트가 처리 완료: {task}"
        
        print(f"✅ {self.name}: 완료 ({elapsed:.2f}초)")
        
        return {
            "agent": self.name,
            "task": task,
            "result": result,
            "processing_time": elapsed,
            "timestamp": datetime.now().isoformat()
        }


# =====================================================
# 2️⃣ 동시 처리 패턴
# =====================================================

async def example_1_simple_concurrent():
    """
    패턴 1: 단순 동시 실행
    - 여러 에이전트가 독립적 작업 수행
    - 모든 작업이 끝날 때까지 대기 (gather)
    """
    print("\n" + "="*60)
    print("패턴 1️⃣ : 단순 동시 실행 (asyncio.gather)")
    print("="*60)
    
    # 1. 에이전트 생성
    math_agent = SimulatedAgent("수학에이전트", "수학", processing_time=3.0)
    chem_agent = SimulatedAgent("화학에이전트", "화학", processing_time=2.5)
    code_agent = SimulatedAgent("코드에이전트", "코드분석", processing_time=2.0)
    
    # 2. 작업 정의
    tasks = [
        math_agent.run("적분 ∫x²dx 계산"),
        chem_agent.run("H₂O의 분자량 계산"),
        code_agent.run("Python 함수 최적화")
    ]
    
    # 3. 동시 실행 (전체 처리 시간: max(3.0, 2.5, 2.0) = 3.0초)
    start = time.time()
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    # 4. 결과 출력
    print("\n📊 결과:")
    for result in results:
        print(f"  - {result['agent']}: {result['result']}")
        print(f"    처리시간: {result['processing_time']:.2f}초")
    
    print(f"\n⏱️ 총 처리시간: {elapsed:.2f}초 (순차면 7.5초였을 것)")
    return results


async def example_2_fan_out():
    """
    패턴 2: Fan-Out (분산)
    - 하나의 작업을 여러 에이전트가 병렬로 처리
    - 예: 코드 리뷰를 여러 전문가가 동시에 검토
    """
    print("\n" + "="*60)
    print("패턴 2️⃣ : Fan-Out (분산 처리)")
    print("="*60)
    
    # 1. 여러 전문가 에이전트 생성
    reviewers = [
        SimulatedAgent("보안전문가", "보안검토", 2.0),
        SimulatedAgent("성능전문가", "성능검토", 1.5),
        SimulatedAgent("스타일전문가", "스타일검토", 1.0),
        SimulatedAgent("문서전문가", "문서검토", 1.2)
    ]
    
    # 2. 같은 코드를 모두가 검토
    code = """
    def process_data(data):
        result = []
        for i in range(len(data)):
            result.append(data[i] * 2)
        return result
    """
    
    # 3. 병렬 리뷰
    print(f"\n🔍 코드 리뷰 대상:\n{code}\n")
    
    start = time.time()
    tasks = [reviewer.run(f"다음 코드 리뷰:\n{code}") 
             for reviewer in reviewers]
    reviews = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    # 4. 모든 의견 수집
    print("\n📋 리뷰 의견:")
    for review in reviews:
        print(f"  - {review['agent']}: {review['result']}")
    
    print(f"\n⏱️ 병렬 리뷰 완료: {elapsed:.2f}초")


async def example_3_fan_in():
    """
    패턴 3: Fan-In (결과 통합)
    - 여러 에이전트의 결과를 한 곳에 모아 통합 처리
    """
    print("\n" + "="*60)
    print("패턴 3️⃣ : Fan-In (결과 통합)")
    print("="*60)
    
    # 1. 데이터 수집 에이전트들
    collectors = [
        SimulatedAgent("뉴스수집", "뉴스", 2.0),
        SimulatedAgent("SNS수집", "소셜미디어", 1.5),
        SimulatedAgent("학술논문수집", "학술", 2.5)
    ]
    
    # 2. 병렬 수집
    print("📰 데이터 수집 중...")
    start = time.time()
    tasks = [
        collector.run(f"AI 관련 {collector.specialty} 검색")
        for collector in collectors
    ]
    collected_data = await asyncio.gather(*tasks)
    collect_time = time.time() - start
    
    # 3. 결과 통합
    print("\n🔗 수집된 데이터 통합:")
    combined_data = {
        "sources": [],
        "total_items": len(collected_data),
        "processing_time": collect_time
    }
    
    for data in collected_data:
        combined_data["sources"].append({
            "source": data['agent'],
            "data": data['result']
        })
        print(f"  - {data['agent']}: {data['result']}")
    
    # 4. 통합 분석
    analyzer = SimulatedAgent("분석에이전트", "종합분석", 1.0)
    print("\n📊 통합 분석 중...")
    analysis = await analyzer.run(f"다음 데이터 종합분석: {combined_data}")
    
    print(f"\n📈 분석 결과: {analysis['result']}")
    print(f"⏱️ 전체 처리시간: {collect_time + analysis['processing_time']:.2f}초")


async def example_4_map_reduce():
    """
    패턴 4: Map-Reduce
    - Map: 데이터를 여러 에이전트가 병렬 처리
    - Reduce: 결과를 통합 계산
    """
    print("\n" + "="*60)
    print("패턴 4️⃣ : Map-Reduce (분산 처리 + 통합)")
    print("="*60)
    
    # 1. 처리할 데이터 (배치 분할)
    data_batches = [
        ["데이터1", "데이터2", "데이터3"],
        ["데이터4", "데이터5", "데이터6"],
        ["데이터7", "데이터8", "데이터9"]
    ]
    
    # 2. Map 단계: 여러 워커가 배치 처리
    workers = [
        SimulatedAgent(f"워커{i}", f"배치처리", 1.5)
        for i in range(3)
    ]
    
    print("🗺️ Map 단계: 병렬 처리")
    start = time.time()
    
    map_tasks = []
    for i, (worker, batch) in enumerate(zip(workers, data_batches)):
        task = worker.run(f"배치 {i+1} 처리: {batch}")
        map_tasks.append(task)
    
    map_results = await asyncio.gather(*map_tasks)
    map_time = time.time() - start
    
    print(f"✅ Map 완료: {map_time:.2f}초\n")
    
    # 3. Reduce 단계: 결과 통합
    print("🔄 Reduce 단계: 결과 통합")
    reducer = SimulatedAgent("Reducer", "결과통합", 1.0)
    
    reduce_start = time.time()
    reduce_result = await reducer.run(
        f"다음 결과들을 통합: {[r['result'] for r in map_results]}"
    )
    reduce_time = time.time() - reduce_start
    
    print(f"✅ Reduce 완료: {reduce_time:.2f}초")
    print(f"\n📊 최종 결과: {reduce_result['result']}")
    print(f"⏱️ Map-Reduce 총 시간: {map_time + reduce_time:.2f}초")


async def example_5_pipeline():
    """
    패턴 5: 파이프라인 (순차 + 병렬)
    - 단계 1: 데이터 준비 (순차)
    - 단계 2: 병렬 처리
    - 단계 3: 결과 수집 (순차)
    """
    print("\n" + "="*60)
    print("패턴 5️⃣ : 파이프라인 (순차 + 병렬)")
    print("="*60)
    
    # 1단계: 데이터 준비
    print("1️⃣ 데이터 준비:")
    prep_agent = SimulatedAgent("데이터준비", "전처리", 1.0)
    prepared = await prep_agent.run("원본 데이터 전처리")
    print(f"   {prepared['result']}\n")
    
    # 2단계: 병렬 처리
    print("2️⃣ 병렬 처리:")
    processors = [
        SimulatedAgent("분석기1", "통계분석", 1.5),
        SimulatedAgent("분석기2", "머신러닝", 2.0),
        SimulatedAgent("분석기3", "시각화", 1.2)
    ]
    
    tasks = [
        processor.run(f"전처리된 데이터 처리")
        for processor in processors
    ]
    results = await asyncio.gather(*tasks)
    print(f"   {len(results)}개 처리 완료\n")
    
    # 3단계: 결과 수집
    print("3️⃣ 결과 수집:")
    final_agent = SimulatedAgent("최종정리", "리포팅", 1.0)
    final = await final_agent.run(
        f"다음 결과들을 최종 보고서로 정리: {[r['result'] for r in results]}"
    )
    print(f"   {final['result']}")


async def example_6_graceful_shutdown():
    """
    패턴 6: 우아한 종료 + 타임아웃
    - 일부 작업 실패 시 처리
    - 타임아웃 처리
    - 부분 결과 반환
    """
    print("\n" + "="*60)
    print("패턴 6️⃣ : 우아한 종료 + 타임아웃")
    print("="*60)
    
    async def task_with_timeout(agent, task, timeout=3.0):
        """타임아웃이 있는 작업"""
        try:
            return await asyncio.wait_for(
                agent.run(task),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            print(f"⚠️ {agent.name}: 타임아웃 ({timeout}초)")
            return {"agent": agent.name, "error": "timeout"}
    
    # 1. 다양한 처리 시간을 가진 에이전트
    agents = [
        SimulatedAgent("빠른에이전트", "기본", 0.5),
        SimulatedAgent("보통에이전트", "기본", 2.0),
        SimulatedAgent("느린에이전트", "기본", 5.0)  # 타임아웃 예상
    ]
    
    # 2. 타임아웃 3초로 실행
    print("🚀 작업 시작 (타임아웃: 3초):\n")
    
    start = time.time()
    tasks = [
        task_with_timeout(agent, "작업 수행", timeout=3.0)
        for agent in agents
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time.time() - start
    
    # 3. 결과 분석
    print("\n📊 결과 분석:")
    success_count = sum(1 for r in results if "error" not in r)
    error_count = len(results) - success_count
    
    print(f"  성공: {success_count}개")
    print(f"  오류: {error_count}개")
    print(f"⏱️ 총 시간: {elapsed:.2f}초 (타임아웃으로 조기 종료)")


# =====================================================
# 3️⃣ 메인 실행
# =====================================================

async def main():
    """모든 예제 실행"""
    
    print("""
╔════════════════════════════════════════════════════════════╗
║                AutoGen 병렬 처리 예제                      ║
║              Concurrent Task Patterns in 2025             ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 각 패턴 실행
    try:
        await example_1_simple_concurrent()
        await example_2_fan_out()
        await example_3_fan_in()
        await example_4_map_reduce()
        await example_5_pipeline()
        await example_6_graceful_shutdown()
        
        print("\n" + "="*60)
        print("✅ 모든 예제 완료!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 이벤트 루프 실행
    asyncio.run(main())
