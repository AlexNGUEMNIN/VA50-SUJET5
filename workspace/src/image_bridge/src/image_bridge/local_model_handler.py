"""
Local Hugging Face model handler for offline inference.
Supports object detection and classification using locally downloaded models.
"""

import os
import torch
import numpy as np
from PIL import Image
from pathlib import Path

# Optional rospy import - only needed when running in ROS context
try:
    import rospy
    HAS_ROSPY = True
except ImportError:
    HAS_ROSPY = False
    # Mock rospy logging functions for standalone use
    class _MockRospy:
        @staticmethod
        def loginfo(msg):
            print(f"[INFO] {msg}")
        @staticmethod
        def logwarn(msg):
            print(f"[WARN] {msg}")
        @staticmethod
        def logerr(msg):
            print(f"[ERROR] {msg}")
        @staticmethod
        def logdebug(msg):
            # Debug logs are silently suppressed in standalone mode
            # to reduce verbosity when not running in ROS context
            pass
    rospy = _MockRospy()


class LocalModelHandler:
    """
    Handler for local Hugging Face models for object detection and classification.
    Designed to work without internet connectivity using pre-downloaded models.
    """
    
    def __init__(self, model_cache_dir=None):
        """
        Initialize local model handler.
        
        Args:
            model_cache_dir (str): Directory where models are cached. 
                                  Defaults to ~/ros_ws/models
        """
        if model_cache_dir is None:
            model_cache_dir = os.path.expanduser('~/ros_ws/models')
        
        self.model_cache_dir = Path(model_cache_dir)
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Model instances
        self.detection_model = None
        self.detection_processor = None
        
        # Device configuration
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        rospy.loginfo(f"Using device: {self.device}")
        
        # Classes d'objets qui nous intéressent (vaisselle et couverts)
        self.target_classes = [
            'fork', 'knife', 'spoon',  # Cutlery / Couverts
            'bowl', 'cup', 'plate', 'dish',  # Dishware / Vaisselle
            'bottle', 'wine glass', 'dining table'  # Related objects / Objets liés
        ]
        
        rospy.loginfo(f"Model cache directory: {self.model_cache_dir}")
    
    def load_detection_model(self, model_name="facebook/detr-resnet-50"):
        """
        Load object detection model from local cache.
        Uses DETR (DEtection TRansformer) by default - good for tableware detection.
        
        Args:
            model_name (str): Model identifier from Hugging Face.
        
        Returns:
            bool: True if loaded successfully, False otherwise.
        """
        try:
            from transformers import DetrImageProcessor, DetrForObjectDetection
            
            model_path = self.model_cache_dir / model_name.replace('/', '_')
            
            rospy.loginfo(f"Loading detection model from {model_path}")
            
            # Check if model exists locally
            if model_path.exists() and (model_path / "config.json").exists():
                rospy.loginfo(f"Loading model from local cache: {model_path}")
                self.detection_processor = DetrImageProcessor.from_pretrained(
                    str(model_path),
                    local_files_only=True
                )
                self.detection_model = DetrForObjectDetection.from_pretrained(
                    str(model_path),
                    local_files_only=True
                )
            else:
                rospy.logwarn(f"Model not found locally at {model_path}")
                rospy.loginfo(f"Attempting to download {model_name}...")
                self.detection_processor = DetrImageProcessor.from_pretrained(model_name)
                self.detection_model = DetrForObjectDetection.from_pretrained(model_name)
                
                # Save for future use
                rospy.loginfo(f"Saving model to {model_path}")
                model_path.mkdir(parents=True, exist_ok=True)
                self.detection_processor.save_pretrained(str(model_path))
                self.detection_model.save_pretrained(str(model_path))
            
            # Move model to device
            self.detection_model.to(self.device)
            self.detection_model.eval()
            
            rospy.loginfo(f"Detection model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            rospy.logerr(f"Failed to load detection model: {e}")
            return False
    
    def detect_objects(self, image, confidence_threshold=0.7):
        """
        Detect objects in an image using the loaded model.
        
        Args:
            image: PIL Image or numpy array
            confidence_threshold (float): Minimum confidence for detections (0-1)
        
        Returns:
            list: List of detections, each containing:
                  - label: object class name
                  - score: confidence score
                  - box: [x_min, y_min, x_max, y_max] in pixels
        """
        if self.detection_model is None or self.detection_processor is None:
            rospy.logerr("Detection model not loaded. Call load_detection_model() first.")
            return []
        
        try:
            # Convert numpy array to PIL Image if needed
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            
            # Process image
            inputs = self.detection_processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Run inference
            with torch.no_grad():
                outputs = self.detection_model(**inputs)
            
            # Convert outputs to COCO API format
            target_sizes = torch.tensor([image.size[::-1]]).to(self.device)
            results = self.detection_processor.post_process_object_detection(
                outputs, 
                target_sizes=target_sizes, 
                threshold=confidence_threshold
            )[0]
            
            # Extract detections
            detections = []
            for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                label_name = self.detection_model.config.id2label[label.item()]
                
                # Filter for tableware objects - use exact word matching
                label_lower = label_name.lower()
                if any(label_lower == target.lower() or 
                       label_lower.startswith(target.lower() + ' ') or
                       label_lower.endswith(' ' + target.lower())
                       for target in self.target_classes):
                    detection = {
                        'label': label_name,
                        'score': score.item(),
                        'box': box.cpu().numpy().tolist()  # [x_min, y_min, x_max, y_max]
                    }
                    detections.append(detection)
                    rospy.logdebug(f"Detected {label_name} with confidence {score.item():.3f}")
            
            rospy.loginfo(f"Detected {len(detections)} tableware objects")
            return detections
            
        except Exception as e:
            rospy.logerr(f"Error during object detection: {e}")
            return []
    
    def compute_object_positions(self, detections, image_width, image_height):
        """
        Compute center positions for detected objects.
        
        Args:
            detections (list): List of detection dictionaries from detect_objects()
            image_width (int): Image width in pixels
            image_height (int): Image height in pixels
        
        Returns:
            list: List of object positions with labels and coordinates
        """
        positions = []
        
        for det in detections:
            box = det['box']
            x_min, y_min, x_max, y_max = box
            
            # Compute center
            center_x = (x_min + x_max) / 2.0
            center_y = (y_min + y_max) / 2.0
            
            # Normalize to 0-1 range
            norm_x = center_x / image_width
            norm_y = center_y / image_height
            
            position = {
                'label': det['label'],
                'score': det['score'],
                'center_x': center_x,
                'center_y': center_y,
                'normalized_x': norm_x,
                'normalized_y': norm_y,
                'width': x_max - x_min,
                'height': y_max - y_min
            }
            positions.append(position)
        
        return positions
    
    def organize_tableware(self, detections):
        """
        Organize detected tableware by type for arrangement planning.
        
        Args:
            detections (list): List of detection dictionaries
        
        Returns:
            dict: Organized objects by category
        """
        organized = {
            'cutlery': [],
            'plates': [],
            'cups': [],
            'others': []
        }
        
        for det in detections:
            label = det['label'].lower()
            
            if any(utensil in label for utensil in ['fork', 'knife', 'spoon']):
                organized['cutlery'].append(det)
            elif any(dish in label for dish in ['plate', 'dish', 'bowl']):
                organized['plates'].append(det)
            elif any(drink in label for drink in ['cup', 'glass']):
                organized['cups'].append(det)
            else:
                organized['others'].append(det)
        
        rospy.loginfo(f"Organized: {len(organized['cutlery'])} cutlery, "
                     f"{len(organized['plates'])} plates, "
                     f"{len(organized['cups'])} cups")
        
        return organized
    
    def get_model_info(self):
        """
        Get information about loaded model.
        
        Returns:
            dict: Model information
        """
        info = {
            'model_loaded': self.detection_model is not None,
            'device': str(self.device),
            'cache_dir': str(self.model_cache_dir),
            'target_classes': self.target_classes
        }
        return info


def download_model(model_name="facebook/detr-resnet-50", cache_dir=None):
    """
    Standalone function to download and cache a model.
    Can be called separately to prepare models offline.
    
    Args:
        model_name (str): Hugging Face model identifier
        cache_dir (str): Directory to save the model
    
    Returns:
        bool: True if successful
    """
    try:
        from transformers import DetrImageProcessor, DetrForObjectDetection
        
        if cache_dir is None:
            cache_dir = os.path.expanduser('~/ros_ws/models')
        
        cache_path = Path(cache_dir) / model_name.replace('/', '_')
        cache_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Downloading {model_name} to {cache_path}...")
        
        processor = DetrImageProcessor.from_pretrained(model_name)
        model = DetrForObjectDetection.from_pretrained(model_name)
        
        processor.save_pretrained(str(cache_path))
        model.save_pretrained(str(cache_path))
        
        print(f"Model successfully saved to {cache_path}")
        return True
        
    except Exception as e:
        print(f"Error downloading model: {e}")
        return False


if __name__ == "__main__":
    # Test/download script
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "download":
        model_name = sys.argv[2] if len(sys.argv) > 2 else "facebook/detr-resnet-50"
        print(f"Downloading model: {model_name}")
        success = download_model(model_name)
        sys.exit(0 if success else 1)
    else:
        print("Usage:")
        print("  python local_model_handler.py download [model_name]")
        print("  Default model: facebook/detr-resnet-50")
