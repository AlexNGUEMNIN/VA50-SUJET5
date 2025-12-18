# Architecture et Flux de Données - Hugging Face Bridge

## 🏗️ Vue d'Ensemble du Système

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ROBOT TIAGO (GAZEBO)                        │
│                                                                     │
│  ┌──────────────┐                                                  │
│  │   Caméra     │ ──► Capture 4 vues panoramiques                 │
│  └──────────────┘                                                  │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────────┐             │
│  │  ~/ros_ws/data/images/                           │             │
│  │   - table_position_1_20251218_103000.png         │             │
│  │   - table_position_2_20251218_103001.png         │             │
│  │   - table_position_3_20251218_103002.png         │             │
│  │   - table_position_4_20251218_103003.png         │             │
│  └──────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ rosservice call /tiago/send_image_to_hf
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   HUGGING FACE BRIDGE NODE                          │
│                   (huggingface_bridge_node)                         │
│                                                                     │
│  Services:                                                          │
│   • /tiago/send_image_to_hf      ──► Traitement pipeline          │
│   • /tiago/get_object_positions  ──► Récupération résultats       │
│                                                                     │
│  Topics:                                                            │
│   • /tiago/hf_status             ──► État en temps réel           │
│   • /tiago/detected_objects      ──► Objets détectés              │
│                                                                     │
│  Orchestration du pipeline Python                                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ subprocess.run('run_pipeline.py')
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PIPELINE PYTHON IA                             │
│           (~/ros_ws/workspace/pipeline/)                            │
│                                                                     │
│  ┌────────────────────────────────────────────────────────┐        │
│  │  ÉTAPE 1: Détection d'Objets                          │        │
│  │  (detect_objects.py)                                   │        │
│  │  • Modèle: Mask R-CNN (torchvision)                    │        │
│  │  • Entrée: table_input.png                             │        │
│  │  • Sortie: detections_input.json + masques             │        │
│  └────────────────────────────────────────────────────────┘        │
│                         │                                           │
│                         ▼                                           │
│  ┌────────────────────────────────────────────────────────┐        │
│  │  ÉTAPE 2: Génération d'Image Cible                    │        │
│  │  (img-gene.py)                                         │        │
│  │  • Modèle: Stable Diffusion + ControlNet               │        │
│  │  • Entrée: scribble.png (guide géométrique)            │        │
│  │  • Sortie: img_generated.png                           │        │
│  └────────────────────────────────────────────────────────┘        │
│                         │                                           │
│                         ▼                                           │
│  ┌────────────────────────────────────────────────────────┐        │
│  │  ÉTAPE 3: Extraction Positions Finales                │        │
│  │  (generated_image_to_positions.py)                     │        │
│  │  • Méthode: Segmentation adaptative + contours         │        │
│  │  • Entrée: img_generated.png                           │        │
│  │  • Sortie: final_positions.json                        │        │
│  └────────────────────────────────────────────────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ Résultats
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FICHIERS DE SORTIE                               │
│          (~/ros_ws/workspace/pipeline/outputs/)                     │
│                                                                     │
│  ┌──────────────────────────────────────────────────┐             │
│  │  detections_input.json                           │             │
│  │  [                                               │             │
│  │    {                                             │             │
│  │      "id": "obj_000",                            │             │
│  │      "label": "plate",                           │             │
│  │      "x_pixel": 450.77,                          │             │
│  │      "y_pixel": 179.39,                          │             │
│  │      "theta": 0.0,                               │             │
│  │      "mask_path": "outputs/masks/..."            │             │
│  │    },                                            │             │
│  │    ...                                           │             │
│  │  ]                                               │             │
│  └──────────────────────────────────────────────────┘             │
│                                                                     │
│  ┌──────────────────────────────────────────────────┐             │
│  │  final_positions.json                            │             │
│  │  [                                               │             │
│  │    {                                             │             │
│  │      "id": "obj_000",                            │             │
│  │      "label": "plate",                           │             │
│  │      "x_pixel": 35.97,                           │             │
│  │      "y_pixel": 203.67,                          │             │
│  │      "theta": 1.49,                              │             │
│  │      "area": 4410.0                              │             │
│  │    },                                            │             │
│  │    ...                                           │             │
│  │  ]                                               │             │
│  └──────────────────────────────────────────────────┘             │
│                                                                     │
│  ┌──────────────────────────────────────────────────┐             │
│  │  img_generated.png                               │             │
│  │  (Image de la configuration cible)               │             │
│  └──────────────────────────────────────────────────┘             │
│                                                                     │
│  ┌──────────────────────────────────────────────────┐             │
│  │  masks/                                          │             │
│  │   - mask_obj_000_plate.png                       │             │
│  │   - mask_obj_001_fork.png                        │             │
│  │   - mask_obj_002_knife.png                       │             │
│  └──────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ rosservice call /tiago/get_object_positions
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  PLANIFICATION ET EXÉCUTION                         │
│                      (Module Robotique)                             │
│                                                                     │
│  1. Récupère positions initiales et finales                        │
│  2. Calcule la trajectoire pour chaque objet                       │
│  3. Planifie les mouvements du bras                                │
│  4. Exécute le réarrangement                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 📊 Flux de Données Détaillé

