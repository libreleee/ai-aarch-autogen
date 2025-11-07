"""
AutoGen - 멀티에이전트 협업 예제 (2025년 11월 기준)

실제 업무 시나리오: 코드 리뷰 팀
- 개발자: 코드 작성
- 보안전문가: 보안 검토
- 성능전문가: 성능 최적화 제안
- 테스트전문가: 테스트 커버리지 확인

실행: python examples/autogen/04-multi-agent-collaboration.py
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List
from enum import Enum
from dataclasses import dataclass


# =====================================================
# 1️⃣ 역할 정의
# =====================================================

class Role(Enum):
    """에이전트 역할"""
    DEVELOPER = "developer"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    LEAD = "lead"


# =====================================================
# 2️⃣ 협업 에이전트
# =====================================================

@dataclass
class Review:
    """검토 의견"""
    reviewer: str
    role: str
    issues: List[str]
    suggestions: List[str]
    score: int  # 1-10
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class CodeReviewAgent:
    """코드 리뷰 전담 에이전트"""
    
    def __init__(self, name: str, role: Role):
        self.name = name
        self.role = role
        self.reviews: List[Review] = []
        self.collaboration_history: List[str] = []
    
    async def review(self, code: str, context: str = "") -> Review:
        """
        코드 검토 수행
        
        Args:
            code: 검토할 코드
            context: 추가 컨텍스트
            
        Returns:
            Review 객체
        """
        print(f"\n🔍 {self.name}: 코드 검토 중...")
        
        # 시뮬레이션 처리
        await asyncio.sleep(1)
        
        # 역할별 검토
        if self.role == Role.SECURITY:
            review = self._security_review(code, context)
        elif self.role == Role.PERFORMANCE:
            review = self._performance_review(code, context)
        elif self.role == Role.TESTING:
            review = self._testing_review(code, context)
        else:
            review = self._default_review(code, context)
        
        self.reviews.append(review)
        print(f"✅ {self.name}: 검토 완료 (점수: {review.score}/10)")
        
        return review
    
    def _security_review(self, code: str, context: str) -> Review:
        """보안 검토"""
        issues = [
            "SQL injection 위험 가능성",
            "입력 검증 부재",
            "민감 데이터 노출 위험"
        ]
        suggestions = [
            "파라미터화된 쿼리 사용",
            "입력 검증 레이어 추가",
            "민감 정보 암호화"
        ]
        return Review(
            reviewer=self.name,
            role=self.role.value,
            issues=issues[:2],
            suggestions=suggestions[:2],
            score=6
        )
    
    def _performance_review(self, code: str, context: str) -> Review:
        """성능 검토"""
        issues = [
            "중첩된 루프로 인한 O(n²) 복잡도",
            "불필요한 메모리 할당",
            "데이터베이스 쿼리 반복"
        ]
        suggestions = [
            "해시맵 사용으로 O(n) 복잡도로 개선",
            "메모리 풀 구현",
            "배치 쿼리 사용"
        ]
        return Review(
            reviewer=self.name,
            role=self.role.value,
            issues=issues[:2],
            suggestions=suggestions[:2],
            score=7
        )
    
    def _testing_review(self, code: str, context: str) -> Review:
        """테스트 검토"""
        issues = [
            "엣지 케이스 미처리 (e.g., 빈 리스트)",
            "에러 핸들링 없음",
            "테스트 커버리지 60% 미만"
        ]
        suggestions = [
            "null/empty 테스트 케이스 추가",
            "try-catch 블록 추가",
            "유닛 테스트 40개 더 추가"
        ]
        return Review(
            reviewer=self.name,
            role=self.role.value,
            issues=issues[:2],
            suggestions=suggestions[:2],
            score=5
        )
    
    def _default_review(self, code: str, context: str) -> Review:
        """기본 검토"""
        issues = [
            "코드 주석 부재",
            "함수명이 명확하지 않음"
        ]
        suggestions = [
            "함수 목적 설명 주석 추가",
            "함수명 리팩토링 (e.g., process_data → calculate_user_stats)"
        ]
        return Review(
            reviewer=self.name,
            role=self.role.value,
            issues=issues,
            suggestions=suggestions,
            score=8
        )
    
    def add_collaboration_comment(self, comment: str):
        """협업 과정 기록"""
        self.collaboration_history.append(comment)


# =====================================================
# 3️⃣ 리더 (조정자)
# =====================================================

class ReviewLead:
    """코드 리뷰 리더 (모든 검토 조정 및 통합)"""
    
    def __init__(self):
        self.team: Dict[Role, CodeReviewAgent] = {}
        self.final_report = None
    
    def add_team_member(self, agent: CodeReviewAgent):
        """팀에 멤버 추가"""
        self.team[agent.role] = agent
        print(f"👥 팀에 추가: {agent.name} ({agent.role.value})")
    
    async def conduct_review(self, code: str, description: str = "") -> Dict:
        """
        전체 코드 리뷰 진행
        1. 각 전문가의 검토 수행 (병렬)
        2. 결과 통합
        3. 최종 리포트 생성
        """
        print("\n" + "="*70)
        print("🎯 코드 리뷰 시작")
        print("="*70)
        print(f"설명: {description}\n")
        
        # Step 1: 병렬 검토
        print("1️⃣ 병렬 검토 수행 중...\n")
        
        review_tasks = [
            agent.review(code, description)
            for agent in self.team.values()
        ]
        
        reviews = await asyncio.gather(*review_tasks)
        
        # Step 2: 결과 통합
        print("\n2️⃣ 결과 통합 중...\n")
        self.final_report = self._integrate_reviews(code, reviews)
        
        # Step 3: 최종 리포트 생성
        print("\n3️⃣ 최종 리포트 생성\n")
        
        return self.final_report
    
    def _integrate_reviews(self, code: str, reviews: List[Review]) -> Dict:
        """모든 검토를 통합해 최종 리포트 생성"""
        
        # 통계
        avg_score = sum(r.score for r in reviews) / len(reviews) if reviews else 0
        total_issues = sum(len(r.issues) for r in reviews)
        total_suggestions = sum(len(r.suggestions) for r in reviews)
        
        # 심각도별 분류
        critical_issues = [
            issue for r in reviews 
            for issue in r.issues 
            if r.role == "security"  # 보안 이슈는 심각
        ]
        
        # 우선순위별 제안
        priority_suggestions = []
        
        # 보안 제안 (최우선)
        security_agent = self.team.get(Role.SECURITY)
        if security_agent and security_agent.reviews:
            priority_suggestions.extend(security_agent.reviews[0].suggestions)
        
        # 성능 제안
        perf_agent = self.team.get(Role.PERFORMANCE)
        if perf_agent and perf_agent.reviews:
            priority_suggestions.extend(perf_agent.reviews[0].suggestions)
        
        # 테스트 제안
        test_agent = self.team.get(Role.TESTING)
        if test_agent and test_agent.reviews:
            priority_suggestions.extend(test_agent.reviews[0].suggestions)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "average_score": round(avg_score, 1),
            "total_issues": total_issues,
            "total_suggestions": total_suggestions,
            "critical_issues": critical_issues,
            "all_reviews": [
                {
                    "reviewer": r.reviewer,
                    "role": r.role,
                    "issues": r.issues,
                    "suggestions": r.suggestions,
                    "score": r.score
                }
                for r in reviews
            ],
            "priority_suggestions": priority_suggestions,
            "recommendation": self._get_recommendation(avg_score, len(critical_issues))
        }
    
    def _get_recommendation(self, avg_score: float, critical_count: int) -> str:
        """평가에 따른 권장사항"""
        if critical_count > 0:
            return "🔴 승인 불가: 심각한 보안 이슈 수정 필요"
        elif avg_score >= 8:
            return "🟢 승인 가능: 보수적인 개선 권장"
        elif avg_score >= 6:
            return "🟡 조건부 승인: 주요 이슈 수정 후 재검토"
        else:
            return "🔴 승인 불가: 주요 개선 필요"
    
    def print_report(self):
        """최종 리포트 출력"""
        if not self.final_report:
            print("❌ 검토가 완료되지 않았습니다")
            return
        
        print("\n" + "="*70)
        print("📋 최종 코드 리뷰 리포트")
        print("="*70)
        
        print(f"\n평가: {self.final_report['average_score']}/10")
        print(f"총 이슈: {self.final_report['total_issues']}개")
        print(f"총 제안: {self.final_report['total_suggestions']}개")
        
        if self.final_report['critical_issues']:
            print(f"\n🚨 심각한 이슈:")
            for issue in self.final_report['critical_issues']:
                print(f"  - {issue}")
        
        print(f"\n📋 각 검토 결과:")
        for review in self.final_report['all_reviews']:
            print(f"\n  {review['reviewer']} ({review['role']}) - 점수: {review['score']}/10")
            print(f"    이슈:")
            for issue in review['issues']:
                print(f"      - {issue}")
            print(f"    제안:")
            for suggestion in review['suggestions']:
                print(f"      - {suggestion}")
        
        print(f"\n💡 우선 처리 제안:")
        for suggestion in self.final_report['priority_suggestions'][:3]:
            print(f"  1. {suggestion}")
        
        print(f"\n🎯 최종 결정: {self.final_report['recommendation']}")
        print("="*70)


# =====================================================
# 4️⃣ 예제 코드
# =====================================================

EXAMPLE_CODE = """
def process_user_data(users):
    result = {}
    for user in users:
        for field in ['name', 'email', 'age']:
            if field not in user:
                continue
            key = field + "_" + user.get('id', 'unknown')
            value = user[field]
            result[key] = value
    
    # DB에 저장
    for key in result:
        db.query(f"INSERT INTO cache (key, value) VALUES ({key}, {result[key]})")
    
    return result
