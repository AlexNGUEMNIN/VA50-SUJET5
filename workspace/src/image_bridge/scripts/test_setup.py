#!/usr/bin/env python3
"""
Test script to validate the local model setup.
Tests model loading, inference, and basic functionality.
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test that all required packages can be imported."""
    print("=" * 60)
    print("TEST 1: Imports")
    print("=" * 60)
    
    try:
        import torch
        print(f"✓ PyTorch {torch.__version__}")
        print(f"  CUDA disponible: {torch.cuda.is_available()}")
        
        import transformers
        print(f"✓ Transformers {transformers.__version__}")
        
        import cv2
        print(f"✓ OpenCV {cv2.__version__}")
        
        import PIL
        print(f"✓ Pillow {PIL.__version__}")
        
        from image_bridge.local_model_handler import LocalModelHandler
        print("✓ LocalModelHandler importé")
        
        print("\n✅ Tous les imports réussis\n")
        return True
        
    except ImportError as e:
        print(f"\n❌ Erreur d'import: {e}\n")
        return False


def test_model_loading():
    """Test loading the detection model."""
    print("=" * 60)
    print("TEST 2: Chargement du modèle")
    print("=" * 60)
    
    try:
        from image_bridge.local_model_handler import LocalModelHandler
        
        handler = LocalModelHandler()
        print(f"✓ Handler créé")
        print(f"  Cache dir: {handler.model_cache_dir}")
        
        model_path = handler.model_cache_dir / "facebook_detr-resnet-50"
        if model_path.exists():
            print(f"✓ Modèle trouvé dans le cache: {model_path}")
        else:
            print(f"⚠ Modèle non trouvé localement, sera téléchargé")
        
        success = handler.load_detection_model()
        
        if success:
            print("✓ Modèle chargé avec succès")
            
            info = handler.get_model_info()
            print(f"\nInformations du modèle:")
            print(f"  Device: {info['device']}")
            print(f"  Classes cibles: {len(info['target_classes'])} types d'objets")
            
            print("\n✅ Test de chargement réussi\n")
            return True, handler
        else:
            print("\n❌ Échec du chargement du modèle\n")
            return False, None
            
    except Exception as e:
        print(f"\n❌ Erreur lors du chargement: {e}\n")
        import traceback
        traceback.print_exc()
        return False, None


def test_dummy_detection(handler):
    """Test detection on a dummy image."""
    print("=" * 60)
    print("TEST 3: Détection sur image de test")
    print("=" * 60)
    
    try:
        import numpy as np
        from PIL import Image
        
        # Create a dummy RGB image
        dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        pil_image = Image.fromarray(dummy_image)
        
        print("✓ Image de test créée (640x480)")
        
        # Run detection
        print("  Exécution de la détection...")
        detections = handler.detect_objects(pil_image, confidence_threshold=0.9)
        
        print(f"✓ Détection complétée")
        print(f"  Objets détectés: {len(detections)}")
        
        if len(detections) > 0:
            print("\n  Note: Détections sur image aléatoire (probablement faux positifs)")
        
        print("\n✅ Test de détection réussi\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la détection: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_real_image(handler):
    """Test detection on a real image if available."""
    print("=" * 60)
    print("TEST 4: Détection sur image réelle (optionnel)")
    print("=" * 60)
    
    images_dir = Path.home() / "ros_ws" / "data" / "images"
    
    if not images_dir.exists():
        print(f"⚠ Répertoire d'images non trouvé: {images_dir}")
        print("  Skipping (normal si aucune image n'a été capturée)")
        return True
    
    image_files = list(images_dir.glob("*.png"))
    
    if not image_files:
        print(f"⚠ Aucune image PNG trouvée dans {images_dir}")
        print("  Skipping (normal si aucune image n'a été capturée)")
        return True
    
    try:
        import cv2
        
        test_image = str(image_files[0])
        print(f"✓ Image trouvée: {Path(test_image).name}")
        
        # Load image
        cv_image = cv2.imread(test_image)
        if cv_image is None:
            print(f"❌ Impossible de charger l'image")
            return False
        
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        print(f"✓ Image chargée: {cv_image.shape[1]}x{cv_image.shape[0]}")
        
        # Run detection
        print("  Exécution de la détection...")
        detections = handler.detect_objects(rgb_image, confidence_threshold=0.7)
        
        print(f"✓ Détection complétée")
        print(f"  Objets détectés: {len(detections)}")
        
        if detections:
            print("\n  Détails des objets:")
            for i, det in enumerate(detections[:5], 1):  # Show max 5
                print(f"    {i}. {det['label']}: {det['score']:.2f}")
            
            if len(detections) > 5:
                print(f"    ... et {len(detections) - 5} autres")
        
        print("\n✅ Test sur image réelle réussi\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_directories():
    """Test that required directories exist."""
    print("=" * 60)
    print("TEST 5: Vérification des répertoires")
    print("=" * 60)
    
    dirs_to_check = [
        Path.home() / "ros_ws" / "models",
        Path.home() / "ros_ws" / "data" / "images",
        Path.home() / "ros_ws" / "data" / "results",
    ]
    
    all_ok = True
    for dir_path in dirs_to_check:
        if dir_path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"⚠ Créé: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    print("\n✅ Tous les répertoires sont prêts\n")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("VALIDATION DE LA CONFIGURATION")
    print("Test du système de détection d'objets avec modèle local")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Test 1: Imports
    results['imports'] = test_imports()
    
    # Test 2: Model loading
    if results['imports']:
        results['model_loading'], handler = test_model_loading()
    else:
        print("⏭️  Skipping tests suivants (imports échoués)\n")
        return 1
    
    # Test 3: Dummy detection
    if results['model_loading'] and handler is not None:
        results['dummy_detection'] = test_dummy_detection(handler)
    else:
        print("⏭️  Skipping tests suivants (modèle non chargé)\n")
        return 1
    
    # Test 4: Real image (optional)
    if results['dummy_detection']:
        results['real_image'] = test_real_image(handler)
    
    # Test 5: Directories
    results['directories'] = test_directories()
    
    # Summary
    print("=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 60)
    
    if all(results.values()):
        print("\n🎉 Tous les tests sont passés!")
        print("Le système est prêt à être utilisé.\n")
        print("Prochaines étapes:")
        print("  1. Capturer des images avec: python3 ~/ros_ws/scripts/capture.py")
        print("  2. Lancer le nœud: roslaunch image_bridge image_processing.launch")
        print("  3. Traiter les images: rosservice call /tiago/process_captured_images")
        return 0
    else:
        print("\n⚠️  Certains tests ont échoué.")
        print("Consultez les messages d'erreur ci-dessus.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
