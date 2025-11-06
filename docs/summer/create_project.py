"""
Multi-Agent Bridge - 범용 프로젝트 생성 스크립트

이 스크립트는 Multi-Agent Bridge를 사용하여
사용자가 정의한 요구사항에 따라 프로젝트를 생성합니다.

프로젝트 요구사항은 requirements/ 디렉토리의 문서로 제공됩니다.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv
from actor_critic import run_actor_critic_workflow

# Windows 콘솔 UTF-8 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# .env 파일 로드 (프로젝트 루트의 .env만 사용)
project_root = Path(__file__).parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# ⚠️ 주의: Claude CLI는 터미널의 기존 인증 상태를 상속받아야 함
# os.environ 설정/수정하지 않음 (00_basic_cli_claude_code_file_save.py 방식)
# subprocess는 자동으로 부모 프로세스의 환경변수를 상속받음

# 로깅 설정
def setup_logging():
    """로깅 설정"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"project_creation_{timestamp}.log"
    
    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # 콘솔 핸들러 (간단하게)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    # 루트 로거 설정
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logging.info(f"📄 Log file: {log_file}")
    return log_file

# 로깅 초기화
log_file = setup_logging()

# 브릿지 내부 디렉토리 초기화
def initialize_bridge_workspace():
    """브릿지 작업 공간 초기화"""
    workspace_dirs = [
        Path("workspace/design_drafts"),
        Path("workspace/code_drafts"),
        Path("workspace/test_results"),
        Path("workspace/artifacts"),
        Path("logs")
    ]
    
    logging.info("🔧 Initializing Bridge workspace...")
    for dir_path in workspace_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.debug(f"Created directory: {dir_path}")
        print(f"  ✓ Created: {dir_path}")
    
    logging.info("✓ Bridge workspace initialized")
    print("✓ Bridge workspace initialized\n")


def select_platforms():
    """멀티 에이전트 플랫폼 선택"""
    print("="*80)
    print("🤖 멀티 에이전트 플랫폼 선택")
    print("="*80)
    
    available_platforms = {
        "1": ("agno", "Agno (Actor-Critic)"),
        "2": ("crewai", "CrewAI"),
        "3": ("langgraph", "LangGraph"),
        "4": ("autogen", "AutoGen"),
        "5": ("metagpt", "MetaGPT"),
    }
    
    for key, (_, name) in available_platforms.items():
        print(f"  {key}. {name}")
    
    print("\n사용할 플랫폼을 선택하세요 (예: 1 또는 1,3):")
    print("💡 여러 개 선택 시 생산성 비교 리포트가 생성됩니다.")
    
    try:
        selection = input("선택 (번호): ").strip()
    except EOFError:
        # YOLO 모드: 자동 선택 (기본값)
        print("[자동 모드] 기본값 '1' (Agno)로 선택합니다.")
        selection = "1"
    
    if not selection:
        # 기본값: Agno만
        selected = ["agno"]
        print(f"✓ 기본 플랫폼 선택: agno")
    else:
        # 선택 파싱
        selected_indices = [s.strip() for s in selection.split(",")]
        selected = [available_platforms[idx][0] for idx in selected_indices if idx in available_platforms]
        
        if not selected:
            selected = ["agno"]
            print(f"✓ 잘못된 입력, 기본 플랫폼 선택: agno")
        else:
            print(f"✓ 선택된 플랫폼: {', '.join(selected)}")
    
    if len(selected) > 1:
        print("📊 생산성 비교 모드 활성화\n")
    
    return selected


