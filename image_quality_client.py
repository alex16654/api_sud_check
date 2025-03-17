"""
Client script for the Image Quality Assessment API with resilience features.
"""

import os
import sys
import time
import json
import random
from typing import Dict, List, Optional, Union, Any
import requests
from requests.exceptions import RequestException, Timeout
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class ImageQualityClient:
    """Client for the Image Quality Assessment API with retry and backoff."""
    
    def __init__(
        self, 
        base_url: str, 
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        jitter: float = 0.1
    ):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the API (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff factor
            jitter: Random jitter factor to add to backoff
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        
    def _retry_request(self, request_func, *args, **kwargs):
        """
        Execute a request with retry logic.
        
        Args:
            request_func: Function to execute (e.g., requests.get)
            *args, **kwargs: Arguments to pass to the function
        
        Returns:
            Response object
        
        Raises:
            ConnectionError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = request_func(*args, **kwargs)
                
                # Check for server overload (503)
                if response.status_code == 503:
                    retry_after = int(response.headers.get('Retry-After', 1))
                    wait_time = retry_after + random.uniform(0, self.jitter)
                    print(f"Server overloaded. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                
                return response
            except (RequestException, Timeout) as e:
                last_exception = e
                
                # Calculate backoff time
                wait_time = (self.backoff_factor ** attempt) + random.uniform(0, self.jitter)
                
                if attempt < self.max_retries - 1:
                    print(f"Request failed: {str(e)}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
        
        raise ConnectionError(f"Failed after {self.max_retries} attempts: {str(last_exception)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the API is healthy.
        
        Returns:
            Dict with status information
        
        Raises:
            ConnectionError: If the API is not reachable
        """
        try:
            response = self._retry_request(
                requests.get,
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise ConnectionError(f"Failed to connect to API: {str(e)}")
    
    def score_from_path(self, image_path: str, downscale: float = 1.0) -> Dict[str, Any]:
        """
        Get image quality score from a file path.
        
        Args:
            image_path: Path to the image file
            downscale: Factor to downscale image (1.0 = no downscaling)
        
        Returns:
            Dict with filename and score
        
        Raises:
            FileNotFoundError: If the image file doesn't exist
            ValueError: If the API returns an error
            ConnectionError: If the API is not reachable
        """
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            response = self._retry_request(
                requests.post,
                f"{self.base_url}/score-from-path",
                data={"image_path": image_path, "downscale": downscale},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get('detail', 'Unknown error')
                raise ValueError(f"API error: {error_msg}")
                
        except RequestException as e:
            raise ConnectionError(f"Failed to connect to API: {str(e)}")
    
    def score_from_file(self, file_path: str, downscale: float = 1.0) -> Dict[str, Any]:
        """
        Upload an image file and get its quality score.
        
        Args:
            file_path: Path to the image file to upload
            downscale: Factor to downscale image (1.0 = no downscaling)
        
        Returns:
            Dict with filename and score
        
        Raises:
            FileNotFoundError: If the image file doesn't exist
            ValueError: If the API returns an error
            ConnectionError: If the API is not reachable
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'image/jpeg')}
                data = {'downscale': str(downscale)}
                
                response = self._retry_request(
                    requests.post,
                    f"{self.base_url}/score-from-file",
                    files=files,
                    data=data,
                    timeout=self.timeout
                )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get('detail', 'Unknown error')
                raise ValueError(f"API error: {error_msg}")
                
        except RequestException as e:
            raise ConnectionError(f"Failed to connect to API: {str(e)}")
    
    def process_directory(
        self, 
        directory: str, 
        use_upload: bool = False, 
        max_workers: int = 5,
        extensions: List[str] = ['.jpg', '.jpeg', '.png'],
        downscale: float = 1.0,
        max_retries_per_file: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Process all images in a directory with resilience.
        
        Args:
            directory: Path to directory containing images
            use_upload: If True, upload files; if False, use path
            max_workers: Maximum number of concurrent workers
            extensions: List of file extensions to process
            downscale: Factor to downscale images
            max_retries_per_file: Maximum retries per file
        
        Returns:
            List of dicts with filename and score
        
        Raises:
            NotADirectoryError: If the directory doesn't exist
        """
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"Directory not found: {directory}")
        
        # Get list of image files
        image_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            print(f"No image files found in {directory}")
            return []
        
        print(f"Processing {len(image_files)} images...")
        
        # Process images in parallel with resilience
        results = []
        errors = []
        
        # Create a function to process a single file with retries
        def process_file_with_retries(file_path):
            for retry in range(max_retries_per_file):
                try:
                    if use_upload:
                        return self.score_from_file(file_path, downscale)
                    else:
                        return self.score_from_path(file_path, downscale)
                except (ConnectionError, ValueError) as e:
                    if retry < max_retries_per_file - 1:
                        # Add jitter to prevent thundering herd
                        wait_time = (2 ** retry) + random.uniform(0, 0.5)
                        time.sleep(wait_time)
                    else:
                        return {"filename": os.path.basename(file_path), "error": str(e)}
                except Exception as e:
                    return {"filename": os.path.basename(file_path), "error": str(e)}
            
            return {"filename": os.path.basename(file_path), "error": "Max retries exceeded"}
        
        # Process files with adaptive concurrency
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_file_with_retries, f): f for f in image_files}
            
            for future in tqdm(futures, total=len(image_files)):
                result = future.result()
                if "error" in result:
                    errors.append(result)
                else:
                    results.append(result)
        
        # Report errors
        if errors:
            print(f"\nEncountered {len(errors)} errors:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  {error['filename']}: {error.get('error', 'Unknown error')}")
            
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")
        
        return results + errors
