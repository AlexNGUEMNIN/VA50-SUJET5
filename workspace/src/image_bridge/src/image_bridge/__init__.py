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
"""

__version__ = "1.0.0"
__author__ = "Alex NGUEMNIN"

from .config import Config
from .image_utils import ImageUtils
from .huggingface_client import HuggingFaceClient
from .ros_interface import ROSInterface

__all__ = ['Config', 'ImageUtils', 'HuggingFaceClient', 'ROSInterface']
