"""
Configuration management for image_bridge node.
"""

import os
import rospy


class Config:
    """
    Configuration class for image_bridge node.
    Handles parameter loading from ROS parameter server and environment variables.
    """
    
    def __init__(self):
        """Initialize configuration from ROS parameters and environment variables."""
        
        # Hugging Face API Configuration
        self.hf_api_url = rospy.get_param(
            '~huggingface/api_url', 
            'https://api-inference.huggingface.co'
        )
        
        # Get API token from environment variable (secure)
        self.hf_api_token = os.getenv('HUGGINGFACE_API_TOKEN', '')
        if not self.hf_api_token:
            rospy.logwarn("HUGGINGFACE_API_TOKEN not set in environment variables")
        
        # Model endpoints
        self.model_clip = rospy.get_param(
            '~models/clip', 
            'openai/clip-vit-base-patch32'
        )
        self.model_mask_rcnn = rospy.get_param(
            '~models/mask_rcnn', 
            'facebook/maskformer-swin-base-coco'
        )
        self.model_diffusion = rospy.get_param(
            '~models/diffusion', 
            'stabilityai/stable-diffusion-2-1'
        )
        self.model_captioning = rospy.get_param(
            '~models/captioning',
            'Salesforce/blip-image-captioning-base'
        )
        
        # ROS Topics
        self.topic_rgb_input = rospy.get_param(
            '~topics/rgb_input', 
            '/xtion/rgb/image_raw'
        )
        self.topic_depth_input = rospy.get_param(
            '~topics/depth_input', 
            '/xtion/depth/image_raw'
        )
        self.topic_ai_generated = rospy.get_param(
            '~topics/ai_generated', 
            '/ai_model/generated_image'
        )
        self.topic_to_ai = rospy.get_param(
            '~topics/to_ai_model', 
            '/image_bridge/to_ai_model'
        )
        self.topic_to_robot = rospy.get_param(
            '~topics/to_robot', 
            '/image_bridge/to_robot'
        )
        self.topic_segmentation = rospy.get_param(
            '~topics/segmentation_masks', 
            '/image_bridge/segmentation_masks'
        )
        self.topic_status = rospy.get_param(
            '~topics/status', 
            '/image_bridge/status'
        )
        
        # Buffer and timing configuration
        self.buffer_size = rospy.get_param('~buffer_size', 10)
        self.publish_rate = rospy.get_param('~publish_rate', 10.0)  # Hz
        self.request_timeout = rospy.get_param('~request_timeout', 30.0)  # seconds
        
        # Image processing
        self.image_encoding = rospy.get_param('~image_encoding', 'bgr8')
        self.image_max_size = rospy.get_param('~image_max_size', 640)  # pixels
        
        # Logging
        self.save_debug_images = rospy.get_param('~save_debug_images', False)
        self.debug_image_path = rospy.get_param(
            '~debug_image_path', 
            os.path.expanduser('~/ros_ws/data/bridge_debug')
        )
        
        if self.save_debug_images:
            os.makedirs(self.debug_image_path, exist_ok=True)
        
        rospy.loginfo("Configuration loaded successfully")
    
    def validate(self):
        """
        Validate configuration parameters.
        
        Returns:
            bool: True if configuration is valid, False otherwise.
        """
        if not self.hf_api_token:
            rospy.logerr("Hugging Face API token is not configured")
            return False
        
        if self.buffer_size < 1:
            rospy.logerr("Buffer size must be at least 1")
            return False
        
        if self.publish_rate <= 0:
            rospy.logerr("Publish rate must be positive")
            return False
        
        return True
    
    def log_config(self):
        """Log current configuration (without sensitive data)."""
        rospy.loginfo("=== Image Bridge Configuration ===")
        rospy.loginfo(f"API URL: {self.hf_api_url}")
        rospy.loginfo(f"API Token: {'*' * 10 if self.hf_api_token else 'NOT SET'}")
        rospy.loginfo(f"RGB Topic: {self.topic_rgb_input}")
        rospy.loginfo(f"Depth Topic: {self.topic_depth_input}")
        rospy.loginfo(f"Buffer Size: {self.buffer_size}")
        rospy.loginfo(f"Publish Rate: {self.publish_rate} Hz")
        rospy.loginfo("==================================")
