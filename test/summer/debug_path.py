import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트의 .env 사용)
project_root = Path(__file__).parent.parent.parent  # test/agno의 부모의 부모 (프로젝트 루트)
env_path = project_root / ".env"
print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path, override=True)

# 프로젝트 경로 설정
new_projects_path = os.getenv("TARGET_NEW_PROJECTS_PATH", "./projects/new")
project_base_path = Path(new_projects_path)

print(f"TARGET_NEW_PROJECTS_PATH env var: {os.getenv('TARGET_NEW_PROJECTS_PATH')}")
print(f"new_projects_path: {new_projects_path}")
print(f"project_base_path: {project_base_path}")
print(f"project_base_path absolute: {project_base_path.resolve()}")