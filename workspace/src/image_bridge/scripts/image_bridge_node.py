#!/usr/bin/env python3
"""
Image Bridge Node - Main entry point.

ROS node that serves as middleware communication between Tiago robot 
(Gazebo simulation) and Hugging Face AI models for autonomous object rearrangement.
"""

import rospy
import signal
import sys
from image_bridge.config import Config
from image_bridge.image_utils import ImageUtils
from image_bridge.huggingface_client import HuggingFaceClient
from image_bridge.ros_interface import ROSInterface


class ImageBridgeNode:
    """
    Main node class for image_bridge.
    Coordinates between configuration, utilities, API client, and ROS interface.
    """
    
    def __init__(self):
        """Initialize the image bridge node."""
        rospy.init_node('image_bridge_node', anonymous=False)
        rospy.loginfo("Starting Image Bridge Node...")
        
        # Load configuration
        self.config = Config()
        if not self.config.validate():
            rospy.logfatal("Configuration validation failed")
            sys.exit(1)
        
        self.config.log_config()
        
        # Initialize utilities
        self.image_utils = ImageUtils()
        
        # Initialize Hugging Face client
        self.hf_client = HuggingFaceClient(
            api_url=self.config.hf_api_url,
            api_token=self.config.hf_api_token,
            request_timeout=self.config.request_timeout
        )
        
        # Initialize ROS interface
        self.ros_interface = ROSInterface(
            config=self.config,
            image_utils=self.image_utils,
            hf_client=self.hf_client
        )
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        rospy.loginfo("Image Bridge Node initialized successfully")
        rospy.loginfo("Ready to process images and communicate with AI models")
    
    def _signal_handler(self, sig, frame):
        """
        Handle shutdown signals gracefully.
        
        Args:
            sig: Signal number.
            frame: Current stack frame.
        """
        rospy.loginfo("Shutdown signal received, cleaning up...")
        self.shutdown()
        sys.exit(0)
    
    def run(self):
        """Run the node (blocking)."""
        rospy.loginfo("Image Bridge Node is running...")
        rospy.spin()
    
    def shutdown(self):
        """Shutdown the node and cleanup resources."""
        rospy.loginfo("Shutting down Image Bridge Node...")
        
        if hasattr(self, 'ros_interface'):
            self.ros_interface.shutdown()
        
        if hasattr(self, 'hf_client'):
            self.hf_client.shutdown()
        
        rospy.loginfo("Image Bridge Node shutdown complete")


def main():
    """Main entry point."""
    try:
        node = ImageBridgeNode()
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Image Bridge Node interrupted")
    except Exception as e:
        rospy.logfatal(f"Fatal error in Image Bridge Node: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
