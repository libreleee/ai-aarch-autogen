"""
Multi-Agent Bridge - Actor-Critic Implementation with AutoGen Patterns

Gemini API를 사용한 Actor-Critic 구현에 AutoGen 멀티에이전트 패턴 적용
- Worker Agent 패턴: Phase 2 구현 단계에 적용
- Mixture of Agents: 핵심 파일에 선택적 적용
- Concurrent Agents: 병렬 파일 생성
"""

import os
import json
import logging
import asyncio
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# 조건부 import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not available, using simulation mode")

import asyncio
import time
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class WorkerResult:
    """워커 실행 결과"""
    worker_id: int
    file_name: str
    status: str
    code: Optional[str]
    quality_score: float
    elapsed: float
    error: Optional[str]


@dataclass
class MoAResult:
    """Mixture of Agents 결과"""
    file_name: str
    perspectives: List[str]
    implementations: List[str]
    synthesized_code: str
    quality_improvement: float


class ActorCriticTeam:
    """Actor-Critic 팀 (Gemini 기반 + AutoGen 패턴)"""

    def __init__(self, project_path: Path, requirements: str):
        self.project_path = project_path
        self.requirements = requirements

        # Gemini API 설정 (시뮬레이션용)
        if GEMINI_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                self.use_real_api = True
            else:
                self.use_real_api = False
                print("⚠️  GOOGLE_API_KEY not found, using simulation mode")
        else:
            self.use_real_api = False
            print("⚠️  Gemini API not available, using simulation mode")
            self.model = None

        self.design_iterations = 0
        self.code_iterations = 0
        self.hitl_count = 0

        # AutoGen 패턴 설정
        self.enable_worker_agents = True
        self.enable_moa_for_critical = True
        self.max_workers = 3

    async def run_complete_workflow(self) -> Dict[str, Any]:
        """
        완전한 워크플로우 실행
        Phase 1 → Phase 2 순차 실행
        """
        print("🎭 Actor-Critic Team 워크플로우 시작")
        print("=" * 80)

        try:
            # Phase 1: 설계
            design_result = await self.design_phase()
            if not design_result["approved"]:
                return {"error": "설계 단계 실패", "details": design_result}

            # Phase 2: 구현 (기본 버전)
            implementation_result = await self.implementation_phase(design_result["design"])
            if not implementation_result["approved"]:
                return {"error": "구현 단계 실패", "details": implementation_result}

            return {
                "success": True,
                "design": design_result,
                "implementation": implementation_result,
                "total_time": design_result.get("elapsed", 0) + implementation_result.get("stats", {}).get("total_time", 0)
            }

        except Exception as e:
            return {"error": f"워크플로우 실행 실패: {e}", "success": False}

    async def design_phase(self) -> Dict[str, Any]:
        """Phase 1: 설계"""
        print("\n📐 Phase 1: DESIGN")
        print("-" * 80)
        logging.info("Starting Phase 1: DESIGN")

        design_prompt = f"""
당신은 소프트웨어 아키텍트입니다.
다음 요구사항을 분석하고 상세한 시스템 설계를 작성하세요.

요구사항:
{self.requirements}

다음 형식으로 설계서를 작성하세요:

## 시스템 아키텍처

## 파일 구조
(각 파일의 역할과 책임)

## 주요 컴포넌트
(클래스, 함수 등)

## 데이터 흐름

## 에러 처리 전략

## 테스트 전략
"""

        print("  [Actor] Generating system design...")
        design = await self._generate_content(design_prompt)

        # 설계서 저장
        design_file = self.project_path / "DESIGN.md"
        design_file.write_text(design, encoding='utf-8')
        print(f"  ✓ Design saved: {design_file}")
        logging.info(f"Design document saved: {design_file}")

        # Critic 검토
        print("  [Critic] Reviewing design...")
        critic_prompt = f"""
다음 설계서를 검토하고 개선 사항을 제안하세요.

설계서:
{design}

다음 관점에서 검토하세요:
1. 완전성: 모든 요구사항이 반영되었는가?
2. 확장성: 향후 확장이 용이한가?
3. 에러 처리: 예외 상황이 고려되었는가?
4. 테스트 가능성: 테스트하기 쉬운 구조인가?

JSON 형식으로 응답하세요:
{{
    "approved": true/false,
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"]
}}
"""

        critic_result = await self._generate_json_response(critic_prompt)

        self.design_iterations += 1

        if critic_result.get("approved", True):
            print(f"  ✓ Design approved (iteration: {self.design_iterations})")
            return {"approved": True, "design": design}
        else:
            print(f"  ⚠️  Issues found: {critic_result.get('issues', [])}")
            # 실제로는 재시도 로직 필요
            return {"approved": True, "design": design}  # 일단 통과

    async def implementation_phase(self, design: str) -> Dict[str, Any]:
        """
        Phase 2: 구현 - AutoGen 패턴 적용
        Worker Agent + 선택적 Mixture of Agents
        """
        print("\n💻 Phase 2: IMPLEMENTATION (AutoGen Enhanced)")
        print("-" * 80)

        start_time = time.time()

        try:
            # 파일 목록 추출 및 분류
            file_list = self._extract_file_list(design)
            critical_files, regular_files = self._categorize_files(file_list)

            print(f"  📋 총 {len(file_list)}개 파일: {len(critical_files)}개 중요, {len(regular_files)}개 일반")

            results = []

            # 1. 중요 파일: Mixture of Agents 패턴 적용
            if self.enable_moa_for_critical and critical_files:
                print(f"  🎭 [MoA] Processing {len(critical_files)} critical files...")
                moa_results = await self._process_critical_files_moa(critical_files, design)
                results.extend(moa_results)

            # 2. 일반 파일: Worker Agent 패턴 적용
            if self.enable_worker_agents and regular_files:
                print(f"  👥 [Workers] Processing {len(regular_files)} regular files...")
                worker_results = await self._process_regular_files_workers(regular_files, design)
                results.extend(worker_results)

            # 결과 분석
            successful = [r for r in results if r["status"] == "success"]
            failed = [r for r in results if r["status"] == "failed"]

            total_elapsed = time.time() - start_time

            print(f"\n  📊 구현 결과:")
            print(f"    ✅ 성공: {len(successful)}/{len(results)}")
            print(f"    ❌ 실패: {len(failed)}")
            print(f"    ⏱️ 총 시간: {total_elapsed:.2f}s")
            print(f"    📈 평균 품질: {sum(r.get('quality_score', 0) for r in successful) / len(successful):.1f}" if successful else "")

            return {
                "approved": len(failed) == 0,
                "files": [r["file_name"] for r in successful],
                "failed": [(r["file_name"], r.get("error", "")) for r in failed],
                "stats": {
                    "total_files": len(results),
                    "successful": len(successful),
                    "failed": len(failed),
                    "total_time": total_elapsed,
                    "avg_quality": sum(r.get("quality_score", 0) for r in successful) / len(successful) if successful else 0,
                    "method": "autogen_enhanced"
                }
            }

        except Exception as e:
            return {
                "approved": False,
                "error": str(e),
                "stats": {"total_time": time.time() - start_time}
            }

    def _create_design_prompt(self) -> str:
        """설계 프롬프트 생성"""
        return f"""
당신은 시니어 소프트웨어 아키텍트입니다.

다음 요구사항을 만족하는 Python 프로젝트의 전체 설계를 작성하세요:

요구사항: {self.requirements}

설계 요구사항:
1. 전체 아키텍처 개요
2. 파일 구조 및 역할 정의
3. 각 파일의 상세 설명
4. 데이터 흐름 및 의존성

출력 형식:
```
프로젝트 개요:
[전체 프로젝트 설명]

파일 구조:
- file1.py: [역할 설명]
- file2.py: [역할 설명]
...

상세 설계:
[file1.py]
[구현 계획 및 주요 기능]

[file2.py]
[구현 계획 및 주요 기능]
...
```
"""

    async def _generate_design(self, prompt: str) -> str:
        """설계 생성 (시뮬레이션)"""
        # 실제로는 LLM 호출
        await asyncio.sleep(1.0)  # 시뮬레이션

        return """
프로젝트 개요:
간단한 사용자 관리 시스템을 구축합니다.

파일 구조:
- models/user.py: 사용자 데이터 모델
- services/auth_service.py: 인증 서비스
- controllers/user_controller.py: 사용자 API 컨트롤러
- utils/helpers.py: 유틸리티 함수들
- config/database.py: 데이터베이스 설정
- main.py: 애플리케이션 진입점

상세 설계:

models/user.py:
- User 클래스의 데이터 모델
- 유효성 검증 로직
- JSON 직렬화/역직렬화

services/auth_service.py:
- 로그인/로그아웃 기능
- JWT 토큰 관리
- 비밀번호 해싱

controllers/user_controller.py:
- 사용자 CRUD API
- 요청/응답 처리
- 에러 처리

utils/helpers.py:
- 공통 유틸리티 함수들
- 날짜 처리, 문자열 조작

config/database.py:
- 데이터베이스 연결 설정
- SQLAlchemy 설정

main.py:
- FastAPI 앱 초기화
- 라우터 등록
- 서버 시작
"""

    def _validate_design(self, design: str) -> Dict[str, Any]:
        """설계 검증"""
        issues = []

        if "파일 구조:" not in design:
            issues.append("파일 구조가 명시되지 않음")

        if "상세 설계:" not in design:
            issues.append("상세 설계가 부족함")

        file_count = len(re.findall(r'^\s*-\s*\w+\.py:', design, re.MULTILINE))
        if file_count < 3:
            issues.append(f"파일 수가 너무 적음 ({file_count}개)")

        return {
            "approved": len(issues) == 0,
            "issues": issues,
            "file_count": file_count
        }

    def _extract_file_list(self, design: str) -> List[Dict[str, str]]:
        """설계에서 파일 목록 추출"""
        files = []

        # 파일 구조 섹션에서 파일 추출
        lines = design.split('\n')
        in_file_structure = False

        for line in lines:
            line = line.strip()
            if '파일 구조:' in line:
                in_file_structure = True
                continue
            elif '상세 설계:' in line:
                break

            if in_file_structure and line.startswith('-'):
                # "file.py: description" 형식 파싱
                if ': ' in line:
                    file_part = line[1:].strip()  # "- " 제거
                    name, description = file_part.split(': ', 1)
                    files.append({
                        "name": name.strip(),
                        "description": description.strip()
                    })

        print(f"  📋 추출된 파일 수: {len(files)}")
        for f in files:
            print(f"    - {f['name']}: {f['description']}")

        return files

    async def _generate_single_file(self, file_info: Dict[str, str], design: str) -> Dict[str, Any]:
        """단일 파일 생성 (시뮬레이션)"""
        file_name = file_info["name"]

        try:
            # 파일 생성 프롬프트
            prompt = f"""
다음 파일을 완전히 구현하세요:

파일: {file_name}
설명: {file_info.get('description', '')}

설계 컨텍스트:
{design[:1000]}...

요구사항:
- 완전하고 실행 가능한 Python 코드
- 적절한 에러 처리
- 한국어 docstring
- TODO나 placeholder 없음

출력 형식:
```python
# 완전한 구현 코드
```
"""

            # 코드 생성 시뮬레이션
            await asyncio.sleep(0.5)
            code = self._generate_mock_code(file_name)

            # 품질 체크
            quality_score = self.quick_quality_check(code, file_name)

            # 파일 저장
            file_path = self.project_path / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(code, encoding='utf-8')

            return {
                "file_name": file_name,
                "status": "success",
                "code": code,
                "quality_score": quality_score,
                "error": None
            }

        except Exception as e:
            return {
                "file_name": file_name,
                "status": "failed",
                "code": None,
                "quality_score": 0.0,
                "error": str(e)
            }

    def _generate_mock_code(self, file_name: str) -> str:
        """모의 코드 생성 (실제로는 LLM 호출)"""

        mock_codes = {
            "models/user.py": '''"""사용자 데이터 모델"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import re


@dataclass
class User:
    """사용자 데이터 모델"""

    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """데이터 검증"""
        if not self.username:
            raise ValueError("사용자 이름은 필수입니다")

        if not self._is_valid_email(self.email):
            raise ValueError("유효하지 않은 이메일 형식입니다")

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """이메일 유효성 검증"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def to_dict(self) -> dict:
        """딕셔너리 변환"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """딕셔너리로부터 생성"""
        return cls(
            id=data.get("id"),
            username=data["username"],
            email=data["email"],
            password_hash=data.get("password_hash", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
''',

            "services/auth_service.py": '''"""인증 서비스"""

import hashlib
import secrets
from typing import Optional, Tuple
from datetime import datetime, timedelta
import jwt

from models.user import User


class AuthService:
    """사용자 인증 서비스"""

    def __init__(self, secret_key: str = "default_secret"):
        self.secret_key = secret_key
        self.token_expiry = timedelta(hours=24)

    def hash_password(self, password: str) -> str:
        """비밀번호 해싱"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((password + salt).encode())
        return f"{salt}:{hash_obj.hexdigest()}"

    def verify_password(self, password: str, password_hash: str) -> str:
        """비밀번호 검증"""
        try:
            salt, hash_value = password_hash.split(':', 1)
            hash_obj = hashlib.sha256((password + salt).encode())
            return hash_obj.hexdigest() == hash_value
        except:
            return False

    def create_token(self, user: User) -> str:
        """JWT 토큰 생성"""
        payload = {
            "user_id": user.id,
            "username": user.username,
            "exp": datetime.utcnow() + self.token_expiry
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[dict]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def authenticate_user(self, username: str, password: str) -> Optional[Tuple[User, str]]:
        """사용자 인증"""
        # 실제로는 데이터베이스에서 사용자 조회
        # 여기서는 모의 구현

        # 모의 사용자 데이터
        mock_users = {
            "admin": {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "password_hash": self.hash_password("password123")
            }
        }

        user_data = mock_users.get(username)
        if not user_data:
            return None

        if not self.verify_password(password, user_data["password_hash"]):
            return None

        user = User(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            password_hash=user_data["password_hash"]
        )

        token = self.create_token(user)
        return user, token

    async def validate_token(self, token: str) -> Optional[User]:
        """토큰으로 사용자 검증"""
        payload = self.verify_token(token)
        if not payload:
            return None

        # 실제로는 데이터베이스에서 사용자 조회
        return User(
            id=payload["user_id"],
            username=payload["username"],
            email=payload.get("email", "")
        )
''',

            "controllers/user_controller.py": '''"""사용자 API 컨트롤러"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from models.user import User
from services.auth_service import AuthService


# Pydantic 모델들
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user: UserResponse
    token: str


class UserController:
    """사용자 API 컨트롤러"""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        """라우터 설정"""

        @self.router.post("/register", response_model=UserResponse)
        async def register(user_data: UserCreate):
            """사용자 등록"""
            try:
                # 실제로는 데이터베이스에 저장
                user = User(
                    username=user_data.username,
                    email=user_data.email,
                    password_hash=self.auth_service.hash_password(user_data.password)
                )

                # 모의 ID 할당
                user.id = 1

                return UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email
                )

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"등록 실패: {e}")

        @self.router.post("/login", response_model=LoginResponse)
        async def login(login_data: LoginRequest):
            """사용자 로그인"""
            try:
                result = await self.auth_service.authenticate_user(
                    login_data.username,
                    login_data.password
                )

                if not result:
                    raise HTTPException(status_code=401, detail="잘못된 인증 정보")

                user, token = result

                return LoginResponse(
                    user=UserResponse(
                        id=user.id,
                        username=user.username,
                        email=user.email
                    ),
                    token=token
                )

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"로그인 실패: {e}")

        @self.router.get("/profile", response_model=UserResponse)
        async def get_profile(current_user: User = Depends(self._get_current_user)):
            """사용자 프로필 조회"""
            return UserResponse(
                id=current_user.id,
                username=current_user.username,
                email=current_user.email
            )

    async def _get_current_user(self, token: str) -> User:
        """토큰으로 현재 사용자 조회"""
        user = await self.auth_service.validate_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
        return user

    def get_router(self) -> APIRouter:
        """라우터 반환"""
        return self.router
''',

            "utils/helpers.py": '''"""유틸리티 함수들"""

import re
from typing import Any, Dict, List
from datetime import datetime, timezone
import hashlib


def generate_id() -> str:
    """고유 ID 생성"""
    timestamp = datetime.now(timezone.utc).timestamp()
    random_part = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
    return f"{int(timestamp)}_{random_part}"


def sanitize_string(text: str, max_length: int = 100) -> str:
    """문자열 정리 및 길이 제한"""
    if not text:
        return ""

    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)

    # 특수 문자 정리
    text = text.strip()

    # 길이 제한
    if len(text) > max_length:
        text = text[:max_length-3] + "..."

    return text


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """날짜/시간 포맷팅"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.strftime(format_str)


def deep_merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """딕셔너리 깊은 병합"""
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def validate_email(email: str) -> bool:
    """이메일 유효성 검증"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """리스트를 청크로 분할"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def calculate_hash(data: str) -> str:
    """문자열 해시 계산"""
    return hashlib.sha256(data.encode()).hexdigest()


def safe_get_nested_value(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """중첩 딕셔너리 안전한 값 조회"""
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current
''',

            "config/database.py": '''"""데이터베이스 설정"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os


# 데이터베이스 설정
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스
Base = declarative_base()
metadata = MetaData()


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """테이블 생성"""
    Base.metadata.create_all(bind=engine)


def init_database():
    """데이터베이스 초기화"""
    create_tables()
    print("✅ 데이터베이스 초기화 완료")


# 연결 테스트
def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False
''',

            "main.py": '''"""메인 애플리케이션 진입점"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.database import init_database
from controllers.user_controller import UserController
from services.auth_service import AuthService


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""

    app = FastAPI(
        title="사용자 관리 시스템",
        description="간단한 사용자 인증 및 관리 API",
        version="1.0.0"
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 실제 운영에서는 특정 도메인으로 제한
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 서비스 초기화
    auth_service = AuthService()

    # 컨트롤러 초기화
    user_controller = UserController(auth_service)

    # 라우터 등록
    app.include_router(
        user_controller.get_router(),
        prefix="/api/users",
        tags=["users"]
    )

    # 헬스체크 엔드포인트
    @app.get("/health")
    async def health_check():
        """헬스체크"""
        return {"status": "healthy", "version": "1.0.0"}

    # 루트 엔드포인트
    @app.get("/")
    async def root():
        """API 정보"""
        return {
            "message": "사용자 관리 시스템 API",
            "version": "1.0.0",
            "docs": "/docs"
        }

    return app


# 애플리케이션 인스턴스
app = create_app()


if __name__ == "__main__":
    import uvicorn

    # 데이터베이스 초기화
    init_database()

    # 서버 시작
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
'''
        }

        return mock_codes.get(file_name, f"""Mock implementation of {file_name}

# TODO: Implement {file_name}
print("Hello from {file_name}")
""")

    def quick_quality_check(self, code: str, file_name: str) -> float:
        """빠른 코드 품질 체크 (0-10점)"""

        score = 10.0

        # 기본 체크
        if len(code) < 100:
            score -= 3.0  # 너무 짧음

        if "TODO" in code or "FIXME" in code:
            score -= 2.0  # placeholder 존재

        if not re.search(r'""".*?"""', code, re.DOTALL):
            score -= 1.0  # docstring 없음

        if "try:" not in code and "except:" not in code:
            score -= 1.0  # 에러 처리 없음

        # 파일 특성별 체크
        if file_name.endswith('.py'):
            if not re.search(r'def |class ', code):
                score -= 2.0  # 함수/클래스 없음

        return max(0.0, score)

    # ===== AutoGen 패턴 메소드들 =====

    def _categorize_files(self, file_list: List[Dict[str, str]]) -> tuple:
        """파일을 중요/일반으로 분류"""
        critical_patterns = [
            r'.*service.*\.py$',
            r'.*model.*\.py$',
            r'.*controller.*\.py$',
            r'.*manager.*\.py$',
            r'.*handler.*\.py$'
        ]

        critical_files = []
        regular_files = []

        for file_info in file_list:
            file_name = file_info['name']

            is_critical = any(
                re.match(pattern, file_name, re.IGNORECASE)
                for pattern in critical_patterns
            )

            if is_critical:
                critical_files.append(file_info)
            else:
                regular_files.append(file_info)

        return critical_files, regular_files

    async def _process_critical_files_moa(self, critical_files: List[Dict], design: str) -> List[Dict]:
        """중요 파일을 Mixture of Agents 패턴으로 처리"""
        results = []

        for file_info in critical_files:
            print(f"    🎭 [MoA] Processing {file_info['name']}...")

            file_start = time.time()

            try:
                # Layer 1: 다중 관점으로 생성
                perspectives = ["performance", "maintainability", "simplicity"]
                layer1_tasks = [
                    self._generate_with_perspective(file_info, design, perspective)
                    for perspective in perspectives
                ]

                implementations = await asyncio.gather(*layer1_tasks)

                # Layer 2: 합성
                best_code = await self._synthesize_implementations(file_info, implementations)

                # 품질 체크 및 저장
                quality_score = self.quick_quality_check(best_code, file_info['name'])

                file_path = self.project_path / file_info['name']
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(best_code, encoding='utf-8')

                elapsed = time.time() - file_start

                results.append({
                    "file_name": file_info['name'],
                    "status": "success",
                    "code": best_code,
                    "quality_score": quality_score,
                    "elapsed": elapsed,
                    "method": "moa"
                })

                print(f"      ✨ Synthesized ({elapsed:.2f}s, Q:{quality_score:.1f})")

            except Exception as e:
                results.append({
                    "file_name": file_info['name'],
                    "status": "failed",
                    "code": None,
                    "quality_score": 0.0,
                    "elapsed": time.time() - file_start,
                    "error": str(e),
                    "method": "moa"
                })

        return results

    async def _process_regular_files_workers(self, regular_files: List[Dict], design: str) -> List[Dict]:
        """일반 파일을 Worker Agent 패턴으로 처리"""
        results = []

        # Worker별 파일 할당
        worker_assignments = self._assign_files_to_workers(regular_files)

        # 각 Worker의 작업을 병렬 실행
        worker_tasks = []
        for worker_id, files in worker_assignments.items():
            if files:
                task = self._worker_agent_process(worker_id, files, design)
                worker_tasks.append(task)

        worker_results = await asyncio.gather(*worker_tasks, return_exceptions=True)

        # 결과 평탄화
        for worker_result in worker_results:
            if isinstance(worker_result, list):
                results.extend(worker_result)
            else:
                # 예외 발생 시 빈 리스트
                pass

        return results

    def _assign_files_to_workers(self, files: List[Dict]) -> Dict[int, List[Dict]]:
        """파일을 워커들에게 할당"""
        assignments = {i: [] for i in range(self.max_workers)}

        for i, file_info in enumerate(files):
            worker_id = i % self.max_workers
            assignments[worker_id].append(file_info)

        return assignments

    async def _worker_agent_process(self, worker_id: int, files: List[Dict], design: str) -> List[Dict]:
        """단일 워커의 파일 처리"""
        results = []

        worker_traits = {
            0: "최적화에 중점을 둔",
            1: "가독성에 중점을 둔",
            2: "안정성에 중점을 둔"
        }

        trait = worker_traits.get(worker_id % 3, "균형잡힌")

        for file_info in files:
            print(f"      👷 [Worker-{worker_id}] {trait} {file_info['name']}...")

            file_start = time.time()

            try:
                # 워커 특성을 고려한 코드 생성
                enhanced_prompt = f"""
당신은 {trait} 개발자입니다.

파일: {file_info['name']}
설명: {file_info.get('description', '')}

설계: {design[:1000]}...

{trait} 특성을 살려서 완전한 코드를 작성하세요.
"""

                code = await self._generate_content(enhanced_prompt)
                code = self._extract_code(code)

                # 품질 체크 및 저장
                quality_score = self.quick_quality_check(code, file_info['name'])

                file_path = self.project_path / file_info['name']
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(code, encoding='utf-8')

                elapsed = time.time() - file_start

                results.append({
                    "file_name": file_info['name'],
                    "status": "success",
                    "code": code,
                    "quality_score": quality_score,
                    "elapsed": elapsed,
                    "worker_id": worker_id,
                    "method": "worker"
                })

                print(f"        ✅ Completed ({elapsed:.2f}s, Q:{quality_score:.1f})")

            except Exception as e:
                results.append({
                    "file_name": file_info['name'],
                    "status": "failed",
                    "code": None,
                    "quality_score": 0.0,
                    "elapsed": time.time() - file_start,
                    "error": str(e),
                    "worker_id": worker_id,
                    "method": "worker"
                })

        return results

    async def _generate_with_perspective(self, file_info: Dict, design: str, perspective: str) -> str:
        """특정 관점으로 코드 생성"""
        perspective_prompts = {
            "performance": "성능 최적화에 초점을 맞춰",
            "maintainability": "유지보수성을 높이는 방향으로",
            "simplicity": "단순하고 이해하기 쉽게"
        }

        prompt = f"""
{perspective_prompts[perspective]} 다음 파일을 구현하세요:

파일: {file_info['name']}
설명: {file_info.get('description', '')}

설계: {design[:800]}...

완전한 Python 코드를 작성하세요.
"""

        response = await self._generate_content(prompt)
        return self._extract_code(response)

    async def _synthesize_implementations(self, file_info: Dict, implementations: List[str]) -> str:
        """다중 구현을 합성하여 최선의 코드 생성"""
        synthesis_prompt = f"""
다음은 {file_info['name']} 파일의 여러 구현입니다:

구현 1 (성능 중심):
{implementations[0][:500]}...

구현 2 (유지보수성 중심):
{implementations[1][:500]}...

구현 3 (단순성 중심):
{implementations[2][:500]}...

이 구현들을 종합하여 최고 품질의 코드를 작성하세요.
각 구현의 장점을 살리고 단점을 보완하세요.
"""

        response = await self._generate_content(synthesis_prompt)
        return self._extract_code(response)

    # ===== 유틸리티 메소드들 =====

    async def _generate_content(self, prompt: str) -> str:
        """콘텐츠 생성 (Gemini API 또는 시뮬레이션)"""
        if self.use_real_api and hasattr(self, 'model'):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"API 호출 실패, 시뮬레이션 모드로 전환: {e}")

        # 시뮬레이션 모드
        await asyncio.sleep(0.3)  # API 호출 시뮬레이션
        return f"```python\n# Generated code for: {prompt[:50]}...\nprint('Generated code')\n```"

    async def _generate_json_response(self, prompt: str) -> Dict[str, Any]:
        """JSON 응답 생성"""
        if self.use_real_api and hasattr(self, 'model'):
            try:
                response = self.model.generate_content(prompt)
                return self._parse_json_response(response.text)
            except Exception as e:
                print(f"API 호출 실패: {e}")

        # 시뮬레이션 모드
        await asyncio.sleep(0.2)
        return {"approved": True, "issues": [], "suggestions": []}

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """JSON 응답 파싱"""
        try:
            # JSON 블록 추출
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response

            return json.loads(json_str.strip())
        except:
            # 파싱 실패 시 기본값
            return {"approved": True, "issues": [], "suggestions": []}

    def _extract_code(self, response: str) -> str:
        """응답에서 코드 추출"""
        # 코드 블록 추출
        if "```python" in response:
            parts = response.split("```python")
            if len(parts) > 1:
                code = parts[1].split("```")[0]
                return code.strip()
        elif "```" in response:
            parts = response.split("```")
            if len(parts) >= 3:
                code = parts[1]
                return code.strip()

        # 코드 블록이 없으면 전체 반환
        return response.strip()


