"""
Image Bridge Package
====================

ROS node that serves as middleware communication between Tiago robot 
(Gazebo simulation) and Hugging Face AI models for autonomous object rearrangement.

Modules:
    - config: Configuration management
    - image_utils: Image format conversions and utilities
    - huggingface_client: API client for Hugging Face models
    - ros_interface: ROS publishers, subscribers, and services management
    - local_model_handler: Local model handler for offline inference (can be imported standalone)
"""

__version__ = "1.0.0"
__author__ = "Alex NGUEMNIN"

# Lazy imports to avoid requiring rospy when only using local_model_handler
def __getattr__(name):
    if name == 'Config':
        from .config import Config
        return Config
    elif name == 'ImageUtils':
        from .image_utils import ImageUtils
        return ImageUtils
    elif name == 'HuggingFaceClient':
        from .huggingface_client import HuggingFaceClient
        return HuggingFaceClient
    elif name == 'ROSInterface':
        from .ros_interface import ROSInterface
        return ROSInterface
    elif name == 'LocalModelHandler':
        from .local_model_handler import LocalModelHandler
        return LocalModelHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ['Config', 'ImageUtils', 'HuggingFaceClient', 'ROSInterface', 'LocalModelHandler']
