"""
MCP Broker (TCP 기반)
기본 메시지 브로커 - TCP 소켓을 사용한 직접 통신
"""

import asyncio
import json
import logging
from typing import AsyncIterator, Optional, Dict, Any
from .core import MessageBroker, Message, MessageType

logger = logging.getLogger(__name__)


class MCPBroker(MessageBroker):
    """MCP TCP 기반 메시지 브로커"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9999):
        self.host = host
        self.port = port
        self.server = None
        self.clients: Dict[str, asyncio.StreamWriter] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.connected = False
    
    async def connect(self) -> None:
        """브로커 시작"""
        try:
            self.server = await asyncio.start_server(
                self._handle_client,
                self.host,
                self.port
            )
            self.connected = True
            logger.info(f"MCP Broker started on {self.host}:{self.port}")
            
            # 백그라운드에서 서버 실행
            asyncio.create_task(self._run_server())
        except Exception as e:
            logger.error(f"Failed to start MCP Broker: {e}")
            raise
    
    async def _run_server(self) -> None:
        """서버 실행"""
        async with self.server:
            await self.server.serve_forever()
    
    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """클라이언트 핸들러"""
        client_id = None
        
        try:
            while True:
                # 메시지 길이 읽기 (4 bytes, big-endian)
                length_data = await reader.readexactly(4)
                if not length_data:
                    break
                
                message_length = int.from_bytes(length_data, 'big')
                
                # 메시지 읽기
                message_data = await reader.readexactly(message_length)
                message_json = message_data.decode('utf-8')
                
                # 메시지 파싱
                message = Message.from_json(message_json)
                
                # 클라이언트 ID 저장
                if message.message_type == MessageType.REGISTER:
                    client_id = message.sender_id
                    self.clients[client_id] = writer
                    logger.info(f"Client registered: {client_id}")
                
                # 메시지 처리
                await self._process_message(message, writer)
        
        except Exception as e:
            logger.error(f"Client error: {e}")
        
        finally:
            if client_id and client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"Client disconnected: {client_id}")
            
            writer.close()
            await writer.wait_closed()
    
    async def _process_message(
        self,
        message: Message,
        writer: asyncio.StreamWriter
    ) -> None:
        """메시지 처리"""
        if message.message_type == MessageType.REQUEST:
            # 요청을 대상에게 라우팅
            if message.target_agent in self.clients:
                await self._send_message(
                    self.clients[message.target_agent],
                    message
                )
        
        elif message.message_type == MessageType.RESPONSE:
            # 응답을 대기 중인 요청에 전달
            if message.message_id in self.pending_responses:
                self.pending_responses[message.message_id].set_result(message)
        
        elif message.message_type == MessageType.BROADCAST:
            # 모든 클라이언트에게 브로드캐스트
            for client_writer in self.clients.values():
                if client_writer != writer:
                    await self._send_message(client_writer, message)
    
    async def _send_message(
        self,
        writer: asyncio.StreamWriter,
        message: Message
    ) -> None:
        """메시지 전송"""
        try:
            message_json = message.to_json()
            message_bytes = message_json.encode('utf-8')
            length = len(message_bytes).to_bytes(4, 'big')
            
            writer.write(length + message_bytes)
            await writer.drain()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def disconnect(self) -> None:
        """브로커 종료"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        self.connected = False
        logger.info("MCP Broker stopped")
    
    async def publish(self, channel: str, message: Message) -> None:
        """메시지 발행"""
        # MCP에서는 직접 클라이언트로 전송
        if channel in self.clients:
            await self._send_message(self.clients[channel], message)
    
    async def subscribe(self, channel: str) -> AsyncIterator[Message]:
        """채널 구독"""
        # MCP에서는 실시간 수신
        while self.connected:
            await asyncio.sleep(0.1)
            # 실제 구독은 클라이언트 핸들러에서 처리
            yield Message(
                message_type=MessageType.BROADCAST,
                sender_id="broker",
                payload={}
            )
    
    async def request_response(
        self,
        target_agent: str,
        message: Message,
        timeout: float = 30.0
    ) -> Optional[Message]:
        """요청-응답 패턴"""
        if target_agent not in self.clients:
            logger.error(f"Target agent not found: {target_agent}")
            return None
        
        # 응답 대기
        future = asyncio.Future()
        self.pending_responses[message.message_id] = future
        
        try:
            # 요청 전송
            await self._send_message(
                self.clients[target_agent],
                message
            )
            
            # 응답 대기
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        
        except asyncio.TimeoutError:
            logger.error(f"Request timeout: {message.message_id}")
            return None
        
        finally:
            if message.message_id in self.pending_responses:
                del self.pending_responses[message.message_id]
    
    async def broadcast(self, message: Message) -> None:
        """모든 클라이언트에게 브로드캐스트"""
        for client_writer in self.clients.values():
            await self._send_message(client_writer, message)
    
    async def store_message(self, message: Message) -> None:
        """메시지 저장"""
        # MCP에서는 메모리 저장 (또는 파일로 확장 가능)
        logger.info(f"Message stored: {message.message_id}")
    
    async def get_message_history(
        self,
        stream: str,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """메시지 히스토리 조회"""
        # MCP에서는 메모리 저장이므로 빈 리스트 반환
        return []
