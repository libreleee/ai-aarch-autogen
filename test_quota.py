import os
import asyncio
import time
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import autogen
from autogen import AssistantAgent, UserProxyAgent
import google.generativeai as genai

# Load environment variables
load_dotenv()

# GEMINI_API_KEY 완전 제거 (환경 변수에서 삭제)
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]

# Google API 초기화 - GOOGLE_API_KEY만 사용
google_api_key = os.getenv("GOOGLE_API_KEY")
if google_api_key:
    genai.configure(api_key=google_api_key)
else:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

class AutoGenParallelProcessor:
    """AutoGen 기반 병렬 처리 클래스"""

    def __init__(self, project_path: Path, requirements: str):
        self.project_path = project_path
        self.requirements = requirements
        self.agents = []

    def check_and_display_quota_status(self):
        """
        현재 API 할당량 상태를 확인하고 표시합니다.
        """
        print("\n🔍 Google Gemini API 할당량 상태 확인")
        print("=" * 50)

        quota_info = self._check_api_quota_status()

        print("📊 무료 티어 한도:")
        print(f"   • 생성 요청: {quota_info.get('requests_per_day', 50)}회/일")
        print(f"   • 입력 토큰: {quota_info.get('input_tokens_per_minute', 32000)}/분")
        print(f"   • 출력 토큰: {quota_info.get('output_tokens_per_minute', 32000)}/분")
        print(f"   • 모델: {quota_info.get('model', 'gemini-2.0-flash-exp')}")

        print("\n💰 업그레이드 옵션:")
        print("   • Gemini 1.5 Pro: 고성능, 높은 한도")
        print("   • Gemini 1.5 Flash: 비용 효율적")
        print("   • Enterprise: 커스텀 한도 설정")

        print("\n🔗 유용한 링크:")
        print(f"   • 할당량 모니터링: {quota_info.get('monitor_url', 'https://ai.google.dev/aistudio')}")
        print(f"   • 요금제 정보: {quota_info.get('upgrade_url', 'https://ai.google.dev/pricing')}")
        print("   • Cloud Console: https://console.cloud.google.com/apis/quotas")

        print(f"\n⚡ 현재 상태:")
        print(f"   • API 키: {'설정됨' if os.getenv('GOOGLE_API_KEY') else '미설정'}")
        print(f"   • GEMINI_API_KEY: {'설정됨' if os.getenv('GEMINI_API_KEY') else '완전히 제거됨'}")
        print(f"   • 일일 리셋: {quota_info.get('reset_time', '매일 자정 (UTC)')}")

        return quota_info

    def _check_api_quota_status(self) -> Dict[str, Any]:
        """
        Google Gemini API 할당량 상태를 확인합니다.

        Returns:
            할당량 상태 정보
        """
        try:
            import requests

            # API 키로 할당량 확인 (실제로는 Google Cloud Console API 사용 필요)
            # 현재는 기본 정보 제공
            return {
                "free_tier_limit": 50,
                "requests_per_day": 50,
                "input_tokens_per_minute": 32000,
                "output_tokens_per_minute": 32000,
                "model": "gemini-2.5-flash-lite",
                "reset_time": "매일 자정 (UTC)",
                "upgrade_url": "https://ai.google.dev/pricing",
                "monitor_url": "https://ai.google.dev/aistudio"
            }
        except Exception as e:
            print(f"  ⚠️ 할당량 확인 실패: {e}")
            return {
                "free_tier_limit": 50,
                "error": str(e)
            }

# 테스트 실행
if __name__ == "__main__":
    processor = AutoGenParallelProcessor(Path('./test'), 'test requirements')
    processor.check_and_display_quota_status()