import time
import asyncio
from fastapi import Request, HTTPException
from typing import Dict, Optional, Callable
import threading

class RequestLimiter:
    """
    Limits the number of concurrent requests and queues excess requests.
    """
    def __init__(
        self, 
        max_concurrent: int = 5,
        max_queue_size: int = 100,
        request_timeout: int = 30
    ):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent  # Сохраняем значение отдельно
        self.max_queue_size = max_queue_size
        self.queue_size = 0
        self.request_timeout = request_timeout
        self.lock = threading.Lock()
    
    async def handle_request(self, request: Request, call_next: Callable):
        """
        Handle an incoming request with rate limiting and queuing.
        """
        # Check if queue is full
        with self.lock:
            if self.queue_size >= self.max_queue_size:
                raise HTTPException(
                    status_code=503,
                    detail="Server is at capacity. Please try again later."
                )
            self.queue_size += 1
        
        try:
            # Try to acquire semaphore with timeout
            try:
                # Wait for semaphore or timeout
                acquire_task = asyncio.create_task(self.semaphore.acquire())
                await asyncio.wait_for(acquire_task, timeout=self.request_timeout)
                
                # Process the request
                return await call_next(request)
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=503,
                    detail="Request timed out waiting in queue. Please try again later."
                )
        finally:
            # Release resources
            with self.lock:
                self.queue_size -= 1
            
            # Проверяем, нужно ли освободить семафор
            # Мы не можем проверить внутреннее значение семафора напрямую,
            # поэтому просто освобождаем его, если он был приобретен
            if acquire_task.done() and not acquire_task.exception():
                self.semaphore.release()
                