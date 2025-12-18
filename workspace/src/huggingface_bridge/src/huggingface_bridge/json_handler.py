#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des fichiers JSON pour le Hugging Face Bridge.
Fournit des utilitaires pour la lecture et l'écriture de fichiers JSON.
"""

import os
import json
from typing import Any, Optional, Dict, List
from pathlib import Path


class JSONHandler:
    """Gestionnaire de fichiers JSON."""
    
    def __init__(self):
        """Initialise le gestionnaire JSON."""
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
    def read_json(path: str) -> Optional[Any]:
        """
        Lit un fichier JSON.
        
        Args:
            path: Chemin du fichier JSON
            
        Returns:
            Contenu du JSON ou None si erreur
        """
        try:
            expanded_path = JSONHandler.expand_path(path)
            
            if not os.path.exists(expanded_path):
                print(f"[JSONHandler] Erreur: Fichier non trouvé {expanded_path}")
                return None
            
            with open(expanded_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
        except json.JSONDecodeError as e:
            print(f"[JSONHandler] Erreur de décodage JSON: {e}")
            return None
        except Exception as e:
            print(f"[JSONHandler] Erreur lors de la lecture du JSON: {e}")
            return None
    
    @staticmethod
    def write_json(data: Any, path: str, indent: int = 2) -> bool:
        """
        Écrit des données dans un fichier JSON.
        
        Args:
            data: Données à écrire
            path: Chemin du fichier de destination
            indent: Niveau d'indentation (par défaut: 2)
            
        Returns:
            True si succès, False sinon
        """
        try:
            expanded_path = JSONHandler.expand_path(path)
            
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(expanded_path), exist_ok=True)
            
            with open(expanded_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"[JSONHandler] Erreur lors de l'écriture du JSON: {e}")
            return False
    
    @staticmethod
    def json_to_string(data: Any, indent: int = 2) -> str:
        """
        Convertit des données en chaîne JSON.
        
        Args:
            data: Données à convertir
            indent: Niveau d'indentation
            
        Returns:
            Chaîne JSON
        """
        try:
            return json.dumps(data, indent=indent, ensure_ascii=False)
        except Exception as e:
            print(f"[JSONHandler] Erreur lors de la conversion en JSON: {e}")
            return "{}"
    
    @staticmethod
    def string_to_json(json_string: str) -> Optional[Any]:
        """
        Convertit une chaîne JSON en données.
        
        Args:
            json_string: Chaîne JSON
            
        Returns:
            Données parsées ou None si erreur
        """
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"[JSONHandler] Erreur de décodage JSON: {e}")
            return None
        except Exception as e:
            print(f"[JSONHandler] Erreur lors du parsing JSON: {e}")
            return None
    
    @staticmethod
    def validate_detections_json(data: Any) -> bool:
        """
        Valide le format d'un JSON de détections.
        
        Args:
            data: Données à valider
            
        Returns:
            True si le format est valide
        """
        if not isinstance(data, list):
            return False
        
        required_fields = {"id", "label", "x_pixel", "y_pixel", "theta"}
        
        for obj in data:
            if not isinstance(obj, dict):
                return False
            
            if not required_fields.issubset(obj.keys()):
                return False
        
        return True
    
    @staticmethod
    def validate_positions_json(data: Any) -> bool:
        """
        Valide le format d'un JSON de positions.
        
        Args:
            data: Données à valider
            
        Returns:
            True si le format est valide
        """
        if not isinstance(data, list):
            return False
        
        required_fields = {"label", "x_pixel", "y_pixel", "theta"}
        
        for obj in data:
            if not isinstance(obj, dict):
                return False
            
            if not required_fields.issubset(obj.keys()):
                return False
        
        return True
    
    @staticmethod
    def merge_json_data(json1: Any, json2: Any) -> Any:
        """
        Fusionne deux structures JSON.
        
        Args:
            json1: Premier JSON
            json2: Deuxième JSON
            
        Returns:
            JSON fusionné
        """
        if isinstance(json1, dict) and isinstance(json2, dict):
            result = json1.copy()
            result.update(json2)
            return result
        elif isinstance(json1, list) and isinstance(json2, list):
            return json1 + json2
        else:
            return json2
    
    @staticmethod
    def get_detections_summary(detections_path: str) -> Dict[str, Any]:
        """
        Génère un résumé des détections depuis un fichier JSON.
        
        Args:
            detections_path: Chemin du fichier de détections
            
        Returns:
            Dictionnaire de résumé
        """
        data = JSONHandler.read_json(detections_path)
        
        if data is None or not JSONHandler.validate_detections_json(data):
            return {"error": "Invalid detections file"}
        
        summary = {
            "total_objects": len(data),
            "labels": {},
            "objects": []
        }
        
        for obj in data:
            label = obj.get("label", "unknown")
            summary["labels"][label] = summary["labels"].get(label, 0) + 1
            
            summary["objects"].append({
                "id": obj.get("id"),
                "label": label,
                "position": {
                    "x": obj.get("x_pixel"),
                    "y": obj.get("y_pixel"),
                    "theta": obj.get("theta")
                }
            })
        
        return summary
    
    @staticmethod
    def file_exists(path: str) -> bool:
        """
        Vérifie si un fichier JSON existe.
        
        Args:
            path: Chemin du fichier
            
        Returns:
            True si le fichier existe
        """
        expanded_path = JSONHandler.expand_path(path)
        return os.path.exists(expanded_path) and os.path.isfile(expanded_path)


if __name__ == "__main__":
    # Tests basiques
    print("Tests du module JSONHandler")
    
    handler = JSONHandler()
    
    # Test de lecture/écriture
    test_data = [
        {
            "id": "obj_000",
            "label": "plate",
            "x_pixel": 100.0,
            "y_pixel": 200.0,
            "theta": 0.0
        }
    ]
    
    # Test de validation
    is_valid = handler.validate_detections_json(test_data)
    print(f"Validation des données: {is_valid}")
    
    # Test de conversion en string
    json_str = handler.json_to_string(test_data)
    print(f"Conversion en string:\n{json_str}")
