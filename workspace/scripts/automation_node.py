#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 🤖 SCRIPT D'AUTOMATISATION - RÉARRANGEMENT AUTONOME D'OBJETS AVEC TIAGO
===============================================================================

Ce script ROS orchestre le pipeline complet de réarrangement autonome d'objets :

    1. CAPTURE        : Prise de photos RGB et profondeur via la caméra Xtion
    2. PIPELINE IA    : Détection, génération d'image cible, calcul des positions
    3. COMMANDE ROBOT : Déplacement du bras robotique vers les objets

Usage:
    rosrun <package> automation_node.py [--mode full|capture|pipeline|command]

Auteur : R3 - Ingénieur Logiciel & Intégration
Projet : VA50 - Vision Artificielle et Systèmes Autonomes
===============================================================================
"""

import rospy
import subprocess
import sys
import os
import time
import signal
import argparse
from std_msgs.msg import String, Bool
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Chemins des scripts (relatifs au workspace ROS)
WORKSPACE_PATH = os.path.expanduser("~/ros_ws/workspace")
SCRIPTS_PATH = os.path.join(WORKSPACE_PATH, "scripts")
PIPELINE_PATH = os.path.join(WORKSPACE_PATH, "pipeline")

# Configuration des étapes
STEP_CONFIG = {
    "capture": {
        "script": os.path.join(SCRIPTS_PATH, "capture.py"),
        "name": "Capture d'images",
        "timeout": 60,  # secondes
        "description": "Capture des images RGB et profondeur via la caméra Xtion"
    },
    "pipeline": {
        "script": os.path.join(PIPELINE_PATH, "run_pipeline.py"),
        "working_dir": PIPELINE_PATH,
        "name": "Pipeline IA",
        "timeout": 300,  # secondes (le pipeline peut être long)
        "description": "Détection d'objets, génération d'image et calcul des positions"
    },
    "command": {
        "script": os.path.join(SCRIPTS_PATH, "command.py"),
        "name": "Commande robot",
        "timeout": 120,  # secondes
        "description": "Déplacement du bras robotique vers les positions calculées"
    }
}


# ==============================================================================
# CLASSE PRINCIPALE
# ==============================================================================

class TiagoAutomationNode:
    """
    Nœud ROS pour l'automatisation du pipeline de réarrangement d'objets.
    
    Cette classe gère l'exécution séquentielle des 3 étapes principales:
    - Capture d'images dans Gazebo
    - Exécution du pipeline IA (Hugging Face)
    - Commande du robot Tiago
    """

    def __init__(self):
        """Initialisation du nœud d'automatisation."""
        rospy.init_node('tiago_automation_node', anonymous=False)
        
        # Publishers pour les statuts
        self.status_pub = rospy.Publisher('/tiago/automation_status', String, queue_size=10)
        self.step_pub = rospy.Publisher('/tiago/current_step', String, queue_size=10)
        self.complete_pub = rospy.Publisher('/tiago/automation_complete', Bool, queue_size=10)
        
        # État interne
        self.current_step = None
        self.is_running = False
        self.start_time = None
        self.step_results = {}
        
        # Gestion des signaux
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        rospy.loginfo("=" * 70)
        rospy.loginfo("🤖 TIAGO AUTOMATION NODE - INITIALISÉ")
        rospy.loginfo("=" * 70)
        
        # Attendre que ROS soit prêt
        rospy.sleep(1.0)

    def signal_handler(self, sig, frame):
        """Gestion propre des signaux d'interruption."""
        rospy.logwarn("⚠️  Signal d'interruption reçu, arrêt en cours...")
        self.is_running = False
        self.publish_status("INTERRUPTED", "Pipeline interrompu par l'utilisateur")
        rospy.signal_shutdown("Interruption utilisateur")
        sys.exit(0)

    def publish_status(self, status, message=""):
        """Publie le statut actuel sur le topic ROS."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_msg = String()
        status_msg.data = f"[{timestamp}] {status}: {message}"
        self.status_pub.publish(status_msg)
        
    def publish_step(self, step_name):
        """Publie l'étape en cours sur le topic ROS."""
        step_msg = String()
        step_msg.data = step_name
        self.step_pub.publish(step_msg)
        self.current_step = step_name

    def print_header(self, title, emoji="🔵"):
        """Affiche un en-tête formaté."""
        rospy.loginfo("")
        rospy.loginfo("=" * 70)
        rospy.loginfo(f" {emoji} {title}")
        rospy.loginfo("=" * 70)

    def print_step(self, step_num, total_steps, title):
        """Affiche le titre d'une étape."""
        rospy.loginfo("")
        rospy.loginfo("-" * 70)
        rospy.loginfo(f" 📍 ÉTAPE {step_num}/{total_steps} : {title}")
        rospy.loginfo("-" * 70)

    def run_script(self, step_key):
        """
        Exécute un script Python dans un sous-processus.
        
        Args:
            step_key: Clé de l'étape dans STEP_CONFIG
            
        Returns:
            tuple: (success: bool, duration: float, output: str)
        """
        config = STEP_CONFIG[step_key]
        script_path = config["script"]
        timeout = config.get("timeout", 120)
        working_dir = config.get("working_dir", os.path.dirname(script_path))
        
        rospy.loginfo(f"📂 Répertoire de travail: {working_dir}")
        rospy.loginfo(f"📜 Script: {script_path}")
        rospy.loginfo(f"⏱️  Timeout: {timeout}s")
        
        # Vérifier que le script existe
        if not os.path.exists(script_path):
            rospy.logerr(f"❌ Script non trouvé: {script_path}")
            return False, 0, f"Script non trouvé: {script_path}"
        
        start_time = time.time()
        
        try:
            # Exécuter le script
            process = subprocess.Popen(
                ["python3", script_path],
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=os.environ.copy()
            )
            
            # Lire la sortie en temps réel
            output_lines = []
            while True:
                line = process.stdout.readline()
                if line:
                    line = line.rstrip()
                    output_lines.append(line)
                    rospy.loginfo(f"  │ {line}")
                    
                # Vérifier si le processus est terminé
                if process.poll() is not None:
                    # Lire les lignes restantes
                    for line in process.stdout.readlines():
                        line = line.rstrip()
                        output_lines.append(line)
                        rospy.loginfo(f"  │ {line}")
                    break
                    
                # Vérifier le timeout
                if time.time() - start_time > timeout:
                    process.terminate()
                    rospy.logerr(f"❌ Timeout après {timeout}s")
                    return False, time.time() - start_time, "Timeout"
                    
                # Vérifier si ROS est en train de s'arrêter
                if rospy.is_shutdown():
                    process.terminate()
                    return False, time.time() - start_time, "ROS shutdown"
            
            duration = time.time() - start_time
            output = "\n".join(output_lines)
            
            if process.returncode == 0:
                rospy.loginfo(f"✅ Succès en {duration:.2f}s")
                return True, duration, output
            else:
                rospy.logerr(f"❌ Échec avec code {process.returncode}")
                return False, duration, output
                
        except Exception as e:
            duration = time.time() - start_time
            rospy.logerr(f"❌ Exception: {e}")
            return False, duration, str(e)

    def execute_step(self, step_num, total_steps, step_key):
        """
        Exécute une étape du pipeline.
        
        Args:
            step_num: Numéro de l'étape
            total_steps: Nombre total d'étapes
            step_key: Clé de l'étape
            
        Returns:
            bool: True si l'étape a réussi
        """
        config = STEP_CONFIG[step_key]
        step_name = config["name"]
        description = config.get("description", "")
        
        self.print_step(step_num, total_steps, step_name)
        rospy.loginfo(f"📋 {description}")
        rospy.loginfo("")
        
        self.publish_step(step_name)
        self.publish_status("RUNNING", f"Exécution de {step_name}")
        
        success, duration, output = self.run_script(step_key)
        
        # Sauvegarder le résultat
        self.step_results[step_key] = {
            "success": success,
            "duration": duration,
            "step_name": step_name
        }
        
        if success:
            self.publish_status("SUCCESS", f"{step_name} terminé en {duration:.2f}s")
            rospy.loginfo("")
            rospy.loginfo(f"✅ {step_name} - TERMINÉ avec succès")
            return True
        else:
            self.publish_status("FAILED", f"{step_name} a échoué")
            rospy.logerr("")
            rospy.logerr(f"❌ {step_name} - ÉCHEC")
            return False

    def run_full_pipeline(self):
        """
        Exécute le pipeline complet en séquence.
        
        Returns:
            bool: True si toutes les étapes ont réussi
        """
        self.print_header("DÉMARRAGE DU PIPELINE COMPLET", "🚀")
        
        self.is_running = True
        self.start_time = time.time()
        self.step_results = {}
        
        steps = ["capture", "pipeline", "command"]
        total_steps = len(steps)
        
        rospy.loginfo(f"📌 {total_steps} étapes à exécuter:")
        for i, step in enumerate(steps, 1):
            rospy.loginfo(f"   {i}. {STEP_CONFIG[step]['name']}")
        rospy.loginfo("")
        
        # Exécuter chaque étape
        for i, step_key in enumerate(steps, 1):
            if rospy.is_shutdown():
                rospy.logwarn("⚠️  Arrêt ROS détecté")
                return False
                
            success = self.execute_step(i, total_steps, step_key)
            
            if not success:
                rospy.logerr(f"❌ Pipeline arrêté à l'étape {i}/{total_steps}")
                self.print_summary(False)
                return False
            
            # Pause entre les étapes
            if i < total_steps:
                rospy.loginfo("⏳ Pause avant l'étape suivante...")
                rospy.sleep(2.0)
        
        self.is_running = False
        self.print_summary(True)
        
        # Publier la fin du pipeline
        complete_msg = Bool()
        complete_msg.data = True
        self.complete_pub.publish(complete_msg)
        
        return True

    def run_single_step(self, step_key):
        """
        Exécute une seule étape du pipeline.
        
        Args:
            step_key: Clé de l'étape à exécuter
            
        Returns:
            bool: True si l'étape a réussi
        """
        if step_key not in STEP_CONFIG:
            rospy.logerr(f"❌ Étape inconnue: {step_key}")
            return False
            
        self.print_header(f"EXÉCUTION : {STEP_CONFIG[step_key]['name']}", "🎯")
        
        self.is_running = True
        self.start_time = time.time()
        self.step_results = {}
        
        success = self.execute_step(1, 1, step_key)
        
        self.is_running = False
        self.print_summary(success)
        
        return success

    def print_summary(self, overall_success):
        """Affiche le résumé de l'exécution."""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        self.print_header("RÉSUMÉ DE L'EXÉCUTION", "📊")
        
        if self.step_results:
            rospy.loginfo("⏱️  Temps par étape:")
            rospy.loginfo("-" * 50)
            
            for step_key, result in self.step_results.items():
                status = "✅" if result["success"] else "❌"
                rospy.loginfo(f"  {status} {result['step_name']:<30} : {result['duration']:6.2f}s")
            
            rospy.loginfo("-" * 50)
        
        rospy.loginfo(f"⏱️  Temps total : {total_time:.2f}s")
        rospy.loginfo("")
        
        if overall_success:
            rospy.loginfo("🎉 " + "=" * 50)
            rospy.loginfo("🎉  PIPELINE TERMINÉ AVEC SUCCÈS !")
            rospy.loginfo("🎉 " + "=" * 50)
            rospy.loginfo("")
            rospy.loginfo("📌 Fichiers générés:")
            rospy.loginfo("   - ~/ros_ws/data/rgb_images/       (images RGB)")
            rospy.loginfo("   - ~/ros_ws/data/depth_images/     (images profondeur)")
            rospy.loginfo("   - ~/ros_ws/workspace/pipeline/outputs/detections_input.json")
            rospy.loginfo("   - ~/ros_ws/workspace/pipeline/outputs/img_generated.png")
            rospy.loginfo("   - ~/ros_ws/workspace/pipeline/outputs/final_positions.json")
        else:
            rospy.logerr("❌ " + "=" * 50)
            rospy.logerr("❌  PIPELINE ÉCHOUÉ")
            rospy.logerr("❌ " + "=" * 50)
            rospy.logerr("⚠️  Vérifiez les logs ci-dessus pour identifier le problème")

    def wait_for_gazebo(self, timeout=30):
        """
        Attend que Gazebo soit prêt en vérifiant les topics ROS.
        
        Args:
            timeout: Temps maximum d'attente en secondes
            
        Returns:
            bool: True si Gazebo est prêt
        """
        rospy.loginfo("⏳ Vérification de la disponibilité de Gazebo...")
        
        required_topics = [
            '/xtion/rgb/image_raw',
            '/xtion/depth_registered/image_raw'
        ]
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if rospy.is_shutdown():
                return False
                
            published_topics = [topic for topic, _ in rospy.get_published_topics()]
            
            missing = [t for t in required_topics if t not in published_topics]
            
            if not missing:
                rospy.loginfo("✅ Gazebo est prêt - Tous les topics requis sont disponibles")
                return True
            
            rospy.loginfo(f"⏳ En attente des topics: {missing}")
            rospy.sleep(2.0)
        
        rospy.logwarn("⚠️  Timeout atteint - Gazebo peut ne pas être complètement prêt")
        return False


