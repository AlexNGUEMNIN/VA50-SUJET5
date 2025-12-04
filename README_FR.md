# Guide Complet : Détection d'Objets avec Modèle Hugging Face Local pour Tiago

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du système](#architecture-du-système)
3. [Prérequis](#prérequis)
4. [Installation](#installation)
5. [Téléchargement du modèle](#téléchargement-du-modèle)
6. [Utilisation](#utilisation)
7. [Tests et Validation](#tests-et-validation)
8. [Structure des Données](#structure-des-données)
9. [Dépannage](#dépannage)
10. [Paramètres Avancés](#paramètres-avancés)

---

## 🎯 Vue d'ensemble

Ce système permet au robot Tiago de :
1. **Capturer** des images panoramiques de son environnement (table avec couverts)
2. **Détecter** automatiquement les objets (fourchettes, couteaux, assiettes, etc.)
3. **Analyser** leur position avec un modèle Hugging Face **en local** (sans connexion internet)
4. **Communiquer** les résultats via des nœuds ROS pour que Tiago puisse organiser les objets

### ✨ Nouveautés

- ✅ **Modèle local** : Fonctionne sans connexion internet après téléchargement initial
- ✅ **Détection de couverts** : Spécialisé pour fourchettes, couteaux, cuillères, assiettes
- ✅ **Intégration ROS** : Communication native avec les systèmes du robot
- ✅ **Traitement par lot** : Analyse toutes les images capturées en une seule commande
- ✅ **Visualisation** : Images annotées avec boîtes de détection

---

## 🏗️ Architecture du système

```
┌─────────────────────────────────────────────────────────────┐
│                     ROBOT TIAGO (Gazebo)                    │
│                                                               │
│  ┌─────────────┐                                             │
│  │  Caméra     │ ──► Capture d'images panoramiques          │
│  │  (Xtion)    │     (capture.py)                            │
│  └─────────────┘                                             │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────────────────────────────┐                    │
│  │  Images sauvegardées                │                    │
│  │  ~/ros_ws/data/images/*.png         │                    │
│  └─────────────────────────────────────┘                    │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              NŒUD DE TRAITEMENT LOCAL                        │
│           (image_processing_node.py)                         │
│                                                               │
│  ┌──────────────────────────────────────────┐               │
│  │  Modèle Hugging Face (DETR)              │               │
│  │  ~/ros_ws/models/facebook_detr-resnet-50 │               │
│  │  • Détection d'objets                    │               │
│  │  • Classification                        │               │
│  │  • Calcul de positions                   │               │
│  └──────────────────────────────────────────┘               │
│                        │                                      │
│                        ▼                                      │
│  ┌──────────────────────────────────────────┐               │
│  │  Résultats de détection                  │               │
│  │  • Objets détectés avec positions        │               │
│  │  • Images annotées                       │               │
│  │  • Fichiers JSON                         │               │
│  └──────────────────────────────────────────┘               │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    TOPICS ROS                                │
│                                                               │
│  • /tiago/object_detections  (JSON des objets détectés)     │
│  • /tiago/object_poses       (Positions pour RViz)          │
│  • /tiago/annotated_image    (Image avec annotations)       │
│                                                               │
│  Service:                                                    │
│  • /tiago/process_captured_images (Traiter toutes images)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Prérequis

### Système
- Ubuntu 20.04 (ou compatible)
- ROS Noetic
- Python 3.8+
- Docker (si utilisation du conteneur Tiago)

### Matériel
- **CPU** : Processeur moderne (Intel i5/i7 ou AMD équivalent)
- **RAM** : Minimum 8 GB (16 GB recommandé)
- **Disque** : ~5 GB d'espace libre pour les modèles
- **GPU** : Optionnel mais recommandé (NVIDIA avec CUDA pour accélération)

---

## 🔧 Installation

### Étape 1 : Accéder au conteneur Docker

```bash
# Depuis votre machine hôte
./client.sh
```

Une fois dans le conteneur :

```bash
cd ~/ros_ws
```

### Étape 2 : Installer les dépendances Python

```bash
cd ~/ros_ws/src/image_bridge
pip3 install -r requirements.txt
```

**Note** : Si vous avez un GPU NVIDIA avec CUDA :

```bash
# Installer PyTorch avec support CUDA
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Étape 3 : Compiler le workspace ROS

```bash
cd ~/ros_ws
catkin_make
source devel/setup.bash
```

---

## 📥 Téléchargement du modèle

Le modèle **DETR (DEtection TRansformer)** de Facebook est utilisé pour la détection d'objets. Il est excellent pour détecter les couverts et la vaisselle.

### Téléchargement automatique

```bash
cd ~/ros_ws/src/image_bridge/scripts
python3 download_model.py
```

Cela téléchargera le modèle dans `~/ros_ws/models/facebook_detr-resnet-50/`

### Téléchargement manuel (si nécessaire)

```python
# Dans un terminal Python
from image_bridge.local_model_handler import download_model
download_model("facebook/detr-resnet-50", "~/ros_ws/models")
```

### Vérification du téléchargement

```bash
ls -lh ~/ros_ws/models/facebook_detr-resnet-50/
```

Vous devriez voir :
- `config.json`
- `preprocessor_config.json`
- `pytorch_model.bin` (fichier volumineux, ~160 MB)

---

## 🚀 Utilisation

### Scénario complet : De la capture à la détection

#### 1. Démarrer la simulation Gazebo avec Tiago

Dans un premier terminal du conteneur :

```bash
source /opt/pal/gallium/setup.bash
roslaunch tiago_gazebo tiago_gazebo.launch world:=pick_and_place
```

**Attendez** que Gazebo démarre complètement (cela peut prendre 1-2 minutes).

#### 2. Capturer les images panoramiques

Dans un second terminal :

```bash
cd ~/ros_ws/scripts
python3 capture.py
```

Le robot va :
- Déplacer sa tête et son torse
- Prendre 4 photos sous différents angles
- Sauvegarder les images dans `~/ros_ws/data/images/`

Exemple de sortie :
```
[INFO] Début de la capture panoramique
[INFO] Position 1/4
[INFO] Tête déplacée: pan=0.0, tilt=-0.7
[INFO] Image sauvegardée: /home/pal/ros_ws/data/images/table_position_1_20251204_104437.png
...
[INFO] Capture terminée
```

#### 3. Démarrer le nœud de traitement d'images

Dans un troisième terminal :

```bash
source ~/ros_ws/devel/setup.bash
roslaunch image_bridge image_processing.launch
```

Le nœud va :
- Charger le modèle local
- S'abonner aux topics de caméra
- Être prêt à traiter les images

Sortie attendue :
```
[INFO] Initialisation du nœud de traitement d'images...
[INFO] Chargement du modèle: facebook/detr-resnet-50
[INFO] Loading model from local cache: /home/pal/ros_ws/models/facebook_detr-resnet-50
[INFO] Detection model loaded successfully on cpu
[INFO] Nœud de traitement d'images initialisé avec succès!
```

#### 4. Traiter les images capturées

Dans un quatrième terminal :

```bash
source ~/ros_ws/devel/setup.bash
rosservice call /tiago/process_captured_images "{}"
```

Le système va :
- Charger toutes les images PNG de `~/ros_ws/data/images/`
- Détecter les objets (fourchettes, couteaux, assiettes, etc.)
- Sauvegarder les images annotées dans `~/ros_ws/data/results/`
- Créer un fichier JSON avec tous les résultats

Exemple de sortie :
```
success: True
message: "Traitement terminé: 4 images traitées. Résultats sauvegardés dans /home/pal/ros_ws/data/results/detection_results_20251204_110530.json"
```

---

## 📊 Structure des Données

### Images capturées

Emplacement : `~/ros_ws/data/images/`

Format : `table_position_X_YYYYMMDD_HHMMSS.png`

### Résultats de détection

#### Fichier JSON

Emplacement : `~/ros_ws/data/results/detection_results_TIMESTAMP.json`

Structure :
```json
[
  {
    "image": "table_position_1_20251204_104437.png",
    "detections": [
      {
        "label": "fork",
        "score": 0.95,
        "center_x": 320.5,
        "center_y": 240.3,
        "normalized_x": 0.5,
        "normalized_y": 0.375,
        "width": 45.2,
        "height": 120.8
      },
      {
        "label": "plate",
        "score": 0.89,
        "center_x": 400.0,
        "center_y": 300.0,
        "normalized_x": 0.625,
        "normalized_y": 0.469,
        "width": 150.0,
        "height": 150.0
      }
    ],
    "organized": {
      "cutlery_count": 2,
      "plates_count": 1,
      "cups_count": 0
    }
  }
]
```

#### Images annotées

Emplacement : `~/ros_ws/data/results/annotated_*.png`

Images avec :
- Boîtes de détection vertes
- Labels et scores de confiance
- Format identique aux images d'origine

---

## 🔍 Tests et Validation

### Test 1 : Vérifier que le modèle est chargé

```bash
# Dans un terminal Python avec ROS initialisé
python3 << EOF
from image_bridge.local_model_handler import LocalModelHandler
handler = LocalModelHandler()
success = handler.load_detection_model()
print(f"Modèle chargé : {success}")
info = handler.get_model_info()
print(f"Info : {info}")
EOF
```

### Test 2 : Traiter une seule image

```python
#!/usr/bin/env python3
import cv2
from image_bridge.local_model_handler import LocalModelHandler

# Charger le modèle
handler = LocalModelHandler()
handler.load_detection_model()

# Charger une image
image_path = "/home/pal/ros_ws/data/images/table_position_1_20251204_104437.png"
image = cv2.imread(image_path)
rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Détecter
detections = handler.detect_objects(rgb_image, confidence_threshold=0.7)

# Afficher les résultats
print(f"Objets détectés : {len(detections)}")
for det in detections:
    print(f"  - {det['label']}: {det['score']:.2f}")
```

### Test 3 : Surveiller les topics ROS

```bash
# Terminal 1 : Écouter les détections
rostopic echo /tiago/object_detections

# Terminal 2 : Écouter les poses
rostopic echo /tiago/object_poses

# Terminal 3 : Visualiser l'image annotée
rosrun image_view image_view image:=/tiago/annotated_image
```

### Test 4 : Validation avec des images de test

Créez un dossier de test avec des images de couverts :

```bash
mkdir -p ~/ros_ws/data/test_images
# Copiez quelques images de test ici
```

Modifiez temporairement le paramètre dans le launch file et relancez.

---

## 🛠️ Dépannage

### Problème : Le modèle ne se télécharge pas

**Solution** :
```bash
# Vérifier la connexion internet
ping huggingface.co

# Essayer de télécharger manuellement
pip3 install transformers[torch]
python3 -c "from transformers import DetrForObjectDetection; DetrForObjectDetection.from_pretrained('facebook/detr-resnet-50')"
```

### Problème : Erreur "CUDA out of memory"

**Solution** : Forcer l'utilisation du CPU
```bash
export CUDA_VISIBLE_DEVICES=""
```

Ou modifier dans le code :
```python
self.device = torch.device("cpu")  # Force CPU
```

### Problème : Aucun objet détecté

**Solutions** :
1. Réduire le seuil de confiance :
   ```xml
   <param name="confidence_threshold" value="0.5" />
   ```

2. Vérifier l'éclairage de la scène dans Gazebo
3. Vérifier que les objets sont visibles dans les images capturées

### Problème : Le service ne répond pas

**Solution** :
```bash
# Vérifier que le nœud tourne
rosnode list | grep image_processing

# Vérifier les services disponibles
rosservice list | grep tiago

# Redémarrer le nœud
rosnode kill /image_processing_node
roslaunch image_bridge image_processing.launch
```

### Problème : Images capturées sont noires ou vides

**Solution** :
```bash
# Vérifier que la caméra publie
rostopic hz /xtion/rgb/image_raw

# Vérifier le contenu
rosrun image_view image_view image:=/xtion/rgb/image_raw
```

---

## ⚙️ Paramètres Avancés

### Modifier le modèle de détection

Dans `image_processing.launch` :
```xml
<!-- Utiliser un modèle plus léger (plus rapide, moins précis) -->
<param name="detection_model" value="facebook/detr-resnet-50" />

<!-- Ou un modèle plus lourd (plus lent, plus précis) -->
<!-- <param name="detection_model" value="facebook/detr-resnet-101" /> -->
```

### Ajuster les classes détectées

Dans `local_model_handler.py`, modifiez :
```python
self.target_classes = [
    'fork', 'knife', 'spoon',
    'bowl', 'cup', 'plate', 'dish',
    'bottle', 'wine glass', 'dining table',
    # Ajoutez vos propres classes ici
]
```

### Optimiser les performances

#### Pour CPU lent :
```python
# Réduire la résolution des images
def process_image(self, cv_image):
    # Redimensionner avant traitement
    height, width = cv_image.shape[:2]
    if width > 640:
        scale = 640 / width
        cv_image = cv2.resize(cv_image, None, fx=scale, fy=scale)
    # ... reste du code
```

#### Pour GPU :
```bash
# Installer PyTorch avec CUDA
pip3 uninstall torch torchvision
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Traitement en temps réel vs Batch

Le nœud supporte les deux modes :

**Temps réel** : S'abonne à `/xtion/rgb/image_raw` et traite en continu
**Batch** : Utilise le service `/tiago/process_captured_images`

Pour désactiver le temps réel (économiser des ressources) :
```xml
<!-- Commenter la ligne camera_topic dans le launch file -->
<!-- <param name="camera_topic" value="/xtion/rgb/image_raw" /> -->
```

---

## 📚 Références

### Modèles disponibles

| Modèle | Taille | Vitesse | Précision | Recommandé pour |
|--------|--------|---------|-----------|-----------------|
| `facebook/detr-resnet-50` | ~160 MB | Moyenne | Bonne | Usage général ✅ |
| `facebook/detr-resnet-101` | ~250 MB | Lente | Excellente | Haute précision |
| `hustvl/yolos-tiny` | ~25 MB | Rapide | Moyenne | CPU limité |

### Topics ROS créés

| Topic | Type | Description |
|-------|------|-------------|
| `/tiago/object_detections` | `std_msgs/String` | JSON des objets détectés |
| `/tiago/object_poses` | `geometry_msgs/PoseArray` | Positions 2D normalisées |
| `/tiago/annotated_image` | `sensor_msgs/Image` | Image avec annotations |

### Services ROS créés

| Service | Type | Description |
|---------|------|-------------|
| `/tiago/process_captured_images` | `std_srvs/Trigger` | Traiter toutes les images |

---

## 🎓 Utilisation Avancée

### Intégration avec le système de planification

Pour que Tiago utilise les détections pour organiser les objets :

```python
#!/usr/bin/env python3
import rospy
import json
from std_msgs.msg import String
from geometry_msgs.msg import PoseArray

def detection_callback(msg):
    """Recevoir les détections et planifier les actions."""
    data = json.loads(msg.data)
    objects = data['objects']
    
    # Filtrer par type
    forks = [o for o in objects if 'fork' in o['label'].lower()]
    knives = [o for o in objects if 'knife' in o['label'].lower()]
    plates = [o for o in objects if 'plate' in o['label'].lower()]
    
    # Planifier l'organisation
    # Par exemple : placer les fourchettes à gauche, couteaux à droite
    for fork in forks:
        target_position = (fork['normalized_x'] - 0.1, fork['normalized_y'])
        # Envoyer commande au robot...
        print(f"Déplacer fourchette vers {target_position}")

rospy.init_node('object_organizer')
rospy.Subscriber('/tiago/object_detections', String, detection_callback)
rospy.spin()
```

### Visualisation dans RViz

Créer un fichier de configuration RViz (`detection_view.rviz`) :
1. Ajouter un display `Image` pour `/tiago/annotated_image`
2. Ajouter un display `PoseArray` pour `/tiago/object_poses`
3. Sauvegarder la configuration

---

## 📞 Support et Contribution

Pour toute question ou problème :
1. Vérifiez les logs ROS : `cat ~/.ros/log/latest/*.log`
2. Consultez la section Dépannage ci-dessus
3. Créez une issue sur le dépôt GitHub avec les logs

---

## 📄 Licence

MIT License - Voir LICENSE pour plus de détails

---

**Auteur** : Alex NGUEMNIN  
**Projet** : VA50-SUJET5  
**Date** : Décembre 2024  
**Version** : 1.0
