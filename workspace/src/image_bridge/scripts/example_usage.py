#!/usr/bin/env python3
"""
Exemple d'utilisation du système de détection d'objets.
Montre comment intégrer la détection dans votre propre code.
"""

import rospy
import json
from std_msgs.msg import String
from geometry_msgs.msg import PoseArray
from std_srvs.srv import Trigger, TriggerRequest


class ObjectDetectionExample:
    """
    Exemple d'utilisation du système de détection pour organiser des objets.
    """
    
    # Configuration constants pour l'organisation
    FORK_LEFT_OFFSET = 0.15   # Décalage à gauche pour les fourchettes
    KNIFE_RIGHT_OFFSET = 0.15  # Décalage à droite pour les couteaux
    
    def __init__(self):
        """Initialiser l'exemple."""
        rospy.init_node('object_detection_example', anonymous=True)
        
        # État
        self.latest_detections = None
        self.processing = False
        
        # S'abonner aux détections
        rospy.Subscriber('/tiago/object_detections', String, self.detections_callback)
        
        rospy.loginfo("Exemple de détection d'objets initialisé")
    
    def detections_callback(self, msg):
        """
        Callback appelé quand de nouvelles détections arrivent.
        
        Args:
            msg (std_msgs/String): JSON des détections
        """
        try:
            self.latest_detections = json.loads(msg.data)
            rospy.loginfo(f"Reçu {self.latest_detections['count']} détections")
            
            # Analyser et organiser
            self.organize_objects(self.latest_detections['objects'])
            
        except Exception as e:
            rospy.logerr(f"Erreur dans le callback: {e}")
    
    def organize_objects(self, objects):
        """
        Organiser les objets détectés.
        
        Args:
            objects (list): Liste des objets détectés avec positions
        """
        # Séparer par type
        forks = [o for o in objects if 'fork' in o['label'].lower()]
        knives = [o for o in objects if 'knife' in o['label'].lower()]
        plates = [o for o in objects if 'plate' in o['label'].lower() or 'dish' in o['label'].lower()]
        
        rospy.loginfo("=" * 60)
        rospy.loginfo("ORGANISATION DES OBJETS")
        rospy.loginfo("=" * 60)
        
        # Fourchettes - à gauche
        if forks:
            rospy.loginfo(f"\nFourchettes ({len(forks)}):")
            for fork in forks:
                rospy.loginfo(f"  Position actuelle: ({fork['center_x']:.1f}, {fork['center_y']:.1f})")
                # Position cible: à gauche de l'assiette
                target_x = fork['normalized_x'] - self.FORK_LEFT_OFFSET
                rospy.loginfo(f"  → Déplacer vers: normalized_x={target_x:.2f}")
        
        # Couteaux - à droite
        if knives:
            rospy.loginfo(f"\nCouteaux ({len(knives)}):")
            for knife in knives:
                rospy.loginfo(f"  Position actuelle: ({knife['center_x']:.1f}, {knife['center_y']:.1f})")
                # Position cible: à droite de l'assiette
                target_x = knife['normalized_x'] + self.KNIFE_RIGHT_OFFSET
                rospy.loginfo(f"  → Déplacer vers: normalized_x={target_x:.2f}")
        
        # Assiettes - au centre
        if plates:
            rospy.loginfo(f"\nAssiettes ({len(plates)}):")
            for plate in plates:
                rospy.loginfo(f"  Position: ({plate['center_x']:.1f}, {plate['center_y']:.1f})")
                rospy.loginfo(f"  → Garder au centre (référence)")
        
        rospy.loginfo("=" * 60)
    
    def process_captured_images(self):
        """
        Demander le traitement de toutes les images capturées.
        
        Returns:
            bool: True si succès
        """
        rospy.loginfo("Demande de traitement des images capturées...")
        
        try:
            # Attendre que le service soit disponible
            rospy.wait_for_service('/tiago/process_captured_images', timeout=5.0)
            
            # Appeler le service
            service = rospy.ServiceProxy('/tiago/process_captured_images', Trigger)
            response = service(TriggerRequest())
            
            if response.success:
                rospy.loginfo(f"Succès: {response.message}")
                return True
            else:
                rospy.logwarn(f"Échec: {response.message}")
                return False
                
        except rospy.ROSException as e:
            rospy.logerr(f"Erreur lors de l'appel du service: {e}")
            return False
    
    def run_example(self):
        """Exécuter l'exemple complet."""
        rospy.loginfo("=" * 60)
        rospy.loginfo("EXEMPLE D'UTILISATION DU SYSTÈME DE DÉTECTION")
        rospy.loginfo("=" * 60)
        
        # Étape 1: Traiter les images
        rospy.loginfo("\nÉtape 1: Traitement des images capturées")
        if not self.process_captured_images():
            rospy.logwarn("Aucune image à traiter ou erreur")
            rospy.loginfo("\nPour capturer des images d'abord:")
            rospy.loginfo("  cd ~/ros_ws/scripts")
            rospy.loginfo("  python3 capture.py")
            return
        
        # Étape 2: Attendre les résultats
        rospy.loginfo("\nÉtape 2: Attente des résultats...")
        rospy.loginfo("(Les détections seront affichées automatiquement)")
        
        # Rester actif pour recevoir les détections
        rospy.loginfo("\nAppuyez sur Ctrl+C pour arrêter")
        rospy.spin()


def simple_example():
    """Exemple simple pour appeler le service de traitement."""
    rospy.init_node('simple_example', anonymous=True)
    
    print("\n" + "=" * 60)
    print("EXEMPLE SIMPLE: Traiter les images capturées")
    print("=" * 60 + "\n")
    
    try:
        # Attendre le service
        print("Attente du service de traitement...")
        rospy.wait_for_service('/tiago/process_captured_images', timeout=5.0)
        
        # Appeler le service
        print("Appel du service...")
        service = rospy.ServiceProxy('/tiago/process_captured_images', Trigger)
        response = service(TriggerRequest())
        
        print("\nRésultat:")
        print(f"  Succès: {response.success}")
        print(f"  Message: {response.message}")
        
        if response.success:
            print("\n✓ Images traitées avec succès!")
            print("\nVoir les résultats dans:")
            print("  - ~/ros_ws/data/results/annotated_*.png")
            print("  - ~/ros_ws/data/results/detection_results_*.json")
        
    except rospy.ROSException as e:
        print(f"\n✗ Erreur: {e}")
        print("\nAssurez-vous que le nœud de traitement est lancé:")
        print("  roslaunch image_bridge image_processing.launch")
    
    print("\n" + "=" * 60 + "\n")


def main():
    """Point d'entrée principal."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        # Mode simple: juste traiter les images
        simple_example()
    else:
        # Mode complet: traiter et organiser
        try:
            example = ObjectDetectionExample()
            example.run_example()
        except rospy.ROSInterruptException:
            rospy.loginfo("Exemple interrompu")


if __name__ == '__main__':
    main()
