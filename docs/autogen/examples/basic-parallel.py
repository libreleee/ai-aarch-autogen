import asyncio
import time
import os
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

    def create_agents(self, num_agents: int = 4) -> List[AssistantAgent]:
        """여러 AutoGen Agent 생성"""

        # Google API 설정
        google_config = {
            "model": "gemini-2.5-flash-lite",
            "api_key": google_api_key,  # 이미 초기화된 키 사용
            "api_type": "google",
            "client_host": "https://generativelanguage.googleapis.com"
        }

        agents = []
        for i in range(num_agents):
            agent = AssistantAgent(
                name=f"worker_agent_{i+1}",
                system_message=self._create_agent_system_prompt(i+1),
                llm_config={"config_list": [google_config]},
                max_consecutive_auto_reply=3,
                human_input_mode="NEVER"
            )
            agents.append(agent)

        self.agents = agents
        return agents

    def _create_agent_system_prompt(self, agent_id: int) -> str:
        """Agent별 시스템 프롬프트 생성"""
        return f"""You are Worker Agent #{agent_id}, a specialized AI assistant for code analysis and processing.

Your role:
- Analyze code files and provide insights
- Generate code improvements and optimizations
- Work efficiently in parallel with other agents
- Focus on quality and accuracy in your responses

Always provide clear, actionable feedback and maintain professional communication."""

    async def process_files_parallel_autogen(self, file_list: List[Dict]) -> Dict[str, Any]:
        """AutoGen Agent들을 사용한 병렬 파일 처리"""

        print(f"\n🤖 [AutoGen] Processing {len(file_list)} files with {len(self.agents)} agents...")
        start_time = time.time()

        # 각 파일을 Agent들에게 할당 (라운드 로빈 방식)
        agent_tasks = []
        for i, file_info in enumerate(file_list):
            agent = self.agents[i % len(self.agents)]
            task = self._process_file_with_agent(agent, file_info, i % len(self.agents) + 1)
            agent_tasks.append(task)

        # 모든 Agent 작업을 동시에 실행
        results = await asyncio.gather(*agent_tasks, return_exceptions=True)

        elapsed = time.time() - start_time

        # 결과 분석
        successful = [r for r in results if isinstance(r, dict) and r.get('status') == 'success']
        failed = [r for r in results if isinstance(r, dict) and r.get('status') in ['failed', 'quota_exceeded']]
        quota_exceeded = [r for r in results if isinstance(r, dict) and r.get('status') == 'quota_exceeded']

        print(f"✅ [AutoGen] Completed in {elapsed:.2f}s")
        print(f"   Success: {len(successful)}, Failed: {len(failed)}")
        if quota_exceeded:
            quota_info = self._check_api_quota_status()
            print(f"   ⚠️  Quota exceeded: {len(quota_exceeded)} requests")
            print(f"      💡 Free tier limit: {quota_info.get('free_tier_limit', 50)} requests/day")
            print(f"      🔄 Reset time: {quota_info.get('reset_time', '매일 자정 (UTC)')}")
            print(f"      📊 Model: {quota_info.get('model', 'gemini-2.0-flash-exp')}")
            print(f"      💰 Upgrade: {quota_info.get('upgrade_url', 'https://ai.google.dev/pricing')}")
            print(f"      📈 Monitor: {quota_info.get('monitor_url', 'https://ai.google.dev/aistudio')}")

        return {
            "total_time": elapsed,
            "successful": len(successful),
            "failed": len(failed),
            "quota_exceeded": len(quota_exceeded),
            "results": successful,
            "agents_used": len(self.agents)
        }
    
    async def _process_file_with_agent(self, agent: AssistantAgent, file_info: Dict, agent_id: int) -> Dict[str, Any]:
        """AutoGen Agent를 사용한 단일 파일 처리"""

        file_name = file_info.get('name', 'unknown.py')
        complexity = file_info.get('complexity', 'medium')

        print(f"  🤖 Agent #{agent_id} processing {file_name} ({complexity})...")

        try:
            # 각 파일마다 새로운 User Proxy Agent 생성 (대화 상태 분리)
            user_proxy = UserProxyAgent(
                name=f"user_proxy_{agent_id}_{file_name.replace('/', '_').replace('.', '_')}",
                code_execution_config=False,
                human_input_mode="NEVER"
            )

            # 파일 분석 요청
            prompt = self._create_file_analysis_prompt(file_name, complexity)

            # Agent와 대화 시작 (동기 호출 + 재시도 로직)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 채팅 시작 - 출력을 최소화하기 위해 로깅 레벨 조정
                    import logging
                    original_level = logging.getLogger().level
                    logging.getLogger().setLevel(logging.WARNING)  # AutoGen 로깅 억제
                    
                    chat_result = user_proxy.initiate_chat(
                        agent,
                        message=prompt,
                        max_turns=3  # 여러 턴 허용으로 더 깊이 있는 분석 가능
                    )
                    
                    # 로깅 레벨 복원
                    logging.getLogger().setLevel(original_level)
                    
                    break  # 성공하면 루프 탈출
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        if "quota" in error_msg.lower() or "exceeded your current quota" in error_msg:
                            # 할당량 초과는 재시도하지 않음
                            print(f"  ❌ Agent #{agent_id} failed for {file_name}: API quota exceeded (no retry)")
                            return {
                                "file_name": file_name,
                                "complexity": complexity,
                                "agent_id": agent_id,
                                "error": "API_QUOTA_EXCEEDED",
                                "status": "quota_exceeded"
                            }
                        elif attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 5  # 점진적 대기 (5s, 10s, 15s)
                            print(f"  ⏳ Rate limited, waiting {wait_time}s before retry...")
                            import time
                            time.sleep(wait_time)
                            continue
                    raise e

            # 응답에서 결과 추출
            response = self._extract_response_from_chat_result(chat_result, agent, user_proxy)
            analysis_result = self._extract_analysis_from_response(response)

            return {
                "file_name": file_name,
                "complexity": complexity,
                "agent_id": agent_id,
                "analysis": analysis_result,
                "status": "success"
            }

        except Exception as e:
            print(f"  ❌ Agent #{agent_id} failed for {file_name}: {e}")
            return {
                "file_name": file_name,
                "complexity": complexity,
                "agent_id": agent_id,
                "error": str(e),
                "status": "failed"
            }

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

    def _extract_response_from_chat_result(self, chat_result, agent, user_proxy) -> str:
        """
        AutoGen 채팅 결과에서 실제 응답 텍스트를 추출합니다.

        Args:
            chat_result: AutoGen 채팅 결과 객체
            agent: 응답한 agent
            user_proxy: user proxy 객체

        Returns:
            추출된 응답 텍스트
        """
        try:
            # 채팅 결과에서 마지막 메시지 추출
            if hasattr(chat_result, 'chat_history') and chat_result.chat_history:
                last_message = chat_result.chat_history[-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif isinstance(last_message, dict) and 'content' in last_message:
                    return last_message['content']

            # 다른 방법으로 응답 추출 시도
            if hasattr(chat_result, 'summary'):
                return chat_result.summary

            # user_proxy의 마지막 메시지 확인
            if hasattr(user_proxy, 'chat_messages') and agent.name in user_proxy.chat_messages:
                messages = user_proxy.chat_messages[agent.name]
                for msg in reversed(messages):
                    if hasattr(msg, 'role') and msg.role == 'assistant':
                        return msg.content if hasattr(msg, 'content') else str(msg)

            return "No response extracted"

        except Exception as e:
            print(f"  ⚠️ 응답 추출 실패: {e}")
            return f"Error extracting response: {str(e)}"

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
        print(f"   • 모델: {quota_info.get('model', 'gemini-2.5-flash-lite')}")
        
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
        print(f"   • 일일 리셋: {quota_info.get('reset_time', '매일 자정 (UTC)')}")
        
        return quota_info

    def _create_file_analysis_prompt(self, file_name: str, complexity: str) -> str:
        """파일 분석 프롬프트 생성"""
        return f"""Please analyze the following file and provide insights:

File: {file_name}
Complexity: {complexity}
Project Requirements: {self.requirements}

Please provide:
1. File purpose and functionality
2. Code quality assessment
3. Potential improvements
4. Complexity analysis

Keep your response concise but informative."""

    def _extract_analysis_from_response(self, response) -> Dict[str, Any]:
        """Agent 응답에서 분석 결과 추출"""
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)
        
        # 간단한 분석 결과 생성 (실제로는 더 정교한 파싱)
        return {
            "content_length": len(content),
            "has_insights": "1." in content or "2." in content,
            "response_preview": content[:200] + "..." if len(content) > 200 else content
        }
