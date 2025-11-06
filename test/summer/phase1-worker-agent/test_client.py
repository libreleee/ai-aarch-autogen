"""
Phase 1 Worker Agent 테스트 클라이언트
TCP Worker Agent 서버와 통신하는 테스트 클라이언트

작성일: 2025년 11월 6일
"""

import socket
import json
import time
import threading
import logging
from typing import Dict, Any, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkerAgentTestClient:
    """TCP Worker Agent 서버를 테스트하는 클라이언트"""

    def __init__(self, host: str = 'localhost', port: int = 8888):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        self.client_id = None

    def connect(self) -> bool:
        """서버에 연결"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            logger.info(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def disconnect(self):
        """서버 연결 종료"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.is_connected = False
        self.socket = None
        logger.info("Disconnected from server")

    def _send_message(self, message: Dict[str, Any]) -> bool:
        """JSON 메시지를 서버에 전송"""
        if not self.is_connected:
            logger.error("Not connected to server")
            return False

        try:
            data = json.dumps(message).encode('utf-8')
            # 메시지 길이를 먼저 전송 (4바이트)
            length = len(data).to_bytes(4, byteorder='big')
            self.socket.send(length + data)
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def _receive_message(self) -> Optional[Dict[str, Any]]:
        """서버로부터 메시지 수신"""
        if not self.is_connected:
            logger.error("Not connected to server")
            return None

        try:
            # 메시지 길이 읽기 (4바이트)
            length_bytes = self.socket.recv(4)
            if not length_bytes:
                return None

            message_length = int.from_bytes(length_bytes, byteorder='big')

            # 메시지 데이터 읽기
            data = self.socket.recv(message_length)
            if not data:
                return None

            return json.loads(data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            return None

    def test_echo(self, message: str) -> Dict[str, Any]:
        """Echo 기능 테스트"""
        echo_request = {
            'type': 'echo',
            'data': message,
            'timestamp': time.time()
        }

        if not self._send_message(echo_request):
            return {'status': 'error', 'message': 'Failed to send echo request'}

        response = self._receive_message()
        if response:
            logger.info(f"Echo response: {response}")
            return {'status': 'success', 'response': response}
        else:
            return {'status': 'error', 'message': 'No response received'}

    def test_status(self) -> Dict[str, Any]:
        """서버 상태 조회 테스트"""
        status_request = {
            'type': 'status',
            'timestamp': time.time()
        }

        if not self._send_message(status_request):
            return {'status': 'error', 'message': 'Failed to send status request'}

        response = self._receive_message()
        if response:
            logger.info(f"Status response: {response}")
            return {'status': 'success', 'response': response}
        else:
            return {'status': 'error', 'message': 'No response received'}

    def test_raw_message(self, message: str) -> str:
        """원시 메시지 테스트 (JSON이 아닌 일반 텍스트)"""
        if not self.is_connected:
            return "Not connected"

        try:
            data = message.encode('utf-8')
            # 메시지 길이를 먼저 전송
            length = len(data).to_bytes(4, byteorder='big')
            self.socket.send(length + data)

            # 응답 수신
            length_bytes = self.socket.recv(4)
            if not length_bytes:
                return "No response"

            message_length = int.from_bytes(length_bytes, byteorder='big')
            response_data = self.socket.recv(message_length)

            response = response_data.decode('utf-8', errors='ignore')
            logger.info(f"Raw message response: {response}")
            return response

        except Exception as e:
            logger.error(f"Failed to send raw message: {e}")
            return f"Error: {e}"


def run_single_client_test(client_id: int):
    """단일 클라이언트 테스트 실행"""
    logger.info(f"Starting client {client_id}")

    client = WorkerAgentTestClient()

    try:
        # 연결
        if not client.connect():
            return

        # 잠시 대기 (서버 초기화 시간)
        time.sleep(0.1)

        # Echo 테스트
        echo_result = client.test_echo(f"Hello from client {client_id}!")
        logger.info(f"Client {client_id} echo result: {echo_result}")

        # 상태 조회 테스트
        status_result = client.test_status()
        logger.info(f"Client {client_id} status result: {status_result}")

        # 원시 메시지 테스트
        raw_result = client.test_raw_message(f"Raw message from client {client_id}")
        logger.info(f"Client {client_id} raw result: {raw_result}")

        # 추가 대기 후 종료
        time.sleep(1)

    except Exception as e:
        logger.error(f"Client {client_id} error: {e}")
    finally:
        client.disconnect()
        logger.info(f"Client {client_id} finished")


def run_multiple_clients_test(num_clients: int = 5):
    """다중 클라이언트 동시 테스트"""
    logger.info(f"Starting multiple client test with {num_clients} clients")

    threads = []

    # 각 클라이언트를 별도 스레드에서 실행
    for i in range(num_clients):
        thread = threading.Thread(target=run_single_client_test, args=(i+1,))
        threads.append(thread)
        thread.start()

        # 약간의 지연을 주어 동시에 연결되지 않도록 함
        time.sleep(0.1)

    # 모든 스레드가 완료될 때까지 대기
    for thread in threads:
        thread.join()

    logger.info("Multiple client test completed")


def run_load_test(num_clients: int = 20, duration: int = 30):
    """부하 테스트 - 지정된 시간 동안 다수의 클라이언트가 지속적으로 요청"""
    logger.info(f"Starting load test with {num_clients} clients for {duration} seconds")

    start_time = time.time()
    threads = []

    def load_client_worker(client_id: int):
        client = WorkerAgentTestClient()
        messages_sent = 0

        try:
            if not client.connect():
                return

            while time.time() - start_time < duration:
                # Echo 메시지 전송
                result = client.test_echo(f"Load test message {messages_sent + 1} from client {client_id}")
                if result['status'] == 'success':
                    messages_sent += 1

                # 짧은 지연
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Load client {client_id} error: {e}")
        finally:
            client.disconnect()
            logger.info(f"Load client {client_id} sent {messages_sent} messages")

    # 클라이언트 스레드 시작
    for i in range(num_clients):
        thread = threading.Thread(target=load_client_worker, args=(i+1,))
        threads.append(thread)
        thread.start()

        # 천천히 시작하여 서버 부하를 점진적으로 증가
        time.sleep(0.05)

    # 모든 스레드가 완료될 때까지 대기
    for thread in threads:
        thread.join()

    total_time = time.time() - start_time
    logger.info(f"Load test completed in {total_time:.2f} seconds")


def main():
    """메인 테스트 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='TCP Worker Agent Test Client')
    parser.add_argument('--test', choices=['single', 'multiple', 'load'], default='single',
                       help='Test type to run')
    parser.add_argument('--clients', type=int, default=5,
                       help='Number of clients for multiple/load test')
    parser.add_argument('--duration', type=int, default=30,
                       help='Duration in seconds for load test')

    args = parser.parse_args()

    logger.info(f"Starting {args.test} test...")

    if args.test == 'single':
        run_single_client_test(1)
    elif args.test == 'multiple':
        run_multiple_clients_test(args.clients)
    elif args.test == 'load':
        run_load_test(args.clients, args.duration)


if __name__ == "__main__":
    main()