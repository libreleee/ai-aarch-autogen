#!/usr/bin/env python3
"""
AutoGen Worker Agent Pattern - TCP Server Implementation

This module implements the AutoGen Worker Agent pattern using the actual AutoGen library,
adapted for TCP-based communication. It demonstrates how multiple AI agents can collaborate
to process client requests through a TCP server.

Key Components:
- TCPWorkerAgent: Individual worker agent using AutoGen AssistantAgent
- TCPOrchestrator: Manages multiple worker agents and TCP connections
- Message routing between TCP clients and AutoGen agents

LLM Configuration:
- Uses Gemini 1.5 Flash model for fast and efficient processing
- Supports both OpenAI GPT and Google Gemini models
- API key loaded from .env file (GOOGLE_API_KEY environment variable)
- Requires python-dotenv package for .env file loading

Author: AutoGen TCP Project
Date: 2025-11-06
"""

import asyncio
import json
import logging
import socket
import time
import os
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autogen_worker_agent_tcp.log'),
        logging.StreamHandler()
    ]
)

class TCPWorkerAgent:
    """Individual worker agent using AutoGen AssistantAgent for TCP-based tasks."""

    def __init__(self, worker_id: int, orchestrator_ref: 'TCPOrchestrator'):
        self.worker_id = worker_id
        self.orchestrator = orchestrator_ref
        self.logger = logging.getLogger(f'TCPWorkerAgent-worker-{worker_id}')

        # Create AutoGen agents for this worker
        self.assistant = AssistantAgent(
            name=f"worker_assistant_{worker_id}",
            system_message=f"""You are Worker Assistant {worker_id}, part of a distributed TCP-based processing system.
            Your role is to process client requests efficiently and provide helpful responses.
            Always be concise but thorough in your responses.""",
            llm_config={
                "config_list": [
                    {
                        "model": "gemini-1.5-flash",  # Using Gemini instead of GPT-4
                        "api_key": os.getenv("GOOGLE_API_KEY", "your-gemini-api-key-here"),  # Load from .env file
                    }
                ],
                "temperature": 0.7,
            }
        )

        self.user_proxy = UserProxyAgent(
            name=f"worker_proxy_{worker_id}",
            code_execution_config=False,  # Disable code execution for this demo
            human_input_mode="NEVER"
        )

        self.is_busy = False
        self.current_task = None
        self.task_count = 0

    async def process_task(self, task_data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Process a task using AutoGen agents."""
        self.is_busy = True
        self.current_task = task_data
        self.task_count += 1

        try:
            self.logger.info(f"Processing task {task_data.get('id', 'unknown')} for client {client_id}")

            # Extract task information
            task_type = task_data.get('type', 'unknown')
            message = task_data.get('data', '')

            # Create a conversation between user proxy and assistant
            chat_result = await self.user_proxy.a_initiate_chat(
                self.assistant,
                message=f"Process this {task_type} request: {message}",
                max_turns=3
            )

            # Extract the final response
            final_message = ""
            if chat_result and chat_result.chat_history:
                # Get the last assistant message
                for msg in reversed(chat_result.chat_history):
                    if msg.get('role') == 'assistant':
                        final_message = msg.get('content', '')
                        break

            result = {
                'task_id': task_data.get('id'),
                'worker_id': self.worker_id,
                'result': final_message,
                'status': 'completed',
                'timestamp': time.time()
            }

            self.logger.info(f"Task {task_data.get('id')} completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Error processing task {task_data.get('id')}: {str(e)}")
            return {
                'task_id': task_data.get('id'),
                'worker_id': self.worker_id,
                'result': f"Error: {str(e)}",
                'status': 'failed',
                'timestamp': time.time()
            }
        finally:
            self.is_busy = False
            self.current_task = None

class TCPOrchestrator:
    """Orchestrator managing multiple TCP worker agents using AutoGen."""

    def __init__(self, host: str = 'localhost', port: int = 8888, num_workers: int = 4):
        self.host = host
        self.port = port
        self.num_workers = num_workers
        self.logger = logging.getLogger('TCPOrchestrator')

        # Create worker agents
        self.workers: List[TCPWorkerAgent] = []
        for i in range(num_workers):
            worker = TCPWorkerAgent(i + 1, self)
            self.workers.append(worker)

        # TCP server components
        self.server_socket: Optional[socket.socket] = None
        self.clients: Dict[str, Tuple[socket.socket, Tuple[str, int]]] = {}
        self.task_queue = asyncio.Queue()
        self.running = False

        # Statistics
        self.total_tasks = 0
        self.active_connections = 0

    async def start(self):
        """Start the TCP orchestrator and worker agents."""
        self.logger.info(f"Starting TCP Orchestrator on {self.host}:{self.port} with {self.num_workers} workers")

        # Start worker tasks
        worker_tasks = []
        for worker in self.workers:
            task = asyncio.create_task(self._worker_loop(worker))
            worker_tasks.append(task)

        # Start TCP server
        self.running = True
        server_task = asyncio.create_task(self._run_tcp_server())

        try:
            await asyncio.gather(server_task, *worker_tasks)
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            await self._shutdown()

    async def _run_tcp_server(self):
        """Run the TCP server to accept client connections."""
        loop = asyncio.get_event_loop()

        # Create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.setblocking(False)

        self.logger.info("TCP Orchestrator started successfully")

        try:
            while self.running:
                try:
                    # Accept new connections
                    client_socket, client_address = await loop.sock_accept(self.server_socket)
                    client_id = f"{int(time.time() * 1000)}-{len(self.clients)}"
                    self.clients[client_id] = (client_socket, client_address)
                    self.active_connections += 1

                    self.logger.info(f"Accepted connection {client_id} from {client_address}")

                    # Start handling messages from this client
                    asyncio.create_task(self._handle_client_messages(client_id, client_socket))

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Error accepting connection: {e}")
                    await asyncio.sleep(0.1)

        except Exception as e:
            self.logger.error(f"TCP server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

    async def _handle_client_messages(self, client_id: str, client_socket: socket.socket):
        """Handle messages from a specific client."""
        try:
            while self.running:
                try:
                    # Receive message length (4 bytes)
                    length_bytes = await asyncio.get_event_loop().sock_recv(client_socket, 4)
                    if not length_bytes or len(length_bytes) < 4:
                        break

                    message_length = int.from_bytes(length_bytes, byteorder='big')

                    # Receive message data
                    data = await asyncio.get_event_loop().sock_recv(client_socket, message_length)
                    if not data or len(data) < message_length:
                        break

                    # Parse message
                    try:
                        message = json.loads(data.decode('utf-8'))
                        self.logger.info(f"Received message from {client_id}: {message}")

                        # Create task and add to queue
                        task = {
                            'id': f"task-{self.total_tasks + 1}",
                            'client_id': client_id,
                            'data': message,
                            'timestamp': time.time()
                        }
                        await self.task_queue.put(task)
                        self.total_tasks += 1

                    except json.JSONDecodeError:
                        self.logger.warning(f"Invalid JSON from {client_id}: {data}")

                except Exception as e:
                    self.logger.error(f"Error handling messages from {client_id}: {e}")
                    break

        except Exception as e:
            self.logger.error(f"Client handler error for {client_id}: {e}")
        finally:
            # Clean up client connection
            if client_id in self.clients:
                del self.clients[client_id]
                self.active_connections -= 1
            try:
                client_socket.close()
            except:
                pass
            self.logger.info(f"Client {client_id} disconnected")

    async def _worker_loop(self, worker: TCPWorkerAgent):
        """Main loop for a worker agent."""
        while self.running:
            try:
                # Get task from queue
                task = await self.task_queue.get()

                # Process task
                result = await worker.process_task(task['data'], task['client_id'])

                # Send result back to client
                await self._send_result_to_client(task['client_id'], result)

                self.task_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                worker.logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(0.1)

    async def _send_result_to_client(self, client_id: str, result: Dict[str, Any]):
        """Send processing result back to the client."""
        if client_id not in self.clients:
            self.logger.warning(f"Client {client_id} not found for result delivery")
            return

        client_socket, _ = self.clients[client_id]
        try:
            result_json = json.dumps(result).encode('utf-8')
            await asyncio.get_event_loop().sock_sendall(client_socket, result_json)
            self.logger.info(f"Sent result to client {client_id}")
        except Exception as e:
            self.logger.error(f"Error sending result to client {client_id}: {e}")

    async def _shutdown(self):
        """Shutdown the orchestrator and clean up resources."""
        self.logger.info("Shutting down TCP Orchestrator...")
        self.running = False

        # Close all client connections
        for client_id, (client_socket, _) in self.clients.items():
            try:
                client_socket.close()
            except:
                pass

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        self.logger.info("TCP Orchestrator shutdown complete")

async def main():
    """Main entry point."""
    logging.info("Starting TCP Worker Agent Server with AutoGen...")

    orchestrator = TCPOrchestrator(host='localhost', port=8888, num_workers=4)

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        logging.info("Server shutdown requested by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
    finally:
        logging.info("Server shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())