import os
import cv2
import numpy as np
import time
import tempfile
import asyncio
import multiprocessing
import signal
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from skimage import img_as_ubyte
from skimage.filters import gaussian
import mahotas
import uvicorn

from logger import setup_logger
from rate_limiter import RequestLimiter

# Set up logger
logger = setup_logger("image_quality_api")

# Determine optimal thread pool size based on available cores
cpu_count = max(1, multiprocessing.cpu_count())
MAX_WORKERS = int(os.getenv("MAX_WORKERS", cpu_count * 2))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", cpu_count * 3))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", 500))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))

# Create thread pool with graceful shutdown capability
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Create request limiter
request_limiter = RequestLimiter(
    max_concurrent=MAX_CONCURRENT_REQUESTS,
    max_queue_size=MAX_QUEUE_SIZE,
    request_timeout=REQUEST_TIMEOUT
)

# Track active requests for graceful shutdown
active_requests = 0
active_requests_lock = threading.Lock()

# Global flag for graceful shutdown
is_shutting_down = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting Image Quality Assessment API with {MAX_WORKERS} workers")
    logger.info(f"Configured for max {MAX_CONCURRENT_REQUESTS} concurrent requests with queue size {MAX_QUEUE_SIZE}")
    app.state.event_loop = asyncio.get_event_loop()
    
    # Setup signal handlers for graceful shutdown
    def handle_shutdown_signal(signum, frame):
        global is_shutting_down
        if not is_shutting_down:
            is_shutting_down = True
            logger.info(f"Received shutdown signal {signum}. Starting graceful shutdown...")
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Image Quality Assessment API")
    logger.info(f"Waiting for {active_requests} active requests to complete...")
    
    # Wait for active requests to complete (with timeout)
    shutdown_start = time.time()
    while active_requests > 0:
        if time.time() - shutdown_start > 30:  # 30 second timeout
            logger.warning(f"Shutdown timeout reached with {active_requests} requests still active")
            break
        await asyncio.sleep(0.1)
    
    # Shutdown thread pool
    executor.shutdown(wait=False)
    logger.info("Shutdown complete")

