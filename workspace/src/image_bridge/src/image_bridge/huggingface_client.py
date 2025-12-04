"""
Hugging Face API client for AI model inference.
"""

import requests
import json
import time
from queue import Queue, Empty
from threading import Thread, Lock
import rospy


class HuggingFaceClient:
    """
    Client for interacting with Hugging Face Inference API.
    Supports asynchronous requests with a queue system.
    """
    
    def __init__(self, api_url, api_token, request_timeout=30.0):
        """
        Initialize Hugging Face API client.
        
        Args:
            api_url (str): Base URL for Hugging Face API.
            api_token (str): API authentication token.
            request_timeout (float): Request timeout in seconds.
        """
        self.api_url = api_url
        self.api_token = api_token
        self.request_timeout = request_timeout
        
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Request queue and worker thread
        self.request_queue = Queue()
        self.response_dict = {}
        self.response_lock = Lock()
        self.request_counter = 0
        self.request_counter_lock = Lock()
        
        # Start worker thread
        self.worker_thread = Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
        rospy.loginfo("HuggingFace client initialized")
    
    def _get_next_request_id(self):
        """Generate unique request ID."""
        with self.request_counter_lock:
            self.request_counter += 1
            return f"req_{self.request_counter}_{int(time.time())}"
    
    def _worker(self):
        """Worker thread to process requests from queue."""
        while True:
            try:
                request_data = self.request_queue.get(timeout=1.0)
                if request_data is None:
                    break
                
                request_id = request_data['id']
                model_id = request_data['model_id']
                payload = request_data['payload']
                
                rospy.logdebug(f"Processing request {request_id} for model {model_id}")
                
                try:
                    response = self._make_request(model_id, payload)
                    with self.response_lock:
                        self.response_dict[request_id] = {
                            'success': True,
                            'data': response,
                            'timestamp': time.time()
                        }
                except Exception as e:
                    rospy.logerr(f"Request {request_id} failed: {e}")
                    with self.response_lock:
                        self.response_dict[request_id] = {
                            'success': False,
                            'error': str(e),
                            'timestamp': time.time()
                        }
                
                self.request_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                rospy.logerr(f"Worker thread error: {e}")
    
    def _make_request(self, model_id, payload):
        """
        Make HTTP request to Hugging Face API.
        
        Args:
            model_id (str): Model identifier.
            payload (dict): Request payload.
        
        Returns:
            dict or bytes: API response.
        """
        url = f"{self.api_url}/models/{model_id}"
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.request_timeout
            )
            
            response.raise_for_status()
            
            # Check if response is JSON or binary
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return response.json()
            else:
                return response.content
                
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout after {self.request_timeout}s")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def query_async(self, model_id, payload):
        """
        Queue an asynchronous request.
        
        Args:
            model_id (str): Model identifier.
            payload (dict): Request payload.
        
        Returns:
            str: Request ID for tracking.
        """
        request_id = self._get_next_request_id()
        request_data = {
            'id': request_id,
            'model_id': model_id,
            'payload': payload
        }
        self.request_queue.put(request_data)
        rospy.logdebug(f"Queued async request {request_id}")
        return request_id
    
    def get_response(self, request_id, timeout=None):
        """
        Get response for a request ID.
        
        Args:
            request_id (str): Request ID.
            timeout (float): Maximum time to wait for response.
        
        Returns:
            dict: Response data with 'success', 'data' or 'error'.
        """
        from threading import Event
        
        start_time = time.time()
        check_interval = 0.1  # Check every 100ms
        
        while True:
            with self.response_lock:
                if request_id in self.response_dict:
                    response = self.response_dict.pop(request_id)
                    return response
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                return {
                    'success': False,
                    'error': 'Response timeout'
                }
            
            # Sleep to avoid busy waiting
            time.sleep(check_interval)
    
    def query_sync(self, model_id, payload):
        """
        Make synchronous request (blocking).
        
        Args:
            model_id (str): Model identifier.
            payload (dict): Request payload.
        
        Returns:
            dict: Response with 'success' and 'data' or 'error'.
        """
        try:
            data = self._make_request(model_id, payload)
            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def image_to_text(self, model_id, image_base64):
        """
        Generate text caption from image.
        
        Args:
            model_id (str): Captioning model ID.
            image_base64 (str): Base64 encoded image.
        
        Returns:
            dict: Response with generated text.
        """
        payload = {
            "inputs": image_base64
        }
        return self.query_sync(model_id, payload)
    
    def text_to_image(self, model_id, prompt, **kwargs):
        """
        Generate image from text prompt.
        
        Args:
            model_id (str): Diffusion model ID.
            prompt (str): Text prompt.
            **kwargs: Additional parameters (guidance_scale, num_inference_steps, etc.).
                     Note: 'inputs' key will be overwritten by the prompt.
        
        Returns:
            dict: Response with generated image data.
        """
        payload = {
            "inputs": prompt
        }
        # Merge kwargs, ensuring 'inputs' is not overwritten
        for key, value in kwargs.items():
            if key != 'inputs':
                payload[key] = value
        return self.query_sync(model_id, payload)
    
    def segment_image(self, model_id, image_base64):
        """
        Perform image segmentation.
        
        Args:
            model_id (str): Segmentation model ID.
            image_base64 (str): Base64 encoded image.
        
        Returns:
            dict: Response with segmentation masks.
        """
        payload = {
            "inputs": image_base64
        }
        return self.query_sync(model_id, payload)
    
    def classify_image(self, model_id, image_base64):
        """
        Classify image using CLIP or similar model.
        
        Args:
            model_id (str): Classification model ID.
            image_base64 (str): Base64 encoded image.
        
        Returns:
            dict: Response with classification results.
        """
        payload = {
            "inputs": image_base64
        }
        return self.query_sync(model_id, payload)
    
    def shutdown(self):
        """Shutdown the client and worker thread."""
        self.request_queue.put(None)
        self.worker_thread.join(timeout=5.0)
        rospy.loginfo("HuggingFace client shutdown")
