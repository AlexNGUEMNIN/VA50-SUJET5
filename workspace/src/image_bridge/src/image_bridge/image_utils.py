"""
Image utilities for format conversion and processing.
"""

import base64
import io
import numpy as np
import cv2
from PIL import Image as PILImage
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
import rospy


class ImageUtils:
    """
    Utility class for image format conversions.
    Handles conversions between: ROS Image messages, OpenCV arrays, PIL Images, and base64 strings.
    """
    
    def __init__(self):
        """Initialize the image utilities with cv_bridge."""
        self.bridge = CvBridge()
    
    def ros_to_cv2(self, ros_image, encoding='bgr8'):
        """
        Convert ROS Image message to OpenCV image.
        
        Args:
            ros_image (sensor_msgs/Image): ROS image message.
            encoding (str): Desired encoding (default: 'bgr8').
        
        Returns:
            numpy.ndarray: OpenCV image array, or None if conversion fails.
        """
        try:
            cv_image = self.bridge.imgmsg_to_cv2(ros_image, encoding)
            return cv_image
        except CvBridgeError as e:
            rospy.logerr(f"CvBridge Error: {e}")
            return None
    
    def cv2_to_ros(self, cv_image, encoding='bgr8'):
        """
        Convert OpenCV image to ROS Image message.
        
        Args:
            cv_image (numpy.ndarray): OpenCV image array.
            encoding (str): Encoding type (default: 'bgr8').
        
        Returns:
            sensor_msgs/Image: ROS image message, or None if conversion fails.
        """
        try:
            ros_image = self.bridge.cv2_to_imgmsg(cv_image, encoding)
            return ros_image
        except CvBridgeError as e:
            rospy.logerr(f"CvBridge Error: {e}")
            return None
    
    def cv2_to_base64(self, cv_image, format='JPEG'):
        """
        Convert OpenCV image to base64 encoded string.
        
        Args:
            cv_image (numpy.ndarray): OpenCV image array.
            format (str): Image format for encoding (JPEG, PNG, etc.).
        
        Returns:
            str: Base64 encoded image string, or None if conversion fails.
        """
        try:
            # Determine if color conversion is needed
            # OpenCV uses BGR by default, PIL uses RGB
            if len(cv_image.shape) == 3 and cv_image.shape[2] == 3:
                # Assume BGR for 3-channel images from OpenCV
                rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            elif len(cv_image.shape) == 3 and cv_image.shape[2] == 4:
                # Handle BGRA images
                rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGRA2RGBA)
            else:
                # Grayscale or other formats - use as is
                rgb_image = cv_image
            
            # Convert to PIL Image
            pil_image = PILImage.fromarray(rgb_image)
            
            # Encode to base64
            buffer = io.BytesIO()
            pil_image.save(buffer, format=format)
            img_bytes = buffer.getvalue()
            base64_str = base64.b64encode(img_bytes).decode('utf-8')
            
            return base64_str
        except Exception as e:
            rospy.logerr(f"Error converting to base64: {e}")
            return None
    
    def base64_to_cv2(self, base64_str):
        """
        Convert base64 encoded string to OpenCV image.
        
        Args:
            base64_str (str): Base64 encoded image string.
        
        Returns:
            numpy.ndarray: OpenCV image array, or None if conversion fails.
        """
        try:
            # Decode base64
            img_bytes = base64.b64decode(base64_str)
            
            # Convert to PIL Image
            buffer = io.BytesIO(img_bytes)
            pil_image = PILImage.open(buffer)
            
            # Convert to numpy array
            np_image = np.array(pil_image)
            
            # Convert RGB to BGR for OpenCV
            if len(np_image.shape) == 3 and np_image.shape[2] == 3:
                cv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
            else:
                cv_image = np_image
            
            return cv_image
        except Exception as e:
            rospy.logerr(f"Error converting from base64: {e}")
            return None
    
    def ros_to_base64(self, ros_image, format='JPEG'):
        """
        Convert ROS Image message directly to base64 string.
        
        Args:
            ros_image (sensor_msgs/Image): ROS image message.
            format (str): Image format for encoding.
        
        Returns:
            str: Base64 encoded image string, or None if conversion fails.
        """
        cv_image = self.ros_to_cv2(ros_image)
        if cv_image is not None:
            return self.cv2_to_base64(cv_image, format)
        return None
    
    def base64_to_ros(self, base64_str, encoding='bgr8'):
        """
        Convert base64 string directly to ROS Image message.
        
        Args:
            base64_str (str): Base64 encoded image string.
            encoding (str): ROS image encoding.
        
        Returns:
            sensor_msgs/Image: ROS image message, or None if conversion fails.
        """
        cv_image = self.base64_to_cv2(base64_str)
        if cv_image is not None:
            return self.cv2_to_ros(cv_image, encoding)
        return None
    
    def resize_image(self, cv_image, max_size=640):
        """
        Resize image while maintaining aspect ratio.
        
        Args:
            cv_image (numpy.ndarray): OpenCV image array.
            max_size (int): Maximum dimension size.
        
        Returns:
            numpy.ndarray: Resized image.
        """
        height, width = cv_image.shape[:2]
        
        if height <= max_size and width <= max_size:
            return cv_image
        
        # Calculate scaling factor
        scale = max_size / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        resized = cv2.resize(cv_image, (new_width, new_height), 
                            interpolation=cv2.INTER_AREA)
        return resized
    
    def save_debug_image(self, cv_image, filename, path):
        """
        Save image for debugging purposes.
        
        Args:
            cv_image (numpy.ndarray): OpenCV image array.
            filename (str): Filename to save.
            path (str): Directory path.
        
        Returns:
            bool: True if saved successfully.
        """
        try:
            import os
            from datetime import datetime
            
            os.makedirs(path, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_path = os.path.join(path, f"{timestamp}_{filename}")
            cv2.imwrite(full_path, cv_image)
            rospy.logdebug(f"Debug image saved: {full_path}")
            return True
        except Exception as e:
            rospy.logerr(f"Error saving debug image: {e}")
            return False