### 1. Capture d'Image

```bash
# Script de capture (à créer par l'équipe robotique)
python3 capture.py

# Résultat: 4 images panoramiques dans ~/ros_ws/data/images/
```

### 2. Envoi au Nœud ROS

```bash
# Service call
rosservice call /tiago/send_image_to_hf \
  "image_path: '/home/pal/ros_ws/data/images/table_position_1.png'"

# Ou via Python
import rospy
from huggingface_bridge.srv import ProcessImage

rospy.init_node('client')
process_image = rospy.ServiceProxy('/tiago/send_image_to_hf', ProcessImage)
response = process_image('/home/pal/ros_ws/data/images/table_position_1.png')
```

### 3. Traitement par le Pipeline

Le nœud ROS exécute automatiquement:

```python
# Interne au nœud
subprocess.run(['python3', 'run_pipeline.py'])
```

Ce qui lance séquentiellement:
1. `detect_objects.py` → Détection Mask R-CNN
2. `img-gene.py` → Génération avec Stable Diffusion
3. `generated_image_to_positions.py` → Extraction positions

### 4. Publication des Résultats

Le nœud publie en temps réel:

```bash
# Écouter le statut
rostopic echo /tiago/hf_status

# Écouter les objets détectés
rostopic echo /tiago/detected_objects
```

### 5. Récupération des Positions

```bash
# Positions initiales
rosservice call /tiago/get_object_positions "json_type: 'initial'"

# Positions finales
rosservice call /tiago/get_object_positions "json_type: 'final'"
```

## 🔄 Exemple de Séquence Complète

```bash
# Terminal 1: Gazebo
source /opt/pal/gallium/setup.bash
roslaunch tiago_gazebo.launch

# Terminal 2: Nœud Bridge
source ~/ros_ws/workspace/devel/setup.bash
roslaunch huggingface_bridge huggingface_bridge.launch

# Terminal 3: Surveillance
rostopic echo /tiago/hf_status

# Terminal 4: Commandes
# 1. Capturer
python3 ~/ros_ws/workspace/scripts/capture.py

# 2. Traiter
rosservice call /tiago/send_image_to_hf \
  "image_path: '/home/pal/ros_ws/data/images/table_position_1.png'"

# 3. Récupérer résultats
rosservice call /tiago/get_object_positions "json_type: 'initial'"
rosservice call /tiago/get_object_positions "json_type: 'final'"

# 4. Planifier et exécuter (module robotique)
# ... code de planification de trajectoire ...
```

## 📈 Suivi de Progression

Le topic `/tiago/hf_status` publie:

```json
{
  "status": "processing",
  "step": "segmentation",
  "progress": 0.25,
  "message": "Segmentation en cours avec Mask R-CNN...",
  "timestamp": 1702900200.123
}
```

États possibles:
- `idle` → En attente
- `processing` → Traitement en cours (progress: 0.0 → 1.0)
- `completed` → Terminé avec succès
- `error` → Erreur rencontrée

## 🔌 Points d'Extension

### Ajouter un Nouveau Modèle

1. Modifier `config/huggingface_config.yaml`:
```yaml
models:
  my_new_model: "organization/model-name"
```

2. Utiliser dans le pipeline:
```python
from transformers import AutoModel
model = AutoModel.from_pretrained(config['models']['my_new_model'])
```

### Ajouter un Nouveau Service

1. Créer `srv/MyService.srv`:
```
# Request
string input_param
---
# Response
bool success
string result
```

2. Ajouter au `CMakeLists.txt`:
```cmake
add_service_files(
  FILES
  ProcessImage.srv
  GetPositions.srv
  MyService.srv  # <-- Nouveau
)
```

3. Implémenter dans le nœud:
```python
def handle_my_service(self, req):
    response = MyServiceResponse()
    # ... traitement ...
    return response

# Dans __init__:
self.service_my = rospy.Service(
    '/tiago/my_service',
    MyService,
    self.handle_my_service
)
```

---

**Documentation complète:** `README.md`  
**Démarrage rapide:** `QUICKSTART.md`
