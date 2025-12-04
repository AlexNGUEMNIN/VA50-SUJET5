# Téléchargement des Modèles / Model Download

## Téléchargement Automatique / Automatic Download

Pour télécharger automatiquement tous les modèles nécessaires :

```bash
cd ~/ros_ws/src/image_bridge/scripts
python3 download_model.py
```

## Téléchargement Manuel / Manual Download

### Méthode 1: En Python

```python
# Ouvrir un interpréteur Python
python3

# Dans l'interpréteur :
import sys
from pathlib import Path

# Ajouter le chemin du module
sys.path.insert(0, str(Path.home() / "ros_ws/src/image_bridge/src"))

# Importer et utiliser la fonction
from image_bridge.local_model_handler import download_model

# Télécharger le modèle
download_model("facebook/detr-resnet-50", "~/ros_ws/models")
```

### Méthode 2: Utiliser le script

```bash
cd ~/ros_ws/src/image_bridge/scripts
python3 download_model.py
```

## Prérequis / Prerequisites

Assurez-vous que les dépendances Python sont installées :

```bash
cd ~/ros_ws/src/image_bridge
pip3 install -r requirements.txt
```

## Dépannage / Troubleshooting

### Erreur "ModuleNotFoundError: No module named 'image_bridge'"

Vérifiez que vous exécutez le script depuis le bon répertoire et que le chemin vers `src` est correct.

### Erreur "No module named 'torch'" ou similaire

Installez les dépendances :
```bash
pip3 install -r ~/ros_ws/src/image_bridge/requirements.txt
```

### Erreur de connexion réseau

Assurez-vous d'avoir une connexion Internet active pour télécharger les modèles depuis Hugging Face.
