#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validation de l'installation du package Hugging Face Bridge.
Vérifie que toutes les dépendances sont installées et que les chemins sont corrects.
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Vérifie la version de Python."""
    print("\n1. Version Python")
    print("-" * 50)
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ✗ Python 3.8+ requis")
        return False
    else:
        print("   ✓ Version compatible")
        return True


def check_dependencies():
    """Vérifie les dépendances Python."""
    print("\n2. Dépendances Python")
    print("-" * 50)
    
    dependencies = {
        'rospy': 'ROS Python',
        'yaml': 'PyYAML',
        'cv2': 'OpenCV',
        'PIL': 'Pillow',
        'numpy': 'NumPy',
        'torch': 'PyTorch',
        'torchvision': 'TorchVision',
        'transformers': 'Transformers',
        'diffusers': 'Diffusers',
        'huggingface_hub': 'Hugging Face Hub'
    }
    
    results = {}
    for module, name in dependencies.items():
        try:
            if module == 'yaml':
                __import__('yaml')
            else:
                __import__(module)
            results[name] = True
            print(f"   ✓ {name:20s} : Installé")
        except ImportError:
            results[name] = False
            print(f"   ✗ {name:20s} : Manquant")
    
    return all(results.values())


def check_ros_environment():
    """Vérifie l'environnement ROS."""
    print("\n3. Environnement ROS")
    print("-" * 50)
    
    ros_vars = ['ROS_DISTRO', 'ROS_MASTER_URI', 'ROS_PACKAGE_PATH']
    all_set = True
    
    for var in ros_vars:
        value = os.environ.get(var)
        if value:
            print(f"   ✓ {var:20s} : {value}")
        else:
            print(f"   ✗ {var:20s} : Non défini")
            all_set = False
    
    return all_set


def check_package_structure():
    """Vérifie la structure du package."""
    print("\n4. Structure du Package")
    print("-" * 50)
    
    # Trouver le répertoire du package
    script_dir = Path(__file__).resolve().parent
    pkg_dir = script_dir.parent
    
    required_files = [
        'CMakeLists.txt',
        'package.xml',
        'README.md',
        'requirements.txt',
        'config/huggingface_config.yaml',
        'launch/huggingface_bridge.launch',
        'scripts/huggingface_bridge_node.py',
        'srv/ProcessImage.srv',
        'srv/GetPositions.srv',
        'src/huggingface_bridge/__init__.py',
        'src/huggingface_bridge/image_handler.py',
        'src/huggingface_bridge/json_handler.py',
        'src/huggingface_bridge/huggingface_client.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = pkg_dir / file_path
        if full_path.exists():
            print(f"   ✓ {file_path}")
        else:
            print(f"   ✗ {file_path} (manquant)")
            all_exist = False
    
    return all_exist


def check_pipeline_structure():
    """Vérifie la structure du pipeline."""
    print("\n5. Structure du Pipeline")
    print("-" * 50)
    
    pipeline_dir = Path.home() / 'ros_ws' / 'workspace' / 'pipeline'
    
    if not pipeline_dir.exists():
        # Essayer un chemin alternatif
        pipeline_dir = Path('/home/runner/work/VA50-SUJET5/VA50-SUJET5/workspace/pipeline')
    
    print(f"   Répertoire: {pipeline_dir}")
    
    required_items = [
        'run_pipeline.py',
        'src/detect_objects.py',
        'src/img-gene.py',
        'src/generated_image_to_positions.py',
        'src/utils.py',
        'data/images',
        'outputs'
    ]
    
    all_exist = True
    for item_path in required_items:
        full_path = pipeline_dir / item_path
        if full_path.exists():
            print(f"   ✓ {item_path}")
        else:
            print(f"   ✗ {item_path} (manquant)")
            all_exist = False
    
    return all_exist


def check_hf_token():
    """Vérifie le token Hugging Face."""
    print("\n6. Token Hugging Face")
    print("-" * 50)
    
    # Chercher dans les variables d'environnement
    token_env = os.environ.get('HF_TOKEN')
    
    # Chercher dans le fichier de config
    script_dir = Path(__file__).resolve().parent
    config_file = script_dir.parent / 'config' / 'huggingface_config.yaml'
    
    token_config = None
    if config_file.exists():
        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                token_config = config.get('huggingface', {}).get('token')
        except Exception as e:
            print(f"   ✗ Erreur lecture config: {e}")
    
    if token_env:
        print(f"   ✓ HF_TOKEN (env) : {token_env[:10]}...")
        return True
    elif token_config and not token_config.startswith('${'):
        print(f"   ✓ Token (config) : {token_config[:10]}...")
        return True
    else:
        print("   ✗ Token non trouvé")
        print("   Définissez HF_TOKEN ou modifiez config/huggingface_config.yaml")
        return False


def print_summary(results):
    """Affiche le résumé des vérifications."""
    print("\n" + "=" * 50)
    print("RÉSUMÉ")
    print("=" * 50)
    
    for check_name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {check_name}")
    
    print("=" * 50)
    
    if all(result for _, result in results):
        print("✓ Toutes les vérifications ont réussi!")
        print("\nVous pouvez maintenant:")
        print("  1. Compiler le workspace: catkin_make")
        print("  2. Sourcer: source devel/setup.bash")
        print("  3. Lancer: roslaunch huggingface_bridge huggingface_bridge.launch")
        return True
    else:
        print("✗ Certaines vérifications ont échoué")
        print("\nConsultez le README.md pour l'installation complète")
        return False


def main():
    """Point d'entrée principal."""
    print("\n" + "=" * 50)
    print("VALIDATION DU PACKAGE HUGGING FACE BRIDGE")
    print("=" * 50)
    
    results = []
    
    # Exécuter les vérifications
    results.append(("Python 3.8+", check_python_version()))
    results.append(("Dépendances Python", check_dependencies()))
    results.append(("Environnement ROS", check_ros_environment()))
    results.append(("Structure du package", check_package_structure()))
    results.append(("Structure du pipeline", check_pipeline_structure()))
    results.append(("Token Hugging Face", check_hf_token()))
    
    # Afficher le résumé
    all_ok = print_summary(results)
    
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterruption par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
