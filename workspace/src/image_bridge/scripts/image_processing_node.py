#!/usr/bin/env python3
"""
Image Processing Node with Local Hugging Face Model.
Processes images captured by Tiago robot and detects tableware objects.
"""

import rospy
import os
import cv2
import json
from pathlib import Path
from datetime import datetime
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseArray, Pose, Point, Quaternion
from std_msgs.msg import Header, String
from cv_bridge import CvBridge

# Import local model handler
from image_bridge.local_model_handler import LocalModelHandler


class ImageProcessingNode:
    """
    ROS node for processing captured images with local ML models.
    Detects tableware objects and publishes their positions.
    """
    
    def __init__(self):
        """Initialize the image processing node."""
        rospy.init_node('image_processing_node', anonymous=False)
        rospy.loginfo("Initialisation du nœud de traitement d'images...")
        
        # CV Bridge for ROS-OpenCV conversion
        self.bridge = CvBridge()
        
        # Initialize local model handler
        self.model_handler = LocalModelHandler()
        
        # Load detection model
        model_name = rospy.get_param('~detection_model', 'facebook/detr-resnet-50')
        rospy.loginfo(f"Chargement du modèle: {model_name}")
        
        if not self.model_handler.load_detection_model(model_name):
            rospy.logfatal("Échec du chargement du modèle!")
            rospy.signal_shutdown("Model loading failed")
            return
        
        # Configuration
        self.confidence_threshold = rospy.get_param('~confidence_threshold', 0.7)
        self.images_dir = Path(rospy.get_param(
            '~images_dir', 
            os.path.expanduser('~/ros_ws/data/images')
        ))
        self.results_dir = Path(rospy.get_param(
            '~results_dir',
            os.path.expanduser('~/ros_ws/data/results')
        ))
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Publishers
        self.detections_pub = rospy.Publisher(
            '/tiago/object_detections',
            String,
            queue_size=10
        )
        
        self.poses_pub = rospy.Publisher(
            '/tiago/object_poses',
            PoseArray,
            queue_size=10
        )
        
        self.annotated_image_pub = rospy.Publisher(
            '/tiago/annotated_image',
            Image,
            queue_size=1
        )
        
        # Subscriber for real-time image processing
        self.image_sub = rospy.Subscriber(
            rospy.get_param('~camera_topic', '/xtion/rgb/image_raw'),
            Image,
            self.image_callback,
            queue_size=1
        )
        
        # Service for processing stored images
        from std_srvs.srv import Trigger, TriggerResponse
        self.process_service = rospy.Service(
            '/tiago/process_captured_images',
            Trigger,
            self.process_captured_images_service
        )
        
        rospy.loginfo("Nœud de traitement d'images initialisé avec succès!")
        rospy.loginfo(f"Seuil de confiance: {self.confidence_threshold}")
        rospy.loginfo(f"Répertoire d'images: {self.images_dir}")
        rospy.loginfo(f"Répertoire de résultats: {self.results_dir}")
    
    def image_callback(self, msg):
        """
        Callback for real-time image processing.
        
        Args:
            msg (sensor_msgs/Image): Image message from camera
        """
        try:
            # Convert ROS image to OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # Process image
            detections = self.process_image(cv_image)
            
            # Publish results
            if detections:
                self.publish_detections(detections, cv_image.shape[1], cv_image.shape[0])
                
                # Create and publish annotated image
                annotated = self.draw_detections(cv_image, detections)
                annotated_msg = self.bridge.cv2_to_imgmsg(annotated, "bgr8")
                self.annotated_image_pub.publish(annotated_msg)
                
        except Exception as e:
            rospy.logerr(f"Erreur dans le callback d'image: {e}")
    
    def process_image(self, cv_image):
        """
        Process a single image with the detection model.
        
        Args:
            cv_image: OpenCV image (BGR)
        
        Returns:
            list: List of detections
        """
        # Convert BGR to RGB for the model
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        # Detect objects
        detections = self.model_handler.detect_objects(
            rgb_image, 
            confidence_threshold=self.confidence_threshold
        )
        
        return detections
    
    def draw_detections(self, image, detections):
        """
        Draw bounding boxes and labels on image.
        
        Args:
            image: OpenCV image
            detections: List of detection dictionaries
        
        Returns:
            Annotated image
        """
        annotated = image.copy()
        
        for det in detections:
            box = det['box']
            label = det['label']
            score = det['score']
            
            # Draw bounding box
            x_min, y_min, x_max, y_max = map(int, box)
            color = (0, 255, 0)  # Green
            cv2.rectangle(annotated, (x_min, y_min), (x_max, y_max), color, 2)
            
            # Draw label
            text = f"{label}: {score:.2f}"
            cv2.putText(annotated, text, (x_min, y_min - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated
    
    def publish_detections(self, detections, image_width, image_height):
        """
        Publish detection results as ROS messages.
        
        Args:
            detections: List of detections
            image_width: Image width
            image_height: Image height
        """
        # Compute positions
        positions = self.model_handler.compute_object_positions(
            detections, image_width, image_height
        )
        
        # Publish as JSON string
        detection_data = {
            'timestamp': rospy.Time.now().to_sec(),
            'count': len(detections),
            'objects': positions
        }
        self.detections_pub.publish(json.dumps(detection_data, indent=2))
        
        # Publish as PoseArray (for visualization in RViz)
        pose_array = PoseArray()
        pose_array.header = Header()
        pose_array.header.stamp = rospy.Time.now()
        pose_array.header.frame_id = "xtion_rgb_optical_frame"
        
        for pos in positions:
            pose = Pose()
            # Use normalized coordinates
            pose.position.x = pos['normalized_x']
            pose.position.y = pos['normalized_y']
            pose.position.z = 0.0
            pose.orientation.w = 1.0
            pose_array.poses.append(pose)
        
        self.poses_pub.publish(pose_array)
    
    def process_captured_images_service(self, req):
        """
        Service handler to process all captured images.
        
        Args:
            req: Service request (Trigger)
        
        Returns:
            TriggerResponse: Success status and message
        """
        from std_srvs.srv import TriggerResponse
        
        rospy.loginfo("Traitement des images capturées...")
        
        try:
            # Find all PNG images in the images directory
            image_files = sorted(self.images_dir.glob("*.png"))
            
            if not image_files:
                return TriggerResponse(
                    success=False,
                    message=f"Aucune image trouvée dans {self.images_dir}"
                )
            
            rospy.loginfo(f"Trouvé {len(image_files)} images à traiter")
            
            all_results = []
            
            for image_path in image_files:
                rospy.loginfo(f"Traitement de {image_path.name}...")
                
                # Load image
                cv_image = cv2.imread(str(image_path))
                if cv_image is None:
                    rospy.logwarn(f"Impossible de charger {image_path.name}")
                    continue
                
                # Process image
                detections = self.process_image(cv_image)
                
                # Compute positions
                positions = self.model_handler.compute_object_positions(
                    detections, cv_image.shape[1], cv_image.shape[0]
                )
                
                # Organize objects
                organized = self.model_handler.organize_tableware(detections)
                
                # Save annotated image
                annotated = self.draw_detections(cv_image, detections)
                annotated_path = self.results_dir / f"annotated_{image_path.name}"
                cv2.imwrite(str(annotated_path), annotated)
                
                # Store results
                result = {
                    'image': image_path.name,
                    'detections': positions,
                    'organized': {
                        'cutlery_count': len(organized['cutlery']),
                        'plates_count': len(organized['plates']),
                        'cups_count': len(organized['cups'])
                    }
                }
                all_results.append(result)
                
                rospy.loginfo(f"  Détecté: {len(detections)} objets")
            
            # Save results to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.results_dir / f"detection_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(all_results, f, indent=2)
            
            message = (f"Traitement terminé: {len(image_files)} images traitées. "
                      f"Résultats sauvegardés dans {results_file}")
            
            rospy.loginfo(message)
            return TriggerResponse(success=True, message=message)
            
        except Exception as e:
            error_msg = f"Erreur lors du traitement: {e}"
            rospy.logerr(error_msg)
            return TriggerResponse(success=False, message=error_msg)
    
    def spin(self):
        """Run the node."""
        rospy.loginfo("Nœud de traitement d'images en cours d'exécution...")
        rospy.spin()


def main():
    """Main entry point."""
    try:
        node = ImageProcessingNode()
        node.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("Nœud interrompu")
    except Exception as e:
        rospy.logfatal(f"Erreur fatale: {e}")


if __name__ == '__main__':
    main()
