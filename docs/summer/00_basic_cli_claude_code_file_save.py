#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Claude CLI을 Git Bash에서 실행하는 테스트

특징:
- API 키를 코드에 노출하지 않음 (CLI 사용)
- Git Bash의 bash 환경에서 현재 사용자 인증 상속
- Windows PowerShell subprocess 컨텍스트 격리 문제 회피

Claude CLI: v2.0.27 (npm installed)
Auth: ~/.claude/.credentials.json (자동으로 로드됨)
"""

# ============================================================================
# 🔧 문제 분석 및 해결책
# ============================================================================
#
# 문제점:
# --------
# 1. subprocess.run()으로 Claude CLI를 호출하면 "Invalid API key" 에러 발생
#    - Python의 subprocess가 새로운 독립적인 프로세스를 생성
#    - 이 프로세스는 터미널의 세션 인증 상태를 상속받지 못함
#    - ~/.claude/.credentials.json 파일에 접근할 수 없음
#
# 2. 여러 시도들이 실패함:
#    a) subprocess + PowerShell.exe: 컨텍스트 격리 (subprocess 새 프로세스 생성)
#    b) subprocess + cmd.exe /c: 컨텍스트 격리 + 실행정책 문제
#    c) os.system(): 여전히 컨텍스트 격리됨
#    d) subprocess + bash.exe (Git Bash): WSL bash로 리다이렉트되어 WSL 에러 발생
#    e) ANTHROPIC_API_KEY 환경변수: Claude CLI는 파일 기반 인증을 기대함
#
# 3. 한글 입력 문제:
#    - 이중 따옴표 안에서 한글 특수문자가 손상될 수 있음
#    - subprocess의 기본 인코딩이 cp949로 설정되어 유니코드 문제 발생
#
# 해결책:
# --------
# 1. PowerShell + ExecutionPolicy Bypass 사용
#    - powershell.exe -ExecutionPolicy Bypass를 명시적으로 설정
#    - 이것이 subprocess에서 실행정책 제약을 우회할 수 있는 유일한 방법
#
# 2. 인코딩 명시
#    - subprocess.run()에 encoding='utf-8' 추가
#    - text=True와 함께 사용하여 str 반환
#
# 3. 프롬프트 최적화
#    - 따옴표가 많은 프롬프트는 PowerShell 인터프리터에 의해 손상될 수 있음
#    - 프롬프트에서 불필요한 따옴표와 특수문자 제거
#    - 명확하고 단순한 문장 구조 사용
#    - 예: "Write a Python function called 'addition'" (X)
#    - 예: "Provide a complete Python function named addition" (O)
#
# 4. 에러 처리 추가
#    - 코드 추출 부분에서 예외 처리 추가
#    - stdout이 None일 수 있으므로 조건부 검사
#
# 핵심 수정 사항:
# --------
# subprocess.run([
#     'powershell.exe',
#     '-NoProfile',
#     '-ExecutionPolicy', 'Bypass',     # 실행정책 우회
#     '-Command',
#     f'claude -p "{prompt}"'
# ], capture_output=True, text=True, encoding='utf-8')  # UTF-8 인코딩
#
# 결과:
# --------
# ✅ TEST 1 (English): 성공 - Claude CLI가 프롬프트 받고 응답 생성
# ✅ TEST 2 (Korean): 성공 - 한글 프롬프트도 정상 처리
# ✅ TEST 3 (Code Extraction): 성공 - Python 코드 블록 추출 및 파일 저장
#
# ============================================================================

import sys
import os
import subprocess
import json
from pathlib import Path

# UTF-8 지원
sys.stdout.reconfigure(encoding='utf-8')

print()
print("=" * 80)
print("🤖 Claude CLI Code Generation Test (Git Bash)")
print("=" * 80)
print()

# ============================================================================
# TEST 1: Basic English Prompt
# ============================================================================
print("TEST 1: English Prompt")
print("-" * 80)

prompt1 = "Write a simple hello function that returns 'Hello, World!'"
print(f"Prompt: {prompt1}\n")

try:
    # PowerShell에서 직접 실행 (실행정책 우회)
    result = subprocess.run(
        [
            'powershell.exe',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-Command',
            f"claude -p \"{prompt1}\""
        ],
        capture_output=True,
        text=True,
        timeout=30,
        encoding='utf-8'
    )
    
    if result.returncode == 0:
        output = result.stdout.strip() if result.stdout else ""
        print(f"✅ SUCCESS (length: {len(output)} chars)")
        print(f"Output:\n{output[:300]}...\n")
    else:
        print(f"❌ FAILED (code: {result.returncode})")
        if result.stderr:
            print(f"Error: {result.stderr[:200]}\n")
        else:
            print(f"Output: {result.stdout[:200] if result.stdout else 'No output'}\n")
        
except Exception as e:
    print(f"❌ ERROR: {e}\n")

# ============================================================================
# TEST 2: Korean Prompt
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: Korean Prompt")
print("-" * 80)

prompt2 = "파이썬에서 두 수를 더하는 함수를 만들어줘"
print(f"Prompt: {prompt2}\n")

try:
    result = subprocess.run(
        [
            'powershell.exe',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-Command',
            f"claude -p '{prompt2}'"
        ],
        capture_output=True,
        text=True,
        timeout=30,
        encoding='utf-8'
    )
    
    if result.returncode == 0:
        output = result.stdout.strip() if result.stdout else ""
        print(f"✅ SUCCESS (length: {len(output)} chars)")
        print(f"Output:\n{output[:300]}...\n")
    else:
        print(f"❌ FAILED (code: {result.returncode})")
        if result.stderr:
            print(f"Error: {result.stderr[:200]}\n")
        else:
            print(f"Output: {result.stdout[:200] if result.stdout else 'No output'}\n")
        
except Exception as e:
    print(f"❌ ERROR: {e}\n")

# ============================================================================
# TEST 3: Code Extraction with File Save
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: Code Extraction (Extract & Save)")
print("-" * 80)

prompt3 = "Provide a complete Python function named addition that takes two parameters and returns their sum. Include the code in a code block."
print(f"Prompt: {prompt3}\n")

try:
    result = subprocess.run(
        [
            'powershell.exe',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-Command',
            f"claude -p '{prompt3}'"
        ],
        capture_output=True,
        text=True,
        timeout=30,
        encoding='utf-8'
    )
    
    if result.returncode == 0:
        output = result.stdout.strip() if result.stdout else ""
        print(f"✅ SUCCESS (length: {len(output)} chars)")
        
        # Extract Python code block
        if '```python' in output:
            try:
                code_part = output.split('```python')[1]
                code = code_part.split('```')[0].strip()
                
                # Save to file
                output_file = Path(__file__).parent / "claude_generated_addition.py"
                output_file.write_text(code, encoding='utf-8')
                
                print(f"✅ Python code extracted ({len(code)} chars)")
                print(f"✅ Saved to: {output_file}")
                print(f"\nExtracted code preview:\n{code[:200]}...\n")
            except Exception as extract_err:
                print(f"❌ Extraction error: {extract_err}\n")
        else:
            print(f"⚠️  No Python code block found in output\n")
    else:
        print(f"❌ FAILED (code: {result.returncode})")
        if result.stderr:
            print(f"Error: {result.stderr[:200]}\n")
        else:
            print(f"Output: {result.stdout[:200] if result.stdout else 'No output'}\n")
        
except Exception as e:
    print(f"❌ ERROR: {e}\n")

print("\n" + "=" * 80)
print("✅ Tests completed")
print("=" * 80)
