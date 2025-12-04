"""
ROS interface for managing publishers, subscribers, and services.
"""

import rospy
import cv2
import numpy as np
from PIL import Image as PILImage
from collections import deque
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseArray
from std_msgs.msg import Header
from image_bridge.msg import BridgeStatus
from image_bridge.srv import CaptureScene, CaptureSceneResponse
from image_bridge.srv import RequestGeneration, RequestGenerationResponse
from image_bridge.srv import GetTargetPoses, GetTargetPosesResponse


class ROSInterface:
    """
    ROS interface manager for image_bridge node.
    Handles all ROS communication including topics and services.
    """
    
    def __init__(self, config, image_utils, hf_client):
        """
        Initialize ROS interface.
        
        Args:
            config (Config): Configuration object.
            image_utils (ImageUtils): Image utilities object.
            hf_client (HuggingFaceClient): Hugging Face client object.
        """
        self.config = config
        self.image_utils = image_utils
        self.hf_client = hf_client
        
        # Image buffers (circular buffers)
        self.rgb_buffer = deque(maxlen=config.buffer_size)
        self.depth_buffer = deque(maxlen=config.buffer_size)
        
        # Latest images
        self.latest_rgb = None
        self.latest_depth = None
        self.latest_ai_generated = None
        
        # Statistics
        self.total_images_processed = 0
        self.current_status = "idle"
        self.current_operation = ""
        self.last_error = ""
        
        # Initialize subscribers
        self._init_subscribers()
        
        # Initialize publishers
        self._init_publishers()
        
        # Initialize services
        self._init_services()
        
        # Status publisher timer
        self.status_timer = rospy.Timer(
            rospy.Duration(1.0 / config.publish_rate),
            self._publish_status
        )
        
        rospy.loginfo("ROS Interface initialized")
    
    def _init_subscribers(self):
        """Initialize ROS subscribers."""
        self.rgb_sub = rospy.Subscriber(
            self.config.topic_rgb_input,
            Image,
            self._rgb_callback,
            queue_size=1
        )
        
        self.depth_sub = rospy.Subscriber(
            self.config.topic_depth_input,
            Image,
            self._depth_callback,
            queue_size=1
        )
        
        self.ai_generated_sub = rospy.Subscriber(
            self.config.topic_ai_generated,
            Image,
            self._ai_generated_callback,
            queue_size=1
        )
        
        rospy.loginfo("Subscribers initialized")
    
    def _init_publishers(self):
        """Initialize ROS publishers."""
        self.to_ai_pub = rospy.Publisher(
            self.config.topic_to_ai,
            Image,
            queue_size=10
        )
        
        self.to_robot_pub = rospy.Publisher(
            self.config.topic_to_robot,
            Image,
            queue_size=10
        )
        
        self.segmentation_pub = rospy.Publisher(
            self.config.topic_segmentation,
            Image,
            queue_size=10
        )
        
        self.status_pub = rospy.Publisher(
            self.config.topic_status,
            BridgeStatus,
            queue_size=10
        )
        
        rospy.loginfo("Publishers initialized")
    
    def _init_services(self):
        """Initialize ROS services."""
        self.capture_service = rospy.Service(
            '/image_bridge/capture_scene',
            CaptureScene,
            self._handle_capture_scene
        )
        
        self.generation_service = rospy.Service(
            '/image_bridge/request_generation',
            RequestGeneration,
            self._handle_request_generation
        )
        
        self.poses_service = rospy.Service(
            '/image_bridge/get_target_poses',
            GetTargetPoses,
            self._handle_get_target_poses
        )
        
        rospy.loginfo("Services initialized")
    
    def _rgb_callback(self, msg):
        """
        Callback for RGB image topic.
        
        Args:
            msg (sensor_msgs/Image): RGB image message.
        """
        self.latest_rgb = msg
        self.rgb_buffer.append(msg)
        self.total_images_processed += 1
        
        if self.config.save_debug_images:
            cv_image = self.image_utils.ros_to_cv2(msg)
            if cv_image is not None:
                self.image_utils.save_debug_image(
                    cv_image, 
                    "rgb.jpg", 
                    self.config.debug_image_path
                )
    
    def _depth_callback(self, msg):
        """
        Callback for depth image topic.
        
        Args:
            msg (sensor_msgs/Image): Depth image message.
        """
        self.latest_depth = msg
        self.depth_buffer.append(msg)
    
    def _ai_generated_callback(self, msg):
        """
        Callback for AI generated image topic.
        
        Args:
            msg (sensor_msgs/Image): Generated image message.
        """
        self.latest_ai_generated = msg
        
        # Republish to robot
        self.to_robot_pub.publish(msg)
        rospy.loginfo("AI generated image received and forwarded to robot")
    
    def _publish_status(self, event):
        """
        Publish status message periodically.
        
        Args:
            event: Timer event.
        """
        status_msg = BridgeStatus()
        status_msg.header = Header()
        status_msg.header.stamp = rospy.Time.now()
        status_msg.status = self.current_status
        status_msg.operation = self.current_operation
        status_msg.buffer_size = len(self.rgb_buffer)
        status_msg.error_message = self.last_error
        status_msg.total_images_processed = self.total_images_processed
        status_msg.last_operation_duration = 0.0  # Will be updated by operations
        
        self.status_pub.publish(status_msg)
    
    def _handle_capture_scene(self, req):
        """
        Handle CaptureScene service request.
        
        Args:
            req (CaptureSceneRequest): Service request.
        
        Returns:
            CaptureSceneResponse: Service response.
        """
        rospy.loginfo("CaptureScene service called")
        self.current_status = "capturing"
        self.current_operation = "capture_scene"
        
        response = CaptureSceneResponse()
        
        try:
            # Get current images
            if req.capture_rgb and self.latest_rgb is not None:
                response.rgb_image = self.latest_rgb
                # Publish to AI model
                self.to_ai_pub.publish(self.latest_rgb)
            
            if req.capture_depth and self.latest_depth is not None:
                response.depth_image = self.latest_depth
            
            if self.latest_rgb is None and self.latest_depth is None:
                response.success = False
                response.message = "No images available"
                self.last_error = "No images available"
            else:
                response.success = True
                response.message = "Scene captured successfully"
                self.last_error = ""
            
        except Exception as e:
            rospy.logerr(f"Error in capture_scene: {e}")
            response.success = False
            response.message = str(e)
            self.last_error = str(e)
        
        self.current_status = "idle"
        self.current_operation = ""
        return response
    
    def _handle_request_generation(self, req):
        """
        Handle RequestGeneration service request.
        
        Args:
            req (RequestGenerationRequest): Service request.
        
        Returns:
            RequestGenerationResponse: Service response.
        """
        rospy.loginfo(f"RequestGeneration service called with prompt: {req.prompt}")
        self.current_status = "processing"
        self.current_operation = "request_generation"
        
        response = RequestGenerationResponse()
        
        try:
            import time
            start_time = time.time()
            
            # Prepare parameters
            params = {}
            if req.guidance_scale > 0:
                params['guidance_scale'] = req.guidance_scale
            if req.num_inference_steps > 0:
                params['num_inference_steps'] = req.num_inference_steps
            
            # Call Hugging Face API
            model_id = req.model_name if req.model_name else self.config.model_diffusion
            result = self.hf_client.text_to_image(model_id, req.prompt, **params)
            
            if result['success']:
                # Convert response to ROS image
                if isinstance(result['data'], bytes):
                    # Binary image data - convert directly
                    try:
                        import io
                        buffer = io.BytesIO(result['data'])
                        pil_image = PILImage.open(buffer)
                        np_image = np.array(pil_image)
                        
                        # Convert RGB to BGR for OpenCV
                        if len(np_image.shape) == 3 and np_image.shape[2] == 3:
                            cv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
                        else:
                            cv_image = np_image
                        
                        ros_image = self.image_utils.cv2_to_ros(cv_image)
                        
                        if ros_image is not None:
                            response.generated_image = ros_image
                            response.success = True
                            response.message = "Image generated successfully"
                            response.inference_time = time.time() - start_time
                            response.generation_id = f"gen_{int(time.time())}"
                            
                            # Publish generated image
                            self.to_robot_pub.publish(ros_image)
                            self.last_error = ""
                        else:
                            response.success = False
                            response.message = "Failed to convert generated image"
                            self.last_error = "Image conversion failed"
                    except Exception as conv_err:
                        rospy.logerr(f"Error converting image: {conv_err}")
                        response.success = False
                        response.message = f"Image conversion error: {conv_err}"
                        self.last_error = str(conv_err)
                else:
                    response.success = False
                    response.message = "Unexpected response format"
                    self.last_error = "Unexpected response format"
            else:
                response.success = False
                response.message = result.get('error', 'Unknown error')
                self.last_error = result.get('error', 'Unknown error')
                
        except Exception as e:
            rospy.logerr(f"Error in request_generation: {e}")
            response.success = False
            response.message = str(e)
            self.last_error = str(e)
        
        self.current_status = "idle"
        self.current_operation = ""
        return response
    
    def _handle_get_target_poses(self, req):
        """
        Handle GetTargetPoses service request.
        
        Args:
            req (GetTargetPosesRequest): Service request.
        
        Returns:
            GetTargetPosesResponse: Service response.
        """
        rospy.loginfo("GetTargetPoses service called")
        self.current_status = "processing"
        self.current_operation = "get_target_poses"
        
        response = GetTargetPosesResponse()
        
        try:
            # Convert images to base64
            current_base64 = self.image_utils.ros_to_base64(req.current_image)
            target_base64 = self.image_utils.ros_to_base64(req.target_image)
            
            if current_base64 is None or target_base64 is None:
                response.success = False
                response.message = "Failed to process input images"
                self.last_error = "Image processing failed"
                return response
            
            # Use segmentation model
            seg_result = self.hf_client.segment_image(
                self.config.model_mask_rcnn,
                current_base64
            )
            
            if seg_result['success']:
                # Process segmentation results
                # Note: Full pose estimation requires additional computer vision processing
                # (e.g., 3D matching, depth processing) that would be implemented based on
                # specific requirements. This provides the segmentation foundation.
                response.success = True
                response.message = "Segmentation completed - pose estimation requires additional CV processing"
                response.target_poses = PoseArray()
                response.target_poses.header.stamp = rospy.Time.now()
                response.target_poses.header.frame_id = "base_link"
                response.object_ids = []
                response.confidence_scores = []
                self.last_error = ""
                
                rospy.loginfo("Segmentation completed. Full pose estimation requires domain-specific CV logic.")
                rospy.loginfo("Developers should extend this service with object matching and 3D pose computation.")
            else:
                response.success = False
                response.message = seg_result.get('error', 'Segmentation failed')
                self.last_error = seg_result.get('error', 'Segmentation failed')
                
        except Exception as e:
            rospy.logerr(f"Error in get_target_poses: {e}")
            response.success = False
            response.message = str(e)
            self.last_error = str(e)
        
        self.current_status = "idle"
        self.current_operation = ""
        return response
    
    def shutdown(self):
        """Shutdown ROS interface."""
        if self.status_timer:
            self.status_timer.shutdown()
        rospy.loginfo("ROS Interface shutdown")
