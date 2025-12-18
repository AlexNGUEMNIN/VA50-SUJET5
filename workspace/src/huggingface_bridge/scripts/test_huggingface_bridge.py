#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le nœud Hugging Face Bridge.
Teste l'appel du service de traitement d'image.
"""

import rospy
import sys
import os
from pathlib import Path

# Import du service
from huggingface_bridge.srv import ProcessImage, ProcessImageRequest
from huggingface_bridge.srv import GetPositions, GetPositionsRequest


def test_process_image():
    """Teste le service de traitement d'image."""
    print("\n" + "=" * 70)
    print("Test du service /tiago/send_image_to_hf")
    print("=" * 70 + "\n")
    
    # Initialiser le nœud
    rospy.init_node('test_huggingface_bridge', anonymous=True)
    
    # Attendre que le service soit disponible
    service_name = '/tiago/send_image_to_hf'
    print(f"Attente du service {service_name}...")
    
    try:
        rospy.wait_for_service(service_name, timeout=10)
        print(f"✓ Service {service_name} disponible\n")
    except rospy.ROSException:
        print(f"✗ Timeout: Le service {service_name} n'est pas disponible")
        print("Assurez-vous que le nœud huggingface_bridge est lancé:")
        print("  roslaunch huggingface_bridge huggingface_bridge.launch")
        return False
    
    # Créer le proxy de service
    try:
        process_image = rospy.ServiceProxy(service_name, ProcessImage)
    except rospy.ServiceException as e:
        print(f"✗ Erreur lors de la création du proxy: {e}")
        return False
    
    # Chemin de l'image de test
    # Utiliser l'image exemple du pipeline si elle existe
    pipeline_dir = os.path.expanduser('~/ros_ws/workspace/pipeline')
    test_image = os.path.join(pipeline_dir, 'data', 'images', 'table_input.png')
    
    if not os.path.exists(test_image):
        print(f"✗ Image de test non trouvée: {test_image}")
        print("\nOptions:")
        print("1. Créez un lien symbolique vers une image existante:")
        print(f"   ln -s /path/to/your/image.png {test_image}")
        print("2. Ou modifiez ce script pour pointer vers votre image")
        return False
    
    print(f"Image de test: {test_image}\n")
    
    # Appeler le service
    print("Envoi de la requête de traitement...")
    print("(Cela peut prendre plusieurs minutes)\n")
    
    try:
        request = ProcessImageRequest()
        request.image_path = test_image
        
        response = process_image(request)
        
        print("\n" + "=" * 70)
        print("Résultat du traitement")
        print("=" * 70)
        
        if response.success:
            print("✓ Traitement réussi!\n")
            print(f"Message: {response.message}\n")
            print("Fichiers générés:")
            print(f"  - Image générée: {response.generated_image_path}")
            print(f"  - Détections: {response.detections_json_path}")
            print(f"  - Positions finales: {response.final_positions_json_path}")
            return True
        else:
            print(f"✗ Erreur: {response.message}")
            return False
            
    except rospy.ServiceException as e:
        print(f"✗ Erreur lors de l'appel du service: {e}")
        return False


def test_get_positions():
    """Teste le service de récupération des positions."""
    print("\n" + "=" * 70)
    print("Test du service /tiago/get_object_positions")
    print("=" * 70 + "\n")
    
    # Attendre que le service soit disponible
    service_name = '/tiago/get_object_positions'
    
    try:
        rospy.wait_for_service(service_name, timeout=5)
        print(f"✓ Service {service_name} disponible\n")
    except rospy.ROSException:
        print(f"✗ Service {service_name} non disponible")
        return False
    
    # Créer le proxy de service
    try:
        get_positions = rospy.ServiceProxy(service_name, GetPositions)
    except rospy.ServiceException as e:
        print(f"✗ Erreur: {e}")
        return False
    
    # Tester les positions initiales
    print("Récupération des positions initiales...")
    try:
        request = GetPositionsRequest()
        request.json_type = "initial"
        response = get_positions(request)
        
        if response.success:
            print("✓ Positions initiales récupérées\n")
            print("Contenu:")
            print(response.json_content)
        else:
            print(f"✗ Erreur: {response.json_content}")
            
    except rospy.ServiceException as e:
        print(f"✗ Erreur: {e}")
    
    # Tester les positions finales
    print("\nRécupération des positions finales...")
    try:
        request = GetPositionsRequest()
        request.json_type = "final"
        response = get_positions(request)
        
        if response.success:
            print("✓ Positions finales récupérées\n")
            print("Contenu:")
            print(response.json_content)
            return True
        else:
            print(f"✗ Erreur: {response.json_content}")
            return False
            
    except rospy.ServiceException as e:
        print(f"✗ Erreur: {e}")
        return False


def print_usage():
    """Affiche l'aide d'utilisation."""
    print("\nUtilisation:")
    print("  python3 test_huggingface_bridge.py [option]")
    print("\nOptions:")
    print("  --process     Teste le service de traitement d'image")
    print("  --positions   Teste le service de récupération de positions")
    print("  --all         Teste tous les services (par défaut)")
    print("  --help        Affiche cette aide")


def main():
    """Point d'entrée principal."""
    print("\n" + "#" * 70)
    print(" Test du Nœud Hugging Face Bridge")
    print("#" * 70)
    
    # Analyser les arguments
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        print_usage()
        return
    
    # Déterminer quels tests exécuter
    test_process = '--process' in args or '--all' in args or len(args) == 0
    test_pos = '--positions' in args or '--all' in args or len(args) == 0
    
    results = []
    
    # Exécuter les tests
    if test_process:
        try:
            result = test_process_image()
            results.append(("Traitement d'image", result))
        except Exception as e:
            print(f"\n✗ Erreur inattendue: {e}")
            import traceback
            traceback.print_exc()
            results.append(("Traitement d'image", False))
    
    if test_pos:
        try:
            result = test_get_positions()
            results.append(("Récupération de positions", result))
        except Exception as e:
            print(f"\n✗ Erreur inattendue: {e}")
            import traceback
            traceback.print_exc()
            results.append(("Récupération de positions", False))
    
    # Afficher le résumé
    print("\n" + "=" * 70)
    print("Résumé des tests")
    print("=" * 70)
    
    for test_name, success in results:
        status = "✓ SUCCÈS" if success else "✗ ÉCHEC"
        print(f"{test_name:30s} : {status}")
    
    print("=" * 70 + "\n")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("✓ Tous les tests ont réussi!")
    else:
        print("✗ Certains tests ont échoué")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterruption par l'utilisateur")
    except Exception as e:
        print(f"\n✗ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
