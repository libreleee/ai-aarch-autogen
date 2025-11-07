import os
from dotenv import load_dotenv

# .env 로드
load_dotenv()

print('🔍 환경 변수 상태 확인:')
print(f'GOOGLE_API_KEY: {"설정됨" if os.getenv("GOOGLE_API_KEY") else "미설정"}')
print(f'GEMINI_API_KEY: {"설정됨" if os.getenv("GEMINI_API_KEY") else "미설정"}')

# GEMINI_API_KEY 제거
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]
    print('✅ GEMINI_API_KEY 환경 변수에서 제거됨')

print(f'제거 후 GEMINI_API_KEY: {"설정됨" if os.getenv("GEMINI_API_KEY") else "미설정"}')

# Google API 초기화 테스트
try:
    import google.generativeai as genai
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if google_api_key:
        genai.configure(api_key=google_api_key)
        print('✅ Google API 초기화 성공')
        print(f'   API 키: {google_api_key[:10]}...')
    else:
        print('❌ GOOGLE_API_KEY를 찾을 수 없음')
except Exception as e:
    print(f'❌ Google API 초기화 실패: {e}')