"""


# =====================================================
# 5️⃣ 메인
# =====================================================

async def main():
    """메인 실행"""
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║           AutoGen 멀티에이전트 협업 예제                      ║
║          Code Review Team - Multi-Agent Collaboration          ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # 1. 팀 구성
    print("\n👥 코드 리뷰 팀 구성:")
    
    lead = ReviewLead()
    
    security_expert = CodeReviewAgent("김보안", Role.SECURITY)
    performance_expert = CodeReviewAgent("이성능", Role.PERFORMANCE)
    testing_expert = CodeReviewAgent("박테스트", Role.TESTING)
    
    lead.add_team_member(security_expert)
    lead.add_team_member(performance_expert)
    lead.add_team_member(testing_expert)
    
    # 2. 코드 리뷰 수행
    await lead.conduct_review(
        code=EXAMPLE_CODE,
        description="사용자 데이터 처리 함수 - 신규 기능"
    )
    
    # 3. 리포트 출력
    lead.print_report()
    
    # 4. 추가 분석
    print("\n\n" + "="*70)
    print("📊 팀 협업 분석")
    print("="*70)
    
    print(f"""
✅ 병렬 검토의 장점:
  - 시간: 순차 검토 15분 → 병렬 검토 5분 (3배 빠름)
  - 다각도: 3가지 관점 동시 검토
  - 품질: 누락된 이슈 최소화

🔄 협업 프로세스:
  1. 리더: 팀 구성 및 작업 할당
  2. 각 전문가: 독립적으로 검토 (병렬)
  3. 리더: 결과 수집 및 통합
  4. 리더: 최종 리포트 생성 및 권장사항 제시

💪 이 패턴의 확장성:
  - 더 많은 전문가 추가 (영어, 문서, 유지보수성)
  - 실제 LLM API 호출로 교체
  - 자동화된 CI/CD 파이프라인 통합
    """)


if __name__ == "__main__":
    asyncio.run(main())