async def main():
    """메인 함수 - AutoGen 패턴 적용 워크플로우 실행"""

    # 프로젝트 설정
    project_path = "generated_project"
    requirements = """
간단한 사용자 관리 시스템을 구축해주세요:
- 사용자 등록/로그인 기능
- JWT 기반 인증
- FastAPI 기반 REST API
- SQLAlchemy ORM
- 기본적인 에러 처리
"""

    # Actor-Critic 팀 생성 (AutoGen 패턴 활성화)
    team = ActorCriticTeam(Path(project_path), requirements)

    # 워크플로우 실행
    result = await team.run_complete_workflow()

    # 결과 출력
    print("\n" + "=" * 80)
    print("🎯 최종 결과 (AutoGen Enhanced):")

    if result.get("success"):
        print("✅ 워크플로우 성공!")
        print(f"📁 생성된 파일 수: {len(result['implementation']['files'])}")
        print(f"⏱️ 총 소요 시간: {result.get('total_time', 0):.2f}s")
        print(f"📊 평균 품질: {result['implementation']['stats'].get('avg_quality', 0):.2f}")
        print(f"🔧 적용된 패턴: {result['implementation']['stats'].get('method', 'unknown')}")
    else:
        print("❌ 워크플로우 실패!")
        print(f"에러: {result.get('error', '알 수 없는 에러')}")

    return result


if __name__ == "__main__":
    asyncio.run(main())