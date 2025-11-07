"""
Phase 1: Worker Agent Pattern 적용 - TCP 서버
AutoGen Worker Agent 패턴을 TCP 클라이언트-서버 시스템에 적용

작성일: 2025년 11월 6일
"""

import asyncio
import logging
import socket
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import json

# AutoGen 통합
try:
    from autogen import AssistantAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("Warning: AutoGen not available. Install with: pip install autogen")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('worker_agent_tcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ClientConnection:
    """클라이언트 연결 정보"""
    socket: socket.socket
    address: Tuple[str, int]
    connection_id: str
    connected_at: float
    last_activity: float


@dataclass
class WorkerTask:
    """Worker가 처리할 작업"""
    task_id: str
    client_connection: ClientConnection
    task_type: str  # 'connect', 'message', 'disconnect'
    data: Optional[bytes] = None
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class TCPWorkerAgent:
    """
    각 클라이언트 연결을 처리하는 Worker Agent
    AutoGen Worker Agent 패턴 기반 구현
    """

    def __init__(self, worker_id: str, orchestrator):
        self.worker_id = worker_id
        self.orchestrator = orchestrator
        self.is_active = True
        self.current_task: Optional[WorkerTask] = None
        self.processed_tasks = 0
        self.start_time = time.time()
        self.logger = logging.getLogger(f"TCPWorkerAgent-{worker_id}")
        
        # AutoGen AssistantAgent 초기화
        if AUTOGEN_AVAILABLE:
            self.agent = AssistantAgent(
                name=f"Worker_{worker_id}",
                system_message=f"""You are a specialized coding assistant (Worker {worker_id}).
You excel at generating high-quality Python code for various tasks.
Always provide complete, runnable code with proper imports and documentation.
Focus on clean, maintainable code that follows Python best practices.""",
                llm_config={
                    "model": "gemini-2.5-flash-lite",
                    "api_type": "google",
                    "client_host": "https://generativelanguage.googleapis.com"
                }
            )
            self.logger.info(f"AutoGen AssistantAgent initialized for Worker {worker_id}")
        else:
            self.agent = None
            self.logger.warning(f"AutoGen not available for Worker {worker_id}")

    async def process_task(self, task: WorkerTask) -> Dict:
        """
        Worker Agent의 메인 처리 로직
        """
        self.current_task = task
        self.logger.info(f"Processing task {task.task_id} for client {task.client_connection.connection_id}")

        try:
            if task.task_type == 'connect':
                result = await self._handle_client_connect(task)
            elif task.task_type == 'message':
                result = await self._handle_client_message(task)
            elif task.task_type == 'disconnect':
                result = await self._handle_client_disconnect(task)
            else:
                result = {'status': 'error', 'message': f'Unknown task type: {task.task_type}'}

            self.processed_tasks += 1
            self.logger.info(f"Task {task.task_id} completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Error processing task {task.task_id}: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            self.current_task = None

    async def _handle_client_connect(self, task: WorkerTask) -> Dict:
        """새로운 클라이언트 연결 처리"""
        client = task.client_connection
        self.logger.info(f"New client connected: {client.connection_id} from {client.address}")

        # 환영 메시지 전송
        welcome_msg = {
            'type': 'welcome',
            'message': f'Connected to TCP Worker Agent Server (Worker: {self.worker_id})',
            'client_id': client.connection_id,
            'timestamp': time.time()
        }

        try:
            await self._send_json_message(client.socket, welcome_msg)
            return {
                'status': 'success',
                'action': 'client_connected',
                'client_id': client.connection_id,
                'worker_id': self.worker_id
            }
        except Exception as e:
            return {'status': 'error', 'message': f'Failed to send welcome message: {e}'}

    async def _handle_client_message(self, task: WorkerTask) -> Dict:
        """클라이언트 메시지 처리"""
        client = task.client_connection
        data = task.data

        if not data:
            return {'status': 'error', 'message': 'No data received'}

        try:
            # 메시지 파싱 (JSON 형식 가정)
            message = json.loads(data.decode('utf-8'))
            self.logger.info(f"Received message from {client.connection_id}: {message}")

            # 메시지 타입에 따른 처리
            if message.get('type') == 'echo':
                # Echo 요청 처리
                response = {
                    'type': 'echo_response',
                    'original_message': message.get('data'),
                    'timestamp': time.time(),
                    'worker_id': self.worker_id
                }
                await self._send_json_message(client.socket, response)

            elif message.get('type') == 'status':
                # 상태 요청 처리
                status_info = {
                    'type': 'status_response',
                    'server_status': 'running',
                    'worker_id': self.worker_id,
                    'uptime': time.time() - self.start_time,
                    'processed_tasks': self.processed_tasks,
                    'autogen_available': AUTOGEN_AVAILABLE,
                    'timestamp': time.time()
                }
                await self._send_json_message(client.socket, status_info)

            elif message.get('type') == 'generate_code' and self.agent:
                # AutoGen을 통한 코드 생성
                result = await self._generate_code_with_autogen(message)
                response = {
                    'type': 'code_generated',
                    'task_id': message.get('task_id'),
                    'code': result.get('code'),
                    'quality_score': result.get('quality_score', 0),
                    'worker_id': self.worker_id,
                    'timestamp': time.time()
                }
                await self._send_json_message(client.socket, response)

            elif message.get('type') == 'generate_code' and not self.agent:
                # AutoGen 미사용 시 에러 응답
                error_response = {
                    'type': 'error',
                    'message': 'AutoGen not available on this worker',
                    'task_id': message.get('task_id'),
                    'worker_id': self.worker_id,
                    'timestamp': time.time()
                }
                await self._send_json_message(client.socket, error_response)

            else:
                # 알 수 없는 메시지 타입
                error_response = {
                    'type': 'error',
                    'message': f'Unknown message type: {message.get("type")}',
                    'timestamp': time.time()
                }
                await self._send_json_message(client.socket, error_response)

            return {
                'status': 'success',
                'action': 'message_processed',
                'client_id': client.connection_id,
                'message_type': message.get('type')
            }

        except json.JSONDecodeError:
            # JSON 파싱 실패 - 일반 텍스트로 처리
            self.logger.info(f"Received raw message from {client.connection_id}: {data}")

            # Echo 응답
            response = f"Echo from Worker {self.worker_id}: {data.decode('utf-8', errors='ignore')}"
            await self._send_raw_message(client.socket, response.encode())

            return {
                'status': 'success',
                'action': 'raw_message_processed',
                'client_id': client.connection_id
            }

        except Exception as e:
            return {'status': 'error', 'message': f'Failed to process message: {e}'}

    async def _handle_client_disconnect(self, task: WorkerTask) -> Dict:
        """클라이언트 연결 종료 처리"""
        client = task.client_connection
        self.logger.info(f"Client disconnected: {client.connection_id}")

        try:
            # 정리 작업
            client.socket.close()
            return {
                'status': 'success',
                'action': 'client_disconnected',
                'client_id': client.connection_id
            }
        except Exception as e:
            return {'status': 'error', 'message': f'Failed to disconnect client: {e}'}

    async def _send_json_message(self, client_socket: socket.socket, message: dict):
        """JSON 메시지를 클라이언트에게 전송"""
        try:
            data = json.dumps(message).encode('utf-8')
            # 메시지 길이를 먼저 전송 (4바이트)
            length = len(data).to_bytes(4, byteorder='big')
            client_socket.send(length + data)
        except Exception as e:
            self.logger.error(f"Failed to send JSON message: {e}")
            raise

    async def _generate_code_with_autogen(self, message: dict) -> Dict:
        """AutoGen을 사용하여 코드 생성"""
        if not self.agent:
            return {'error': 'AutoGen not available'}

        prompt = message.get('prompt', '')
        task_id = message.get('task_id', 'unknown')

        try:
            self.logger.info(f"Generating code for task {task_id} with AutoGen")

            # AutoGen을 통한 코드 생성
            # 실제로는 UserProxyAgent와의 대화가 필요하지만, 여기서는 직접 호출
            code_prompt = f"""
Generate Python code for the following requirement:

{prompt}

Requirements:
- Provide complete, runnable Python code
- Include proper imports
- Add docstrings and comments
- Follow Python best practices
- Make the code production-ready

Return only the Python code in a code block:
```python
# Your code here
```
"""

            # AutoGen generate_reply 사용 (비동기)
            response = await self.agent.generate_reply(code_prompt)
            
            # 응답에서 코드 추출
            generated_code = self._extract_code_from_response(response)
            
            # 코드 품질 평가 (간단한 휴리스틱)
            quality_score = self._evaluate_code_quality(generated_code)
            
            self.logger.info(f"Code generated for task {task_id}, quality: {quality_score}/10")
            
            return {
                'code': generated_code,
                'quality_score': quality_score,
                'task_id': task_id
            }

        except Exception as e:
            self.logger.error(f"Error generating code with AutoGen: {e}")
            return {'error': str(e), 'task_id': task_id}

    def _extract_code_from_response(self, response) -> str:
        """AutoGen 응답에서 코드 추출"""
        if isinstance(response, str):
            content = response
        elif hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
        
        # 코드 블록에서 추출
        import re
        code_match = re.search(r'```python\s*\n(.*?)\n```', content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # 코드 블록 없이도 코드가 있을 수 있음
        return content.strip()

    def _evaluate_code_quality(self, code: str) -> float:
        """코드 품질 평가 (간단한 점수화)"""
        score = 5.0  # 기본 점수
        
        # 길이 기반 점수
        if len(code) > 100:
            score += 1
        if len(code) > 500:
            score += 1
        
        # 구조적 요소 확인
        if 'import ' in code:
            score += 0.5
        if 'def ' in code:
            score += 0.5
        if 'class ' in code:
            score += 0.5
        if '"""' in code or "'''" in code:
            score += 0.5
        if 'try:' in code:
            score += 0.5
        if 'except:' in code:
            score += 0.5
        
        # 최대 10점
        return min(score, 10.0)

    def get_stats(self) -> Dict:
        """Worker의 현재 통계 정보"""
        return {
            'worker_id': self.worker_id,
            'is_active': self.is_active,
            'processed_tasks': self.processed_tasks,
            'uptime': time.time() - self.start_time,
            'current_task': self.current_task.task_id if self.current_task else None
        }


class TCPOrchestrator:
    """
    연결을 Worker Agent들에게 분배하는 Orchestrator
    AutoGen Orchestrator 패턴 기반 구현
    """

    def __init__(self, host: str = 'localhost', port: int = 8888, num_workers: int = 4):
        self.host = host
        self.port = port
        self.num_workers = num_workers
        self.workers: Dict[str, TCPWorkerAgent] = {}
        self.task_queue = asyncio.Queue()
        self.active_connections: Dict[str, ClientConnection] = {}
        self.is_running = False
        self.logger = logging.getLogger("TCPOrchestrator")

        # 통계 정보
        self.total_connections = 0
        self.total_tasks = 0
        self.start_time = time.time()

    async def start(self):
        """Orchestrator 시작"""
        self.logger.info(f"Starting TCP Orchestrator on {self.host}:{self.port} with {self.num_workers} workers")

        # Worker Agent들 생성
        for i in range(self.num_workers):
            worker_id = f"worker-{i+1}"
            self.workers[worker_id] = TCPWorkerAgent(worker_id, self)

        self.is_running = True

        # 서버 소켓 생성 및 바인딩
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)
        self.server_socket.setblocking(False)

        self.logger.info("TCP Orchestrator started successfully")

        # 메인 이벤트 루프 시작
        await self._run_event_loop()

    async def _run_event_loop(self):
        """메인 이벤트 루프"""
        # Worker 태스크 처리 태스크들 생성
        worker_tasks = []
        for worker in self.workers.values():
            task = asyncio.create_task(self._worker_task_processor(worker))
            worker_tasks.append(task)

        # 연결 수락 태스크
        accept_task = asyncio.create_task(self._accept_connections())

        # 모든 태스크 실행
        try:
            await asyncio.gather(accept_task, *worker_tasks)
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            await self._shutdown()

    async def _accept_connections(self):
        """새로운 클라이언트 연결을 수락하고 Worker들에게 분배"""
        loop = asyncio.get_event_loop()

        while self.is_running:
            try:
                # 비동기적으로 연결 수락
                client_socket, client_address = await loop.sock_accept(self.server_socket)

                # 연결 ID 생성
                connection_id = f"conn-{int(time.time() * 1000)}-{len(self.active_connections)}"

                # ClientConnection 객체 생성
                connection = ClientConnection(
                    socket=client_socket,
                    address=client_address,
                    connection_id=connection_id,
                    connected_at=time.time(),
                    last_activity=time.time()
                )

                self.active_connections[connection_id] = connection
                self.total_connections += 1

                self.logger.info(f"Accepted connection {connection_id} from {client_address}")

                # 연결 처리 태스크 생성 및 큐에 추가
                task = WorkerTask(
                    task_id=f"task-{self.total_tasks}",
                    client_connection=connection,
                    task_type='connect'
                )

                await self.task_queue.put(task)
                self.total_tasks += 1

                # 클라이언트 메시지 리스닝 태스크 시작
                asyncio.create_task(self._handle_client_messages(connection))

            except Exception as e:
                self.logger.error(f"Error accepting connection: {e}")
                await asyncio.sleep(0.1)

    async def _handle_client_messages(self, connection: ClientConnection):
        """특정 클라이언트의 메시지를 처리"""
        loop = asyncio.get_event_loop()

        while self.is_running and connection.connection_id in self.active_connections:
            try:
                # 메시지 길이 읽기 (4바이트)
                length_bytes = await loop.sock_recv(connection.socket, 4)
                if not length_bytes:
                    # 연결 종료
                    break

                message_length = int.from_bytes(length_bytes, byteorder='big')

                # 메시지 데이터 읽기
                data = await loop.sock_recv(connection.socket, message_length)
                if not data:
                    break

                # 마지막 활동 시간 업데이트
                connection.last_activity = time.time()

                # 메시지 처리 태스크 생성
                task = WorkerTask(
                    task_id=f"task-{self.total_tasks}",
                    client_connection=connection,
                    task_type='message',
                    data=data
                )

                await self.task_queue.put(task)
                self.total_tasks += 1

            except Exception as e:
                self.logger.error(f"Error handling messages from {connection.connection_id}: {e}")
                break

        # 연결 종료 처리
        if connection.connection_id in self.active_connections:
            disconnect_task = WorkerTask(
                task_id=f"task-{self.total_tasks}",
                client_connection=connection,
                task_type='disconnect'
            )
            await self.task_queue.put(disconnect_task)
            self.total_tasks += 1

            del self.active_connections[connection.connection_id]

    async def _worker_task_processor(self, worker: TCPWorkerAgent):
        """특정 Worker의 태스크를 처리"""
        while self.is_running:
            try:
                # 큐에서 태스크 가져오기
                task = await self.task_queue.get()

                # Worker에게 태스크 처리 요청
                result = await worker.process_task(task)

                # 결과 로깅
                if result['status'] == 'success':
                    self.logger.debug(f"Task {task.task_id} completed by {worker.worker_id}")
                else:
                    self.logger.error(f"Task {task.task_id} failed: {result.get('message', 'Unknown error')}")

                self.task_queue.task_done()

            except Exception as e:
                self.logger.error(f"Error in worker task processor: {e}")
                await asyncio.sleep(0.1)

    def get_available_worker(self) -> TCPWorkerAgent:
        """가장 적은 작업을 가진 Worker 선택 (단순 라운드 로빈)"""
        # 현재 가장 적은 태스크를 가진 Worker 찾기
        available_workers = [(w, w.processed_tasks) for w in self.workers.values() if w.is_active]
        if not available_workers:
            # 모든 Worker가 비활성화된 경우 첫 번째 Worker 반환
            return list(self.workers.values())[0]

        # 가장 적은 태스크를 가진 Worker 선택
        available_workers.sort(key=lambda x: x[1])
        return available_workers[0][0]

    async def _shutdown(self):
        """정상적인 종료 처리"""
        self.logger.info("Shutting down TCP Orchestrator...")

        self.is_running = False

        # 모든 연결 종료
        for connection in self.active_connections.values():
            try:
                connection.socket.close()
            except:
                pass

        self.active_connections.clear()

        # 서버 소켓 종료
        try:
            self.server_socket.close()
        except:
            pass

        self.logger.info("TCP Orchestrator shutdown complete")

    def get_stats(self) -> Dict:
        """Orchestrator의 현재 통계 정보"""
        worker_stats = {worker_id: worker.get_stats() for worker_id, worker in self.workers.items()}

        return {
            'orchestrator': {
                'host': self.host,
                'port': self.port,
                'num_workers': self.num_workers,
                'is_running': self.is_running,
                'total_connections': self.total_connections,
                'total_tasks': self.total_tasks,
                'active_connections': len(self.active_connections),
                'uptime': time.time() - self.start_time
            },
            'workers': worker_stats,
            'queue_size': self.task_queue.qsize() if hasattr(self.task_queue, 'qsize') else 0
        }


async def main():
    """메인 함수 - TCP Worker Agent 서버 실행"""
    logger.info("Starting TCP Worker Agent Server...")

    # Orchestrator 생성 및 시작
    orchestrator = TCPOrchestrator(host='localhost', port=8888, num_workers=4)

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    # asyncio 이벤트 루프 실행
    asyncio.run(main())