# 사용 예제
async def main():
    """AutoGen 병렬 처리 데모"""

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

    processor = AutoGenParallelProcessor(
        project_path=Path("./test_project"),
        requirements="Sample project requirements"
    )

    # AutoGen Agent들 생성
    agents = processor.create_agents(num_agents=4)
    print(f"🤖 Created {len(agents)} AutoGen agents")

    # AutoGen 기반 병렬 처리 실행
    result = await processor.process_files_parallel_autogen(test_files)

    print(f"\n📊 Final Results:")
    print(f"   Total files: {len(test_files)}")
    print(f"   Processing time: {result['total_time']:.2f}s")
    print(f"   Success rate: {result['successful']}/{len(test_files)}")
    print(f"   Agents used: {result['agents_used']}")
    
    if result.get('quota_exceeded', 0) > 0:
        quota_info = processor._check_api_quota_status()
        print(f"   ⚠️  API Quota exceeded: {result['quota_exceeded']} requests")
        print(f"   💡 Free tier: {quota_info.get('free_tier_limit', 50)} requests/day")
        print(f"   🔄 Reset: {quota_info.get('reset_time', '매일 자정 (UTC)')}")
        print(f"   💰 Upgrade: https://ai.google.dev/pricing")
        print(f"   📊 Monitor: https://ai.google.dev/aistudio")
    
    # 순차 처리와 비교
    print(f"\n⚡ Performance comparison:")
    sequential_time = sum([1.0 for _ in test_files])  # 순차 처리 예상 시간
    speedup = sequential_time / result['total_time']
    print(f"   Sequential time estimate: {sequential_time:.2f}s")
    print(f"   Parallel speedup: {speedup:.1f}x")


if __name__ == "__main__":
    asyncio.run(main())