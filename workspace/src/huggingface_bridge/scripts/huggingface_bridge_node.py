#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nœud ROS principal pour le pont Hugging Face.
Permet la communication bidirectionnelle entre Tiago et les modèles Hugging Face.
"""

import rospy
import sys
import os
import subprocess
import json
import time
from pathlib import Path
from std_msgs.msg import String

# Ajouter le chemin du module au PYTHONPATH
script_dir = Path(__file__).resolve().parent
module_dir = script_dir.parent / 'src'
sys.path.insert(0, str(module_dir))

from huggingface_bridge.image_handler import ImageHandler
from huggingface_bridge.json_handler import JSONHandler
from huggingface_bridge.huggingface_client import HuggingFaceClient

# Import des services (à faire après l'import de rospy)
from huggingface_bridge.srv import ProcessImage, ProcessImageResponse
from huggingface_bridge.srv import GetPositions, GetPositionsResponse


class HuggingFaceBridgeNode:
    """Nœud ROS pour la communication avec Hugging Face."""
    
    def __init__(self):
        """Initialise le nœud ROS."""
        # Initialiser le nœud ROS
        rospy.init_node('huggingface_bridge_node', anonymous=False)
        
        rospy.loginfo("=" * 70)
        rospy.loginfo("Initialisation du nœud Hugging Face Bridge")
        rospy.loginfo("=" * 70)
        
        # Charger la configuration
        self.load_config()
        
        # Initialiser les gestionnaires
        self.image_handler = ImageHandler()
        self.json_handler = JSONHandler()
        
        # Initialiser le client Hugging Face
        hf_token = self.config.get('huggingface', {}).get('token', '')
        if hf_token.startswith('${') and hf_token.endswith('}'):
            # Variable d'environnement
            var_name = hf_token[2:-1]
            hf_token = os.environ.get(var_name, '')
        
        self.hf_client = HuggingFaceClient(token=hf_token)
        
        # Chemins de configuration
        self.paths = self.config.get('paths', {})
        self.pipeline_dir = self.expand_path(self.paths.get('pipeline_dir', '~/ros_ws/workspace/pipeline'))
        self.output_dir = self.expand_path(self.paths.get('output_dir', '~/ros_ws/workspace/pipeline/outputs'))
        
        # Créer les services ROS
        self.create_services()
        
        # Créer les publishers
        self.create_publishers()
        
        # État du traitement
        self.processing = False
        self.current_step = ""
        
        rospy.loginfo("✓ Nœud Hugging Face Bridge initialisé avec succès")
        rospy.loginfo("✓ Services disponibles:")
        rospy.loginfo(f"  - {self.config['ros']['service_send_image']}")
        rospy.loginfo(f"  - {self.config['ros']['service_get_positions']}")
        rospy.loginfo("=" * 70)
    
    def expand_path(self, path: str) -> str:
        """Expanse un chemin avec ~ et variables."""
        return os.path.expanduser(os.path.expandvars(path))
    
    def load_config(self):
        """Charge la configuration depuis le fichier YAML."""
        try:
            import yaml
            
            # Chercher le fichier de config
            config_path = rospy.get_param('~config_file', '')
            
            if not config_path:
                # Utiliser le chemin par défaut
                pkg_dir = Path(__file__).resolve().parent.parent
                config_path = pkg_dir / 'config' / 'huggingface_config.yaml'
            
            rospy.loginfo(f"Chargement de la configuration depuis: {config_path}")
            
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            rospy.loginfo("✓ Configuration chargée avec succès")
            
        except Exception as e:
            rospy.logerr(f"Erreur lors du chargement de la configuration: {e}")
            # Configuration par défaut
            self.config = {
                'huggingface': {'token': ''},
                'paths': {
                    'pipeline_dir': '~/ros_ws/workspace/pipeline',
                    'output_dir': '~/ros_ws/workspace/pipeline/outputs'
                },
                'ros': {
                    'service_send_image': '/tiago/send_image_to_hf',
                    'service_get_positions': '/tiago/get_object_positions',
                    'topic_status': '/tiago/hf_status',
                    'topic_objects': '/tiago/detected_objects'
                },
                'processing': {
                    'timeout': 300
                }
            }
    
    def create_services(self):
        """Crée les services ROS."""
        service_send = self.config['ros']['service_send_image']
        service_get = self.config['ros']['service_get_positions']
        
        self.service_send_image = rospy.Service(
            service_send,
            ProcessImage,
            self.handle_process_image
        )
        
        self.service_get_positions = rospy.Service(
            service_get,
            GetPositions,
            self.handle_get_positions
        )
        
        rospy.loginfo(f"✓ Service créé: {service_send}")
        rospy.loginfo(f"✓ Service créé: {service_get}")
    
    def create_publishers(self):
        """Crée les publishers ROS."""
        topic_status = self.config['ros']['topic_status']
        topic_objects = self.config['ros']['topic_objects']
        
        self.pub_status = rospy.Publisher(topic_status, String, queue_size=10)
        self.pub_objects = rospy.Publisher(topic_objects, String, queue_size=10)
        
        rospy.loginfo(f"✓ Publisher créé: {topic_status}")
        rospy.loginfo(f"✓ Publisher créé: {topic_objects}")
    
    def publish_status(self, status: str, step: str, progress: float, message: str):
        """
        Publie le statut du traitement.
        
        Args:
            status: État (processing, completed, error)
            step: Étape en cours
            progress: Progression (0.0 à 1.0)
            message: Message descriptif
        """
        status_dict = {
            "status": status,
            "step": step,
            "progress": progress,
            "message": message,
            "timestamp": time.time()
        }
        
        status_json = json.dumps(status_dict, indent=2)
        self.pub_status.publish(status_json)
        rospy.loginfo(f"[Status] {step}: {message} ({progress*100:.0f}%)")
    
    def publish_objects(self, objects: list):
        """
        Publie la liste des objets détectés.
        
        Args:
            objects: Liste des objets détectés
        """
        objects_dict = {
            "timestamp": time.time(),
            "objects": objects
        }
        
        objects_json = json.dumps(objects_dict, indent=2)
        self.pub_objects.publish(objects_json)
        rospy.loginfo(f"[Objects] {len(objects)} objets détectés publiés")
    
    def handle_process_image(self, req):
        """
        Gère la requête de traitement d'image.
        
        Args:
            req: Requête ProcessImage
            
        Returns:
            ProcessImageResponse
        """
        rospy.loginfo("=" * 70)
        rospy.loginfo("Nouvelle requête de traitement d'image")
        rospy.loginfo("=" * 70)
        rospy.loginfo(f"Image source: {req.image_path}")
        
        response = ProcessImageResponse()
        
        try:
            # Vérifier si un traitement est en cours
            if self.processing:
                response.success = False
                response.message = "Un traitement est déjà en cours"
                rospy.logwarn(response.message)
                return response
            
            self.processing = True
            
            # Étape 1: Vérifier l'image d'entrée
            self.publish_status("processing", "validation", 0.0, "Validation de l'image...")
            
            image_path = self.expand_path(req.image_path)
            
            if not self.image_handler.validate_image_path(image_path):
                response.success = False
                response.message = f"Image non trouvée ou invalide: {image_path}"
                rospy.logerr(response.message)
                self.processing = False
                self.publish_status("error", "validation", 0.0, response.message)
                return response
            
            rospy.loginfo(f"✓ Image validée: {image_path}")
            
            # Copier l'image dans le répertoire pipeline
            pipeline_input = os.path.join(self.pipeline_dir, 'data', 'images', 'table_input.png')
            os.makedirs(os.path.dirname(pipeline_input), exist_ok=True)
            
            img = self.image_handler.read_image(image_path)
            self.image_handler.write_image(img, pipeline_input)
            rospy.loginfo(f"✓ Image copiée vers: {pipeline_input}")
            
            # Étape 2: Exécuter le pipeline complet
            self.publish_status("processing", "pipeline", 0.1, "Exécution du pipeline IA...")
            
            success = self.run_pipeline()
            
            if not success:
                response.success = False
                response.message = "Erreur lors de l'exécution du pipeline"
                rospy.logerr(response.message)
                self.processing = False
                self.publish_status("error", "pipeline", 0.5, response.message)
                return response
            
            # Étape 3: Récupérer les résultats
            self.publish_status("processing", "results", 0.9, "Récupération des résultats...")
            
            # Chemins des fichiers de sortie
            detections_json = os.path.join(self.output_dir, 'detections_input.json')
            final_positions_json = os.path.join(self.output_dir, 'final_positions.json')
            generated_image = os.path.join(self.output_dir, 'img_generated.png')
            
            # Vérifier que les fichiers existent
            if not os.path.exists(detections_json):
                response.success = False
                response.message = f"Fichier de détections non trouvé: {detections_json}"
                rospy.logerr(response.message)
                self.processing = False
                return response
            
            if not os.path.exists(final_positions_json):
                response.success = False
                response.message = f"Fichier de positions finales non trouvé: {final_positions_json}"
                rospy.logerr(response.message)
                self.processing = False
                return response
            
            # Publier les objets détectés
            detections = self.json_handler.read_json(detections_json)
            if detections:
                self.publish_objects(detections)
            
            # Construire la réponse
            response.success = True
            response.message = "Traitement terminé avec succès"
            response.detections_json_path = detections_json
            response.final_positions_json_path = final_positions_json
            response.generated_image_path = generated_image if os.path.exists(generated_image) else ""
            
            self.publish_status("completed", "done", 1.0, "Traitement terminé avec succès")
            
            rospy.loginfo("=" * 70)
            rospy.loginfo("✓ Traitement terminé avec succès")
            rospy.loginfo(f"  - Détections: {detections_json}")
            rospy.loginfo(f"  - Positions finales: {final_positions_json}")
            rospy.loginfo(f"  - Image générée: {response.generated_image_path}")
            rospy.loginfo("=" * 70)
            
        except Exception as e:
            response.success = False
            response.message = f"Erreur inattendue: {str(e)}"
            rospy.logerr(response.message)
            self.publish_status("error", "exception", 0.0, response.message)
        
        finally:
            self.processing = False
        
        return response
    
    def run_pipeline(self) -> bool:
        """
        Exécute le pipeline complet de traitement.
        
        Returns:
            True si succès, False sinon
        """
        try:
            # Utiliser le script run_pipeline.py
            pipeline_script = os.path.join(self.pipeline_dir, 'run_pipeline.py')
            
            if not os.path.exists(pipeline_script):
                rospy.logerr(f"Script pipeline non trouvé: {pipeline_script}")
                return False
            
            rospy.loginfo(f"Exécution du pipeline: {pipeline_script}")
            
            # Changer de répertoire pour le pipeline
            original_dir = os.getcwd()
            os.chdir(self.pipeline_dir)
            
            # Exécuter le pipeline
            timeout = self.config.get('processing', {}).get('timeout', 300)
            
            result = subprocess.run(
                ['python3', pipeline_script],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Revenir au répertoire original
            os.chdir(original_dir)
            
            # Afficher la sortie
            if result.stdout:
                rospy.loginfo("Sortie du pipeline:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        rospy.loginfo(f"  {line}")
            
            if result.stderr:
                rospy.logwarn("Erreurs du pipeline:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        rospy.logwarn(f"  {line}")
            
            if result.returncode != 0:
                rospy.logerr(f"Le pipeline a échoué avec le code: {result.returncode}")
                return False
            
            rospy.loginfo("✓ Pipeline exécuté avec succès")
            return True
            
        except subprocess.TimeoutExpired:
            rospy.logerr(f"Timeout du pipeline après {timeout} secondes")
            return False
        except Exception as e:
            rospy.logerr(f"Erreur lors de l'exécution du pipeline: {e}")
            return False
    
    def handle_get_positions(self, req):
        """
        Gère la requête de récupération des positions.
        
        Args:
            req: Requête GetPositions
            
        Returns:
            GetPositionsResponse
        """
        rospy.loginfo(f"Requête de positions: {req.json_type}")
        
        response = GetPositionsResponse()
        
        try:
            # Déterminer le fichier à lire
            if req.json_type == "initial":
                json_path = os.path.join(self.output_dir, 'detections_input.json')
            elif req.json_type == "final":
                json_path = os.path.join(self.output_dir, 'final_positions.json')
            else:
                response.success = False
                response.json_content = json.dumps({
                    "error": f"Type invalide: {req.json_type}. Utilisez 'initial' ou 'final'"
                })
                return response
            
            # Lire le fichier JSON
            data = self.json_handler.read_json(json_path)
            
            if data is None:
                response.success = False
                response.json_content = json.dumps({
                    "error": f"Impossible de lire le fichier: {json_path}"
                })
                rospy.logerr(f"Fichier non trouvé: {json_path}")
                return response
            
            # Convertir en string JSON
            response.success = True
            response.json_content = self.json_handler.json_to_string(data)
            
            rospy.loginfo(f"✓ Positions {req.json_type} récupérées ({len(data)} objets)")
            
        except Exception as e:
            response.success = False
            response.json_content = json.dumps({"error": str(e)})
            rospy.logerr(f"Erreur lors de la récupération des positions: {e}")
        
        return response
    
    def run(self):
        """Boucle principale du nœud."""
        rospy.loginfo("Nœud Hugging Face Bridge en cours d'exécution...")
        rospy.loginfo("En attente de requêtes...")
        
        # Publier un statut initial
        self.publish_status("idle", "waiting", 0.0, "En attente de requêtes")
        
        rospy.spin()


def main():
    """Point d'entrée principal."""
    try:
        node = HuggingFaceBridgeNode()
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Interruption du nœud")
    except Exception as e:
        rospy.logerr(f"Erreur fatale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