# Initialize FastAPI app
app = FastAPI(
    title="Image Quality Assessment API",
    description="API for assessing image quality using BRISQUE score",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware for request timing, logging, and rate limiting
# Исправленная часть middleware в app.py
@app.middleware("http")
async def middleware(request: Request, call_next):
    global active_requests, is_shutting_down
    
    # Check if server is shutting down
    if is_shutting_down:
        return JSONResponse(
            status_code=503,
            content={"error": "Server is shutting down. Please try again later."}
        )
    
    # Track request start time
    start_time = time.time()
    
    # Increment active requests counter
    with active_requests_lock:
        active_requests += 1
    
    try:
        # Apply rate limiting and queuing
        try:
            response = await request_limiter.handle_request(request, call_next)
        except HTTPException as e:
            logger.warning(f"Request rejected: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail}
            )
        
        # Add processing time header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request completion
        logger.info(f"Request to {request.url.path} processed in {process_time:.4f}s")
        return response
    
    except Exception as e:
        logger.error(f"Unhandled exception in middleware: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
    finally:
        # Decrement active requests counter
        with active_requests_lock:
            active_requests -= 1

def brisque_score(image_path, downscale_factor=1.0):
    """
    Calculate the BRISQUE score for an image.
    
    Args:
        image_path: Path to the image file
        downscale_factor: Factor to downscale image before processing (1.0 = no downscaling)
    """
    try:
        # Check if server is shutting down
        if is_shutting_down:
            return {"error": "Server is shutting down", "status": "error"}
        
        # Check if file exists
        if not os.path.isfile(image_path):
            logger.error(f"File not found: {image_path}")
            return {"error": "File not found", "status": "error"}
        
        # Check file size
        try:
            file_size = os.path.getsize(image_path)
            if file_size > 20 * 1024 * 1024:  # 20MB limit
                logger.error(f"File too large: {image_path} ({file_size / (1024*1024):.2f} MB)")
                return {"error": "File too large (max 20MB)", "status": "error"}
        except Exception as e:
            logger.error(f"Error checking file size: {str(e)}")
        
        # Read image with timeout protection
        start_time = time.time()
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        if image is None:
            logger.error(f"Failed to read image: {image_path}")
            return {"error": "Failed to read image", "status": "error"}
        
        # Downscale image if needed to improve performance
        if downscale_factor < 1.0:
            new_width = int(image.shape[1] * downscale_factor)
            new_height = int(image.shape[0] * downscale_factor)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Process image with resource usage protection
        try:
            # Apply timeout for processing
            if time.time() - start_time > 25:  # 25 second timeout
                logger.error(f"Processing timeout for {image_path}")
                return {"error": "Processing timeout", "status": "error"}
            
            image = img_as_ubyte(gaussian(image, sigma=1.5))
            features = mahotas.features.haralick(image).mean(axis=0)
            
            return {"score": float(np.mean(features)), "status": "success"}
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return {"error": str(e), "status": "error"}
    except Exception as e:
        logger.error(f"Unhandled exception in brisque_score: {str(e)}")
        return {"error": "Internal processing error", "status": "error"}

@app.post("/score-from-file", response_class=JSONResponse)
async def score_from_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    downscale: Optional[float] = Form(1.0)
):
    """
    Assess image quality from an uploaded file.
    
    Returns a quality score - lower values indicate worse quality.
    """
    # Validate downscale factor
    downscale = max(0.1, min(1.0, float(downscale)))
    
    logger.info(f"Processing file upload: {file.filename} (downscale={downscale})")
    
    # Check if server is shutting down
    if is_shutting_down:
        raise HTTPException(
            status_code=503,
            detail="Server is shutting down. Please try again later."
        )
    
    # Save the uploaded file temporarily
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(await file.read())
            temp_path = temp.name
        
        # Calculate the score
        start_time = time.time()
        result = await app.state.event_loop.run_in_executor(
            executor, 
            lambda: brisque_score(temp_path, downscale)
        )
        processing_time = time.time() - start_time
        
        if result["status"] == "success":
            logger.info(f"Processed {file.filename} in {processing_time:.4f}s with score {result['score']:.2f}")
            
            # Schedule temp file cleanup
            if background_tasks:
                background_tasks.add_task(cleanup_temp_file, temp_path)
            
            return {"filename": file.filename, "score": round(result["score"], 2)}
        else:
            logger.error(f"Error processing {file.filename}: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=400, detail=result.get("error", "Error processing image"))
    except Exception as e:
        logger.error(f"Error processing {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file if not handled by background task
        if temp_path and not background_tasks:
            cleanup_temp_file(temp_path)

def cleanup_temp_file(file_path):
    """Clean up a temporary file with error handling."""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.warning(f"Failed to delete temp file {file_path}: {str(e)}")

@app.post("/score-from-path", response_class=JSONResponse)
async def score_from_path(
    image_path: str = Form(...),
    downscale: Optional[float] = Form(1.0)
):
    """
    Assess image quality from a file path.
    
    Returns a quality score - lower values indicate worse quality.
    """
    # Validate downscale factor
    downscale = max(0.1, min(1.0, float(downscale)))
    
    logger.info(f"Processing image from path: {image_path} (downscale={downscale})")
    
    # Check if server is shutting down
    if is_shutting_down:
        raise HTTPException(
            status_code=503,
            detail="Server is shutting down. Please try again later."
        )
    
    try:
        # Calculate the score
        start_time = time.time()
        result = await app.state.event_loop.run_in_executor(
            executor, 
            lambda: brisque_score(image_path, downscale)
        )
        processing_time = time.time() - start_time
        
        if result["status"] == "success":
            logger.info(f"Processed {image_path} in {processing_time:.4f}s with score {result['score']:.2f}")
            return {"filename": os.path.basename(image_path), "score": round(result["score"], 2)}
        else:
            logger.error(f"Error processing {image_path}: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=400, detail=result.get("error", "Error processing image"))
    except Exception as e:
        logger.error(f"Error processing {image_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint with system status."""
    return {
        "status": "healthy" if not is_shutting_down else "shutting_down",
        "timestamp": time.time(),
        "active_requests": active_requests,
        "queue_size": request_limiter.queue_size,
        "max_workers": MAX_WORKERS,
        "max_concurrent_requests": MAX_CONCURRENT_REQUESTS
    }

@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Image Quality Assessment API",
        "version": "1.0.0",
        "endpoints": {
            "/score-from-file": "Upload an image file to get quality score",
            "/score-from-path": "Provide a path to an image file to get quality score",
            "/health": "Health check endpoint"
        },
        "status": "available" if not is_shutting_down else "shutting_down"
    }

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", str(max(1, cpu_count))))
    
    # For production, use multiple workers without reload
    uvicorn.run(
        "app:app", 
        host=host, 
        port=port, 
        workers=workers,
        reload=False
    )