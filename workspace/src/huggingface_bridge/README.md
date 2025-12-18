# Hugging Face Bridge - Nœud ROS de Communication Tiago ↔ Hugging Face

## 📋 Description

Ce package ROS fournit un pont de communication bidirectionnelle entre le robot Tiago (simulation Gazebo) et les modèles Hugging Face pour le réarrangement autonome d'objets. Il orchestre le pipeline complet de traitement d'images, depuis la détection d'objets jusqu'à la génération de positions cibles.

**Projet**: VA50-SUJET5 - Réarrangement autonome d'objets avec Tiago  
**Rôle**: Ingénieur Logiciel & Intégration (R3)  
**Auteur**: AlexNGUEMNIN

## 🎯 Fonctionnalités

- **Service de traitement d'images** : Envoie une image capturée par Tiago au pipeline IA
- **Détection d'objets** : Utilise Mask R-CNN pour segmenter et identifier les objets
- **Génération d'image cible** : Utilise Stable Diffusion avec ControlNet pour générer la configuration cible
- **Extraction de positions** : Calcule les positions finales des objets depuis l'image générée
- **Publication en temps réel** : Publie le statut du traitement et les objets détectés
- **Services ROS** : Récupération des positions initiales et finales

## 🏗️ Architecture du Pipeline

```
1. Capture d'image (Tiago)
   ↓
2. Envoi au nœud ROS (/tiago/send_image_to_hf)
   ↓
3. Détection d'objets (Mask R-CNN)
   ↓
4. Description textuelle (CLIP + Captioning)
   ↓
5. Génération d'image cible (Stable Diffusion + ControlNet)
   ↓
6. Extraction de positions finales
   ↓
7. Retour des résultats (JSON)
   ↓
8. Exécution du réarrangement (Tiago)
```

## 📁 Structure du Package

```
huggingface_bridge/
├── CMakeLists.txt                      # Configuration CMake
├── package.xml                         # Métadonnées du package ROS
├── README.md                           # Ce fichier
├── requirements.txt                    # Dépendances Python
├── config/
│   └── huggingface_config.yaml        # Configuration (tokens, chemins, etc.)
├── launch/
│   └── huggingface_bridge.launch      # Fichier de lancement ROS
├── scripts/
│   └── huggingface_bridge_node.py     # Nœud ROS principal
├── src/
│   └── huggingface_bridge/
│       ├── __init__.py                # Package Python
│       ├── huggingface_client.py      # Client API Hugging Face
│       ├── image_handler.py           # Gestion des images
│       └── json_handler.py            # Gestion des JSON
└── srv/
    ├── ProcessImage.srv               # Service de traitement d'image
    └── GetPositions.srv               # Service de récupération de positions
```

## 🔧 Prérequis

### Logiciels Requis