async def create_project():
    """범용 프로젝트 생성"""
    
    print("\n" + "="*80)
    print("🚀 Multi-Agent Bridge - Project Creation")
    print("="*80 + "\n")
    
    logging.info("="*80)
    logging.info("Starting Multi-Agent Bridge Project Creation")
    logging.info("="*80)
    
    # 1. 브릿지 워크스페이스 초기화
    initialize_bridge_workspace()
    
    # 2. 플랫폼 선택
    selected_platforms = select_platforms()
    logging.info(f"Selected platforms: {selected_platforms}")
    
    # 3. 프로젝트 정보 입력
    print("="*80)
    print("📝 프로젝트 정보 입력")
    print("="*80)
    project_name = input("프로젝트 이름: ").strip()
    if not project_name:
        project_name = "my-project"
        print(f"✓ 기본 이름 사용: {project_name}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 프로젝트 경로 설정
    new_projects_path = os.getenv("TARGET_NEW_PROJECTS_PATH", "./projects/new")
    project_base_path = Path(new_projects_path)
    
    print(f"\n📦 Creating new project: {project_name}")
    print(f"📍 Base location: {project_base_path}\n")
    
    logging.info(f"Project name: {project_name}")
    logging.info(f"Base location: {project_base_path}")
    logging.info(f"Timestamp: {timestamp}")
    
    # 4. 프로젝트 디렉토리 생성 (docs 구조 포함)
    for platform in selected_platforms:
        if len(selected_platforms) > 1:
            project_path = project_base_path / f"{project_name}-{platform}-{timestamp}"
        else:
            project_path = project_base_path / f"{project_name}-{timestamp}"
        
        project_path.mkdir(parents=True, exist_ok=True)
        
        # docs 디렉토리 구조 생성 (업계 표준)
        docs_dir = project_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # 표준 문서 디렉토리 구조
        doc_subdirs = {
            "01-requirements": "클라이언트 요구사항",
            "02-design": "시스템 설계",
            "03-rfp": "RFP 및 비용 산출",
            "04-implementation": "구현 관련 문서",
            "05-testing": "테스트 문서",
            "06-delivery": "최종 결과 및 메트릭"
        }
        
        for subdir, desc in doc_subdirs.items():
            (docs_dir / subdir).mkdir(exist_ok=True)
        
        requirements_dir = docs_dir / "01-requirements"
        
        print(f"✓ Created project directory: {project_path}")
        print(f"✓ Created docs structure: {docs_dir}")
        
        logging.info(f"Created project directory: {project_path}")
        logging.info(f"Created docs directory: {docs_dir}")
        logging.info(f"Created requirements directory: {requirements_dir}")
        
        # Git 초기화 (옵션에 따라)
        git_init = os.getenv("GIT_INIT_FOR_NEW_PROJECTS", "true").lower() == "true"
        if git_init:
            import subprocess
            try:
                subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
                print(f"✓ Initialized Git repository")
            except Exception as e:
                print(f"⚠️  Git init failed: {e}")
        
        print()
    
    # 5. 사용자 요구사항 추가 대기 (HITL)
    print("="*80)
    print("📁 사용자 요구사항 추가 (필수)")
    print("="*80)
    print(f"디렉토리: {requirements_dir}")
    print("\n다음 파일을 추가해주세요:")
    print("  - requirements.md        (프로젝트 요구사항)")
    print("\n또는 추가 문서:")
    print("  - protocol_spec.md       (프로토콜 명세)")
    print("  - test_scenarios.md      (테스트 시나리오)")
    print("\n💡 Windows 탐색기로 파일을 복사/붙여넣기 하세요:")
    print(f"   탐색기 열기: explorer \"{requirements_dir}\"")
    print("\n문서 추가 완료 후 아무 키나 눌러 계속하세요...")
    
    try:
        import msvcrt
        print("\n⏸️  대기 중 (키 입력 대기)...", end="", flush=True)
        try:
            msvcrt.getch()  # Windows에서 키 입력 대기
        except:
            # YOLO 모드: 자동 진행
            print("\n[자동 모드] 키 입력 없음, 자동으로 진행합니다.")
        print(" ✓")
    except ImportError:
        # Linux/Mac 환경
        try:
            input("\n⏸️  대기 중 (Enter 키 입력)... ")
        except EOFError:
            print("\n[자동 모드] 입력 없음, 자동으로 진행합니다.")
    
    print("✓ 계속 진행합니다.\n")
    
    # requirements.md가 없으면 기본 템플릿 생성
    default_req_file = requirements_dir / "requirements.md"
    if not default_req_file.exists():
        default_requirements = f"""# {project_name} Project Requirements

## Project Overview
Create a {project_name} project with the following requirements.

## Functional Requirements
1. Main functionality component
2. Supporting modules
3. Integration points

## Non-Functional Requirements
1. Performance requirements
2. Scalability considerations
3. Error handling and resilience

## Technical Stack
- Python 3.10+
- Standard libraries where possible
- Clear code structure with documentation

## Deliverables
1. Source code with comments
2. Unit tests
3. Documentation and README
"""
        default_req_file.write_text(default_requirements, encoding='utf-8')
        print(f"✓ Created default requirements.md: {default_req_file}")
    
    # 6. 요구사항 정의
    # 기본 요구사항 (requirements/ 디렉토리에 문서가 없을 경우)
    requirements = f"""
프로젝트: {project_name}

프로젝트 요구사항을 requirements/ 디렉토리에 추가해주세요.
추가하지 않은 경우 기본 템플릿이 사용됩니다.
"""
    
    # 참고문서 읽기
    if requirements_dir.exists():
        requirements_docs = []
        for doc_file in requirements_dir.glob("*"):
            if doc_file.is_file():
                try:
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        requirements_docs.append(f"### {doc_file.name}\n{content}")
                except Exception as e:
                    print(f"⚠️  Failed to read {doc_file}: {e}")
        
        if requirements_docs:
            requirements = requirements + "\n\n## 참고 문서\n\n" + "\n\n".join(requirements_docs)
            print(f"✓ Loaded {len(requirements_docs)} requirement documents\n")
    
    # 7. 실제 Actor-Critic 워크플로우 실행
    print("="*80)
    print("🤖 Actor-Critic Workflow")
    print("="*80)
    
    results = {}
    
    for platform in selected_platforms:
        print(f"\n[Platform: {platform.upper()}]")
        print("-" * 80)
        
        # 플랫폼별 프로젝트 경로
        if len(selected_platforms) > 1:
            current_project_path = project_base_path / f"{project_name}-{platform}-{timestamp}"
        else:
            current_project_path = project_base_path / f"{project_name}-{timestamp}"
        
        # Actor-Critic 실행
        import time
        start_time = time.time()
        
        result = await run_actor_critic_workflow(current_project_path, requirements)
        
        elapsed_time = time.time() - start_time
        result["elapsed_time"] = elapsed_time
        result["platform"] = platform
        results[platform] = result
        
        if result["success"]:
            print(f"\n✅ {platform.upper()} workflow completed in {elapsed_time:.2f}s!")
            print(f"   Files created: {len(result.get('files', []))}")
            print(f"   Design iterations: {result.get('design_iterations', 0)}")
            print(f"   Code iterations: {result.get('code_iterations', 0)}")
            
            logging.info(f"{platform.upper()} workflow completed successfully")
            logging.info(f"  Elapsed time: {elapsed_time:.2f}s")
            logging.info(f"  Files created: {result.get('files', [])}")
            logging.info(f"  Design iterations: {result.get('design_iterations', 0)}")
            logging.info(f"  Code iterations: {result.get('code_iterations', 0)}")
            logging.info(f"  Coverage: {result.get('coverage', 0)}%")
        else:
            print(f"\n❌ {platform.upper()} workflow failed: {result.get('error', 'Unknown error')}")
            logging.error(f"{platform.upper()} workflow failed: {result.get('error', 'Unknown error')}")
        
        print()
    
    # 8. 비교 리포트 (복수 플랫폼인 경우)
    if len(selected_platforms) > 1:
        print("\n" + "="*80)
        print("📊 생산성 비교 리포트")
        print("="*80)
        
        # 실제 결과 데이터
        comparison_data = []
        for platform, result in results.items():
            comparison_data.append({
                "platform": platform,
                "success": result["success"],
                "elapsed_time": result.get("elapsed_time", 0),
                "design_iterations": result.get("design_iterations", 0),
                "code_iterations": result.get("code_iterations", 0),
                "hitl_count": result.get("hitl_count", 0),
                "tests_passed": result.get("coverage", 0) > 0
            })
        
        # 테이블 출력
        print(f"\n{'Platform':<15} {'Status':<10} {'Time(s)':<10} {'Design':<10} {'Code':<10} {'HITL':<8} {'Tests':<8}")
        print("-" * 80)
        for data in comparison_data:
            status = "✅ Success" if data['success'] else "❌ Failed"
            tests = "✅ Pass" if data['tests_passed'] else "❌ Fail"
            print(f"{data['platform']:<15} {status:<10} {data['elapsed_time']:<10.2f} "
                  f"{data['design_iterations']:<10} {data['code_iterations']:<10} "
                  f"{data['hitl_count']:<8} {tests:<8}")
        
        # 가장 빠른 플랫폼
        fastest = min(comparison_data, key=lambda x: x['elapsed_time'])
        print(f"\n🏆 가장 빠른 플랫폼: {fastest['platform']} ({fastest['elapsed_time']:.2f}s)")
        
        # 리포트 저장
        report_path = project_base_path / f"comparison_report_{timestamp}.json"
        import json
        with open(report_path, 'w') as f:
            json.dump(comparison_data, f, indent=2)
        print(f"📄 상세 리포트: {report_path}\n")
    
    # 9. 완료
    print("\n" + "="*80)
    print("✅ PROJECT CREATION COMPLETED!")
    print("="*80)
    print(f"\n📍 Location: {project_base_path}")
    
    logging.info("="*80)
    logging.info("PROJECT CREATION COMPLETED!")
    logging.info("="*80)
    logging.info(f"Location: {project_base_path}")
    
    if len(selected_platforms) == 1:
        final_path = project_base_path / f"{project_name}-{timestamp}"
        print(f"📂 Project: {final_path}")
        logging.info(f"Project: {final_path}")
    else:
        print(f"📂 Projects:")
        logging.info("Projects created:")
        for platform in selected_platforms:
            project_dir = f"{project_name}-{platform}-{timestamp}/"
            print(f"   - {project_dir}")
            logging.info(f"  - {project_dir}")
    
    print("\n다음 단계:")
    print("  1. 프로젝트 디렉토리로 이동")
    print("  2. 의존성 설치: pip install -r requirements.txt")
    print("  3. 서버 실행: python server.py")
    print("  4. 클라이언트 실행: python client.py")
    print("  5. 테스트 실행: pytest tests/")
    print(f"\n📄 상세 로그: {log_file}")
    print()
    
    logging.info("Session completed successfully")


if __name__ == "__main__":
    try:
        asyncio.run(create_project())
    except KeyboardInterrupt:
        print("\n\n⚠️  작업이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
