#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module client pour l'API Hugging Face.
Gère l'authentification et les interactions avec les modèles Hugging Face.
"""

import os
import sys
from typing import Optional


class HuggingFaceClient:
    """Client pour l'API Hugging Face."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialise le client Hugging Face.
        
        Args:
            token: Token d'authentification Hugging Face
        """
        self.token = token or os.environ.get('HF_TOKEN')
        self.authenticated = False
        
        if self.token and self.token.startswith('hf_'):
            self._authenticate()
    
    def _authenticate(self) -> bool:
        """
        S'authentifie avec Hugging Face Hub.
        
        Returns:
            True si l'authentification a réussi
        """
        try:
            # Import ici pour éviter les erreurs si pas installé
            from huggingface_hub import login, HfApi
            
            # Tenter la connexion
            login(token=self.token, add_to_git_credential=False)
            
            # Vérifier que le token fonctionne
            api = HfApi()
            user_info = api.whoami(token=self.token)
            
            print(f"[HuggingFaceClient] Authentifié en tant que: {user_info.get('name', 'Unknown')}")
            self.authenticated = True
            return True
            
        except ImportError:
            print("[HuggingFaceClient] AVERTISSEMENT: huggingface_hub n'est pas installé")
            print("[HuggingFaceClient] Les fonctionnalités d'authentification sont désactivées")
            return False
        except Exception as e:
            print(f"[HuggingFaceClient] Erreur d'authentification: {e}")
            self.authenticated = False
            return False
    
    def is_authenticated(self) -> bool:
        """
        Vérifie si le client est authentifié.
        
        Returns:
            True si authentifié
        """
        return self.authenticated
    
    def set_token(self, token: str) -> bool:
        """
        Définit un nouveau token et s'authentifie.
        
        Args:
            token: Nouveau token Hugging Face
            
        Returns:
            True si l'authentification a réussi
        """
        self.token = token
        return self._authenticate()
    
    def get_model_info(self, model_name: str) -> Optional[dict]:
        """
        Récupère les informations d'un modèle.
        
        Args:
            model_name: Nom du modèle (ex: "facebook/maskformer-swin-base-coco")
            
        Returns:
            Dictionnaire d'informations ou None si erreur
        """
        try:
            from huggingface_hub import HfApi
            
            api = HfApi()
            model_info = api.model_info(model_name, token=self.token)
            
            return {
                "id": model_info.id,
                "downloads": model_info.downloads,
                "likes": model_info.likes,
                "tags": model_info.tags
            }
        except ImportError:
            print("[HuggingFaceClient] huggingface_hub non installé")
            return None
        except Exception as e:
            print(f"[HuggingFaceClient] Erreur lors de la récupération des infos du modèle: {e}")
            return None
    
    @staticmethod
    def check_dependencies() -> dict:
        """
        Vérifie que toutes les dépendances sont installées.
        
        Returns:
            Dictionnaire avec le statut de chaque dépendance
        """
        dependencies = {
            'huggingface_hub': False,
            'transformers': False,
            'torch': False,
            'torchvision': False,
            'diffusers': False,
            'PIL': False,
            'cv2': False
        }
        
        for dep in dependencies.keys():
            try:
                if dep == 'PIL':
                    __import__('PIL')
                elif dep == 'cv2':
                    __import__('cv2')
                else:
                    __import__(dep)
                dependencies[dep] = True
            except ImportError:
                pass
        
        return dependencies
    
    @staticmethod
    def print_dependency_status():
        """Affiche le statut des dépendances."""
        deps = HuggingFaceClient.check_dependencies()
        
        print("\n" + "=" * 50)
        print("Statut des dépendances Hugging Face")
        print("=" * 50)
        
        for dep, installed in deps.items():
            status = "✓ Installé" if installed else "✗ Manquant"
            print(f"{dep:20s} : {status}")
        
        print("=" * 50 + "\n")
        
        all_installed = all(deps.values())
        if not all_installed:
            print("ATTENTION: Certaines dépendances sont manquantes.")
            print("Installez-les avec: pip install -r requirements.txt")
        else:
            print("Toutes les dépendances sont installées ✓")


if __name__ == "__main__":
    # Tests et vérifications
    print("Tests du module HuggingFaceClient\n")
    
    # Vérifier les dépendances
    HuggingFaceClient.print_dependency_status()
    
    # Tester l'authentification
    print("\nTest d'authentification...")
    client = HuggingFaceClient()
    
    if client.is_authenticated():
        print("✓ Authentification réussie")
    else:
        print("✗ Authentification échouée ou token manquant")
        print("Définissez la variable HF_TOKEN ou passez le token au constructeur")