- **ROS Noetic** (ou version compatible)
- **Python 3.8+**
- **Docker** (pour l'environnement Tiago)
- **CUDA** (optionnel, pour accélération GPU)

### Dépendances Python

Voir `requirements.txt` pour la liste complète. Principales dépendances :
- `huggingface-hub` : Authentification et accès aux modèles
- `transformers` : Modèles de traitement du langage
- `torch` & `torchvision` : Framework PyTorch
- `diffusers` : Modèles de diffusion (Stable Diffusion)
- `opencv-python` : Traitement d'images
- `Pillow` : Manipulation d'images

## 📥 Installation

### Étape 1 : Cloner le Projet

```bash
git clone https://github.com/AlexNGUEMNIN/VA50-SUJET5.git
cd VA50-SUJET5
```

### Étape 2 : Construire l'Environnement Docker

```bash
# Construire l'image Docker
./build.sh

# Lancer le serveur (Terminal 1)
./server.sh

# Lancer un client (Terminal 2)
./client.sh
```

### Étape 3 : Installer les Dépendances Python

**Dans le conteneur Docker** :

```bash
cd ~/ros_ws/workspace/src/huggingface_bridge
pip3 install -r requirements.txt
```

### Étape 4 : Configurer Hugging Face

Le token Hugging Face est déjà configuré dans `config/huggingface_config.yaml` :

```yaml
huggingface:
  token: "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"
```

**Alternative** : Utiliser une variable d'environnement

```bash
export HF_TOKEN="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"
```

Puis modifier le fichier de configuration :

```yaml
huggingface:
  token: ${HF_TOKEN}
```

### Étape 5 : Compiler le Workspace ROS

```bash
cd ~/ros_ws/workspace
catkin_make
source devel/setup.bash
```

## 🚀 Utilisation

### Scénario Complet : De la Capture au Réarrangement

#### Terminal 1 : Lancer Gazebo avec Tiago

```bash
source /opt/pal/gallium/setup.bash
cd ~/ros_ws/workspace/src
roslaunch tiago_gazebo.launch
```

Gazebo va démarrer avec le robot Tiago dans son environnement.

#### Terminal 2 : Capturer les Images

```bash
cd ~/ros_ws/workspace/scripts
python3 capture.py
```

Cela va capturer 4 images panoramiques et les sauvegarder dans `~/ros_ws/data/images/`.

Les images seront nommées :
- `table_position_1_YYYYMMDD_HHMMSS.png`
- `table_position_2_YYYYMMDD_HHMMSS.png`
- `table_position_3_YYYYMMDD_HHMMSS.png`
- `table_position_4_YYYYMMDD_HHMMSS.png`

#### Terminal 3 : Lancer le Nœud Hugging Face Bridge

```bash
source ~/ros_ws/workspace/devel/setup.bash
roslaunch huggingface_bridge huggingface_bridge.launch
```

Vous devriez voir :

```
======================================================================
Initialisation du nœud Hugging Face Bridge
======================================================================
✓ Configuration chargée avec succès
✓ Service créé: /tiago/send_image_to_hf
✓ Service créé: /tiago/get_object_positions
✓ Publisher créé: /tiago/hf_status
✓ Publisher créé: /tiago/detected_objects
✓ Nœud Hugging Face Bridge initialisé avec succès
======================================================================
```

#### Terminal 4 : Envoyer une Image au Pipeline IA

**Méthode 1 : Via `rosservice call`**

```bash
source ~/ros_ws/workspace/devel/setup.bash

rosservice call /tiago/send_image_to_hf \
  "image_path: '/home/pal/ros_ws/data/images/table_position_1_20251218_103000.png'"
```

**Méthode 2 : Via Script Python**

Créez un script `test_pipeline.py` :

```python
#!/usr/bin/env python3
import rospy
from huggingface_bridge.srv import ProcessImage

rospy.init_node('test_client')

# Attendre que le service soit disponible
rospy.wait_for_service('/tiago/send_image_to_hf')

# Créer le proxy de service
process_image = rospy.ServiceProxy('/tiago/send_image_to_hf', ProcessImage)

# Appeler le service
response = process_image('/home/pal/ros_ws/data/images/table_position_1_20251218_103000.png')

if response.success:
    print("✓ Traitement réussi!")
    print(f"Image générée: {response.generated_image_path}")
    print(f"Détections: {response.detections_json_path}")
    print(f"Positions finales: {response.final_positions_json_path}")
else:
    print(f"✗ Erreur: {response.message}")
```

Puis exécutez :

```bash
python3 test_pipeline.py
```

#### Terminal 5 : Récupérer les Résultats

**Positions Initiales** :

```bash
rosservice call /tiago/get_object_positions "json_type: 'initial'"
```

**Positions Finales** :

```bash
rosservice call /tiago/get_object_positions "json_type: 'final'"
```

**Écouter le Statut en Temps Réel** :

```bash
rostopic echo /tiago/hf_status
```

**Écouter les Objets Détectés** :

```bash
rostopic echo /tiago/detected_objects
```

## 📊 Structure des Données

### JSON de Détections Initiales

Fichier : `~/ros_ws/workspace/pipeline/outputs/detections_input.json`

```json
[
  {
    "id": "obj_000",
    "label": "plate",
    "x_pixel": 450.77,
    "y_pixel": 179.39,
    "theta": 0.0,
    "mask_path": "outputs/masks/mask_obj_000_plate.png"
  },
  {
    "id": "obj_001",
    "label": "fork",
    "x_pixel": 244.36,
    "y_pixel": 216.26,
    "theta": 0.0,
    "mask_path": "outputs/masks/mask_obj_001_fork.png"
  },
  {
    "id": "obj_002",
    "label": "knife",
    "x_pixel": 515.83,
    "y_pixel": 203.88,
    "theta": 0.0,
    "mask_path": "outputs/masks/mask_obj_002_knife.png"
  }
]
```

### JSON de Positions Finales

Fichier : `~/ros_ws/workspace/pipeline/outputs/final_positions.json`

```json
[
  {
    "id": "obj_000",
    "label": "plate",
    "x_pixel": 35.97,
    "y_pixel": 203.67,
    "theta": 1.49,
    "area": 4410.0
  },
  {
    "id": "obj_001",
    "label": "fork",
    "x_pixel": 165.79,
    "y_pixel": 209.44,
    "theta": 1.57,
    "area": 4387.5
  },
  {
    "id": "obj_002",
    "label": "knife",
    "x_pixel": 297.40,
    "y_pixel": 207.55,
    "theta": 1.57,
    "area": 4320.0
  }
]
```

### Message de Statut (Topic)

Topic : `/tiago/hf_status`

```json
{
  "status": "processing",
  "step": "segmentation",
  "progress": 0.25,
  "message": "Segmentation en cours avec Mask R-CNN...",
  "timestamp": 1702900200.123
}
```

États possibles :
- `idle` : En attente
- `processing` : Traitement en cours
- `completed` : Traitement terminé
- `error` : Erreur

### Message d'Objets Détectés (Topic)

Topic : `/tiago/detected_objects`

```json
{
  "timestamp": 1702900200.456,
  "objects": [
    {
      "id": "obj_000",
      "label": "plate",
      "x_pixel": 450.77,
      "y_pixel": 179.39,
      "theta": 0.0
    }
  ]
}
```

## 🔍 Services ROS

### Service `/tiago/send_image_to_hf`

**Type** : `huggingface_bridge/ProcessImage`

**Requête** :
```
string image_path    # Chemin de l'image à traiter
```

**Réponse** :
```
bool success                      # True si succès
string message                    # Message de statut
string generated_image_path       # Chemin de l'image générée
string detections_json_path       # Chemin du JSON des détections
string final_positions_json_path  # Chemin du JSON des positions finales
```

**Exemple** :
```bash
rosservice call /tiago/send_image_to_hf \
  "image_path: '/home/pal/ros_ws/data/images/table_input.png'"
```

### Service `/tiago/get_object_positions`

**Type** : `huggingface_bridge/GetPositions`

**Requête** :
```
string json_type    # "initial" ou "final"
```

**Réponse** :
```
bool success        # True si succès
string json_content # Contenu du JSON en string
```

**Exemple** :
```bash
rosservice call /tiago/get_object_positions "json_type: 'initial'"
```

## 📡 Topics ROS

### Topic `/tiago/hf_status`

**Type** : `std_msgs/String`

Publie le statut du traitement en temps réel au format JSON.

**Exemple** :
```bash
rostopic echo /tiago/hf_status
```

### Topic `/tiago/detected_objects`

**Type** : `std_msgs/String`

Publie la liste des objets détectés au format JSON.

**Exemple** :
```bash
rostopic echo /tiago/detected_objects
```

## ⚙️ Configuration

Le fichier de configuration se trouve dans `config/huggingface_config.yaml`.

### Sections Principales

#### Authentification Hugging Face

```yaml
huggingface:
  token: "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"
```

#### Chemins des Fichiers

```yaml
paths:
  input_images: "~/ros_ws/data/images"
  output_dir: "~/ros_ws/workspace/pipeline/outputs"
  masks_dir: "~/ros_ws/workspace/pipeline/outputs/masks"
  pipeline_dir: "~/ros_ws/workspace/pipeline"
```

#### Modèles Hugging Face

```yaml
models:
  segmentation: "facebook/maskformer-swin-base-coco"
  clip: "openai/clip-vit-base-patch32"
  image_generation: "stabilityai/stable-diffusion-2-1"
```

#### Paramètres de Traitement

```yaml
processing:
  confidence_threshold: 0.7
  max_objects: 10
  image_size: [640, 480]
  timeout: 300  # Timeout en secondes
```

#### Topics et Services ROS

```yaml
ros:
  service_send_image: "/tiago/send_image_to_hf"
  service_get_positions: "/tiago/get_object_positions"
  topic_status: "/tiago/hf_status"
  topic_objects: "/tiago/detected_objects"
```

## 🧪 Tests et Validation

### Test 1 : Vérifier que le Nœud est Actif

```bash
rosnode list | grep huggingface
```

Devrait afficher :
```
/huggingface_bridge_node
```

### Test 2 : Vérifier les Services

```bash
rosservice list | grep tiago
```

Devrait afficher :
```
/tiago/get_object_positions
/tiago/send_image_to_hf
```

### Test 3 : Vérifier les Topics

```bash
rostopic list | grep tiago
```

Devrait afficher :
```
/tiago/detected_objects
/tiago/hf_status
```

### Test 4 : Tester avec une Image de Test

```bash
# Créer une image de test
cd ~/ros_ws/data/images
wget https://via.placeholder.com/640x480 -O test_image.png

# Appeler le service
rosservice call /tiago/send_image_to_hf \
  "image_path: '/home/pal/ros_ws/data/images/test_image.png'"
```

### Test 5 : Vérifier les Dépendances Python

```bash
cd ~/ros_ws/workspace/src/huggingface_bridge/src/huggingface_bridge
python3 huggingface_client.py
```

Cela affichera le statut de toutes les dépendances.

## 🐛 Dépannage

### Problème : Erreur d'authentification Hugging Face

**Symptôme** :
```
[HuggingFaceClient] Erreur d'authentification: ...
```

**Solution** :
1. Vérifiez que le token est correct dans `config/huggingface_config.yaml`
2. Ou exportez la variable d'environnement :
   ```bash
   export HF_TOKEN="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"
   ```

### Problème : Modèles non téléchargés

**Symptôme** :
```
Downloading model...
```

**Solution** :
- Les modèles se téléchargent automatiquement au premier lancement
- Soyez patient, cela peut prendre plusieurs minutes
- Vérifiez votre connexion Internet

### Problème : Erreur de chemin de fichiers

**Symptôme** :
```
Image non trouvée ou invalide: ...
```

**Solution** :
- Vérifiez que le chemin est absolu : `/home/pal/...`
- Ne pas utiliser de chemins relatifs
- Vérifiez les permissions du fichier

### Problème : Timeout de traitement

**Symptôme** :
```
Timeout du pipeline après 300 secondes
```

**Solution** :
- Augmentez le timeout dans `config/huggingface_config.yaml` :
  ```yaml
  processing:
    timeout: 600  # 10 minutes
  ```

### Problème : Dépendances manquantes

**Symptôme** :
```
ModuleNotFoundError: No module named 'xxx'
```

**Solution** :
```bash
cd ~/ros_ws/workspace/src/huggingface_bridge
pip3 install -r requirements.txt
```

### Problème : Erreur de compilation ROS

**Symptôme** :
```
CMake Error at ...
```

**Solution** :
```bash
cd ~/ros_ws/workspace
catkin_make clean
catkin_make
source devel/setup.bash
```

## 📚 Documentation Supplémentaire

### Pipeline Python

Les scripts du pipeline se trouvent dans `~/ros_ws/workspace/pipeline/src/` :

- `detect_objects.py` : Détection d'objets avec Mask R-CNN
- `caption_and_clip.py` : Génération de descriptions textuelles
- `img-gene.py` : Génération d'image avec Stable Diffusion
- `generated_image_to_positions.py` : Extraction de positions

### Logs

Les logs du nœud ROS sont disponibles dans :
```bash
~/.ros/log/latest/huggingface_bridge_node-*.log
```

Pour voir les logs en temps réel :
```bash
tail -f ~/.ros/log/latest/huggingface_bridge_node-*.log
```

## 🤝 Contribution

Pour contribuer au projet :

1. Forkez le repository
2. Créez une branche (`git checkout -b feature/ma-fonctionnalite`)
3. Commitez vos changements (`git commit -am 'Ajout de fonctionnalité'`)
4. Pushez vers la branche (`git push origin feature/ma-fonctionnalite`)
5. Créez une Pull Request

## 📄 Licence

MIT License - Voir le fichier LICENSE pour plus de détails.

## 📞 Support

Pour toute question ou problème :
- **Issues GitHub** : https://github.com/AlexNGUEMNIN/VA50-SUJET5/issues
- **Email** : alex.nguemnin@example.com

## 🙏 Remerciements

- **PAL Robotics** pour le robot Tiago
- **Hugging Face** pour les modèles pré-entraînés
- **ROS Community** pour le framework ROS

---

**Dernière mise à jour** : 2025-12-18  
**Version** : 1.0.0  
**Auteur** : AlexNGUEMNIN