# ==============================================================================
# FONCTION PRINCIPALE
# ==============================================================================

def main():
    """Point d'entrée principal du script."""
    
    # Parser les arguments
    parser = argparse.ArgumentParser(
        description="Script d'automatisation du pipeline de réarrangement d'objets avec Tiago",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  rosrun scripts automation_node.py                  # Pipeline complet
  rosrun scripts automation_node.py --mode capture   # Capture uniquement
  rosrun scripts automation_node.py --mode pipeline  # Pipeline IA uniquement
  rosrun scripts automation_node.py --mode command   # Commande robot uniquement
  rosrun scripts automation_node.py --no-wait        # Sans attendre Gazebo
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['full', 'capture', 'pipeline', 'command'],
        default='full',
        help='Mode d\'exécution (default: full)'
    )
    
    parser.add_argument(
        '--no-wait',
        action='store_true',
        help='Ne pas attendre que Gazebo soit prêt'
    )
    
    # Parser les arguments (en ignorant les arguments ROS)
    args, _ = parser.parse_known_args()
    
    try:
        # Créer le nœud d'automatisation
        node = TiagoAutomationNode()
        
        # Attendre que Gazebo soit prêt (sauf si --no-wait)
        if not args.no_wait and args.mode in ['full', 'capture']:
            if not node.wait_for_gazebo(timeout=60):
                rospy.logwarn("⚠️  Gazebo peut ne pas être prêt, tentative de continuer...")
        
        # Exécuter selon le mode choisi
        if args.mode == 'full':
            success = node.run_full_pipeline()
        else:
            success = node.run_single_step(args.mode)
        
        # Retourner le code de sortie approprié
        sys.exit(0 if success else 1)
        
    except rospy.ROSInterruptException:
        rospy.loginfo("Interruption ROS")
        sys.exit(1)
    except Exception as e:
        rospy.logerr(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
