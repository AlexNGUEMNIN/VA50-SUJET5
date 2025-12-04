#!/usr/bin/env python3
"""
Script to download Hugging Face models for offline use.
Downloads DETR model for object detection of tableware.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from image_bridge.local_model_handler import download_model


def main():
    """Download models for offline use."""
    
    # Default model for object detection (good for tableware)
    models_to_download = [
        "facebook/detr-resnet-50",  # DETR - good general object detector
    ]
    
    # Cache directory
    cache_dir = os.path.expanduser("~/ros_ws/models")
    
    print("=" * 60)
    print("Téléchargement des modèles Hugging Face")
    print("=" * 60)
    print(f"Répertoire de cache: {cache_dir}")
    print()
    
    success_count = 0
    total_count = len(models_to_download)
    
    for i, model_name in enumerate(models_to_download, 1):
        print(f"[{i}/{total_count}] Téléchargement de {model_name}...")
        print("-" * 60)
        
        if download_model(model_name, cache_dir):
            print(f"✓ {model_name} téléchargé avec succès")
            success_count += 1
        else:
            print(f"✗ Échec du téléchargement de {model_name}")
        
        print()
    
    print("=" * 60)
    print(f"Téléchargement terminé: {success_count}/{total_count} modèles téléchargés")
    print("=" * 60)
    
    if success_count == total_count:
        print("\nTous les modèles sont prêts à être utilisés!")
        print(f"Emplacement: {cache_dir}")
        return 0
    else:
        print("\nCertains modèles n'ont pas pu être téléchargés.")
        print("Vérifiez votre connexion internet et réessayez.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
