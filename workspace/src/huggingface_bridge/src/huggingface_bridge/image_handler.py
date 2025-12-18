#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des images pour le Hugging Face Bridge.
Fournit des utilitaires pour la lecture, écriture et conversion d'images.
"""

import os
import cv2
import base64
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Optional, Tuple


class ImageHandler:
    """Gestionnaire d'images pour la conversion et manipulation."""
    
    def __init__(self):
        """Initialise le gestionnaire d'images."""
        pass
    
    @staticmethod
    def expand_path(path: str) -> str:
        """
        Expanse un chemin avec ~ et variables d'environnement.
        
        Args:
            path: Chemin à expanser
            
        Returns:
            Chemin absolu expansé
        """
        return os.path.expanduser(os.path.expandvars(path))
    
    @staticmethod
    def validate_image_path(path: str) -> bool:
        """
        Vérifie qu'un chemin d'image existe et est lisible.
        
        Args:
            path: Chemin de l'image
            
        Returns:
            True si le fichier existe et est une image valide
        """
        expanded_path = ImageHandler.expand_path(path)
        
        if not os.path.exists(expanded_path):
            return False
        
        if not os.path.isfile(expanded_path):
            return False
        
        # Vérifier l'extension
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
        ext = os.path.splitext(expanded_path)[1].lower()
        
        return ext in valid_extensions
    
    @staticmethod
    def read_image(path: str) -> Optional[np.ndarray]:
        """
        Lit une image depuis un fichier.
        
        Args:
            path: Chemin de l'image
            
        Returns:
            Image au format numpy array (BGR) ou None si erreur
        """
        try:
            expanded_path = ImageHandler.expand_path(path)
            img = cv2.imread(expanded_path)
            
            if img is None:
                print(f"[ImageHandler] Erreur: Impossible de lire l'image {expanded_path}")
                return None
            
            return img
        except Exception as e:
            print(f"[ImageHandler] Erreur lors de la lecture de l'image: {e}")
            return None
    
    @staticmethod
    def write_image(img: np.ndarray, path: str) -> bool:
        """
        Écrit une image dans un fichier.
        
        Args:
            img: Image au format numpy array
            path: Chemin de destination
            
        Returns:
            True si succès, False sinon
        """
        try:
            expanded_path = ImageHandler.expand_path(path)
            
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(expanded_path), exist_ok=True)
            
            success = cv2.imwrite(expanded_path, img)
            
            if not success:
                print(f"[ImageHandler] Erreur: Impossible d'écrire l'image {expanded_path}")
                return False
            
            return True
        except Exception as e:
            print(f"[ImageHandler] Erreur lors de l'écriture de l'image: {e}")
            return False
    
    @staticmethod
    def resize_image(img: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
        """
        Redimensionne une image.
        
        Args:
            img: Image à redimensionner
            size: Tuple (largeur, hauteur)
            
        Returns:
            Image redimensionnée
        """
        return cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    
    @staticmethod
    def convert_to_rgb(img: np.ndarray) -> np.ndarray:
        """
        Convertit une image BGR en RGB.
        
        Args:
            img: Image BGR
            
        Returns:
            Image RGB
        """
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    @staticmethod
    def convert_to_bgr(img: np.ndarray) -> np.ndarray:
        """
        Convertit une image RGB en BGR.
        
        Args:
            img: Image RGB
            
        Returns:
            Image BGR
        """
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def image_to_base64(img: np.ndarray) -> str:
        """
        Convertit une image en base64.
        
        Args:
            img: Image au format numpy array
            
        Returns:
            Chaîne base64
        """
        _, buffer = cv2.imencode('.png', img)
        return base64.b64encode(buffer).decode('utf-8')
    
    @staticmethod
    def base64_to_image(b64_string: str) -> Optional[np.ndarray]:
        """
        Convertit une chaîne base64 en image.
        
        Args:
            b64_string: Chaîne base64
            
        Returns:
            Image au format numpy array ou None si erreur
        """
        try:
            img_data = base64.b64decode(b64_string)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            print(f"[ImageHandler] Erreur lors de la conversion base64: {e}")
            return None
    
    @staticmethod
    def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
        """
        Convertit une image PIL en OpenCV.
        
        Args:
            pil_img: Image PIL
            
        Returns:
            Image OpenCV (numpy array BGR)
        """
        # Convertir en RGB si nécessaire
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        # Convertir en numpy array
        img_array = np.array(pil_img)
        
        # Convertir RGB en BGR pour OpenCV
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        return img_bgr
    
    @staticmethod
    def cv2_to_pil(cv2_img: np.ndarray) -> Image.Image:
        """
        Convertit une image OpenCV en PIL.
        
        Args:
            cv2_img: Image OpenCV (numpy array BGR)
            
        Returns:
            Image PIL
        """
        # Convertir BGR en RGB
        img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        
        # Convertir en PIL
        pil_img = Image.fromarray(img_rgb)
        
        return pil_img
    
    @staticmethod
    def get_image_info(path: str) -> dict:
        """
        Récupère les informations d'une image.
        
        Args:
            path: Chemin de l'image
            
        Returns:
            Dictionnaire avec les informations de l'image
        """
        expanded_path = ImageHandler.expand_path(path)
        
        if not os.path.exists(expanded_path):
            return {"error": "File not found"}
        
        img = cv2.imread(expanded_path)
        
        if img is None:
            return {"error": "Cannot read image"}
        
        height, width = img.shape[:2]
        channels = img.shape[2] if len(img.shape) > 2 else 1
        
        return {
            "path": expanded_path,
            "width": width,
            "height": height,
            "channels": channels,
            "size": os.path.getsize(expanded_path),
            "format": os.path.splitext(expanded_path)[1]
        }


if __name__ == "__main__":
    # Tests basiques
    print("Tests du module ImageHandler")
    
    handler = ImageHandler()
    
    # Test d'expansion de chemin
    test_path = "~/test.png"
    expanded = handler.expand_path(test_path)
    print(f"Expansion de chemin: {test_path} -> {expanded}")
