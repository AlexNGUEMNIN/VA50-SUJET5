# Architecture du Système de Détection d'Objets

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ROBOT TIAGO                                 │
│                        (Simulation Gazebo)                           │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Images RGB/Profondeur
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CAPTURE D'IMAGES                               │
│                    (scripts/capture.py)                              │
│                                                                       │
│  • Contrôle tête/torse du robot                                     │
│  • Capture 4 angles différents                                      │
│  • Sauvegarde: ~/ros_ws/data/images/*.png                          │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Images PNG stockées
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  NŒUD DE TRAITEMENT LOCAL                            │
│              (image_processing_node.py)                              │
│                                                                       │
│  ┌─────────────────────────────────────────────────────┐            │
│  │         LOCAL MODEL HANDLER                         │            │
│  │     (local_model_handler.py)                        │            │
│  │                                                      │            │
│  │  ┌────────────────────────────────────────┐        │            │
│  │  │   Modèle DETR (PyTorch)                │        │            │
│  │  │   ~/ros_ws/models/                     │        │            │
│  │  │   facebook_detr-resnet-50/             │        │            │
│  │  │                                         │        │            │
│  │  │   • ResNet-50 backbone                 │        │            │
│  │  │   • Transformer encoder/decoder        │        │            │
│  │  │   • 91 classes COCO                    │        │            │
│  │  │   • ~160 MB                            │        │            │
│  │  └────────────────────────────────────────┘        │            │
│  │                                                      │            │
│  │  Traitement:                                        │            │
│  │  1. Chargement image                                │            │
│  │  2. Prétraitement (resize, normalize)               │            │
│  │  3. Inférence (détection objets)                    │            │
│  │  4. Post-traitement (filtrage, positions)           │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                       │
│  Résultats:                                                          │
│  • JSON: positions + labels + scores                                │
│  • Images annotées avec boîtes de détection                         │
│  • Organisation par catégorie (couverts/assiettes/tasses)          │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Publications ROS
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        TOPICS ROS                                    │
│                                                                       │
│  /tiago/object_detections (std_msgs/String)                         │
│  ├─ Format JSON                                                      │
│  ├─ Temps réel ou batch                                             │
│  └─ Contient: labels, positions, scores                             │
│                                                                       │
│  /tiago/object_poses (geometry_msgs/PoseArray)                      │
│  ├─ Format ROS standard                                             │
│  ├─ Visualisable dans RViz                                          │
│  └─ Positions normalisées 2D                                        │
│                                                                       │
│  /tiago/annotated_image (sensor_msgs/Image)                         │
│  ├─ Image avec boîtes de détection                                  │
│  ├─ Labels et scores affichés                                       │
│  └─ Visualisable avec image_view                                    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Abonnement aux topics
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   SYSTÈME DE CONTRÔLE TIAGO                          │
│                  (Votre code d'organisation)                         │
│                                                                       │
│  • Reçoit les détections                                            │
│  • Planifie les mouvements                                          │
│  • Commande le bras/gripper                                         │
│  • Organise les objets sur la table                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Flux de Données Détaillé

### 1. Capture d'Images

```
Tiago Robot
    │
    ├─ Topic: /xtion/rgb/image_raw (sensor_msgs/Image)
    │  └─ 640x480 pixels, BGR8 encoding
    │
    └─ capture.py écoute et sauvegarde
       └─ ~/ros_ws/data/images/table_position_X_TIMESTAMP.png
```

### 2. Traitement Local

```
Image PNG
    │
    ├─ Chargement avec OpenCV/PIL
    │  └─ Conversion RGB (640x480x3)
    │
    ├─ Prétraitement (DETR Processor)
    │  ├─ Resize to model input size
    │  ├─ Normalize [0,1] → [-1,1]
    │  └─ Convert to tensor
    │
    ├─ Inférence (DETR Model)
    │  ├─ Feature extraction (ResNet-50)
    │  ├─ Transformer processing
    │  └─ Object queries → detections
    │
    └─ Post-traitement
       ├─ Filter by confidence (>0.7)
       ├─ Filter by class (tableware only)
       ├─ Convert boxes to pixel coordinates
       └─ Compute centers and normalized positions
```

### 3. Publication ROS

```
Détections
    │
    ├─ /tiago/object_detections
    │  └─ JSON: {
    │       "timestamp": 1234567.89,
    │       "count": 5,
    │       "objects": [
    │         {
    │           "label": "fork",
    │           "score": 0.95,
    │           "center_x": 320.5,
    │           "center_y": 240.3,
    │           "normalized_x": 0.5,
    │           "normalized_y": 0.375
    │         }, ...
    │       ]
    │     }
    │
    ├─ /tiago/object_poses
    │  └─ PoseArray: {
    │       header: {...},
    │       poses: [
    │         Pose(x=0.5, y=0.375, z=0.0, ...),
    │         ...
    │       ]
    │     }
    │
    └─ /tiago/annotated_image
       └─ Image avec overlay graphique
```

## Services ROS

```
/tiago/process_captured_images (std_srvs/Trigger)
    │
    Request: {}
    │
    Processing:
    ├─ Scan ~/ros_ws/data/images/
    ├─ Pour chaque image PNG:
    │  ├─ Détecter objets
    │  ├─ Sauvegarder image annotée
    │  └─ Collecter statistiques
    │
    Response: {
      success: true/false,
      message: "N images traitées..."
    }
```

## Composants Logiciels

### Python Packages

```
transformers==4.30+
    ├─ DetrImageProcessor (prétraitement)
    └─ DetrForObjectDetection (modèle)

torch==2.0+
    ├─ Tensors et opérations
    ├─ Device management (CPU/CUDA)
    └─ Model inference

opencv-python==4.5+
    ├─ Lecture/écriture images
    ├─ Conversion colorspace
    └─ Drawing (annotations)

rospy
    ├─ Node initialization
    ├─ Publishers/Subscribers
    └─ Services
```

### Fichiers Principaux

```
workspace/src/image_bridge/
│
├─ src/image_bridge/
│  ├─ local_model_handler.py
│  │  ├─ LocalModelHandler class
│  │  ├─ load_detection_model()
│  │  ├─ detect_objects()
│  │  └─ compute_object_positions()
│  │
│  ├─ huggingface_client.py (legacy, API cloud)
│  ├─ ros_interface.py (legacy, API cloud)
│  └─ config.py (configuration)
│
├─ scripts/
│  ├─ image_processing_node.py
│  │  ├─ ImageProcessingNode class
│  │  ├─ image_callback()
│  │  ├─ process_image()
│  │  └─ process_captured_images_service()
│  │
│  ├─ download_model.py
│  │  └─ Télécharge DETR depuis Hugging Face
│  │
│  ├─ test_setup.py
│  │  └─ Validation de l'installation
│  │
│  └─ example_usage.py
│     └─ Exemples d'intégration
│
└─ launch/
   └─ image_processing.launch
      └─ Lance le nœud avec paramètres
```

## Performance

### Timing Typique (CPU Intel i5)

```
Chargement modèle: ~2-3 secondes (première fois)
Traitement par image: ~1-2 secondes
    ├─ Prétraitement: ~0.1s
    ├─ Inférence: ~0.8-1.5s
    └─ Post-traitement: ~0.1s
```

### Mémoire

```
Modèle en RAM: ~500 MB
Image en mémoire: ~1 MB
Peak usage: ~1 GB (avec buffers)
```

### Avec GPU (NVIDIA RTX 3060)

```
Chargement modèle: ~3-4 secondes (transfert vers GPU)
Traitement par image: ~0.2-0.3 secondes
    ├─ Prétraitement: ~0.05s
    ├─ Inférence: ~0.1-0.15s
    └─ Post-traitement: ~0.05s
```

## Comparaison avec l'ancienne version

### Avant (API Hugging Face Cloud)

```
Avantages:
  ✓ Pas de téléchargement de modèle
  ✓ Modèles toujours à jour

Inconvénients:
  ✗ Requiert connexion internet
  ✗ Latence réseau (~2-5s par image)
  ✗ Limites de quota API
  ✗ Coûts potentiels
  ✗ Dépendance externe
```

### Maintenant (Modèle Local)

```
Avantages:
  ✓ Fonctionne hors ligne
  ✓ Latence faible (~1s CPU, ~0.2s GPU)
  ✓ Pas de limites d'utilisation
  ✓ Pas de coûts récurrents
  ✓ Contrôle total

Inconvénients:
  ✗ Téléchargement initial (~160 MB)
  ✗ Utilise RAM/VRAM
  ✗ Modèle fixe (pas de mise à jour auto)
```

## Extensibilité

### Ajouter un nouveau modèle

```python
# Dans local_model_handler.py

def load_yolo_model(self):
    """Alternative: modèle YOLO plus léger."""
    from transformers import YolosImageProcessor, YolosForObjectDetection
    
    processor = YolosImageProcessor.from_pretrained("hustvl/yolos-tiny")
    model = YolosForObjectDetection.from_pretrained("hustvl/yolos-tiny")
    # ... configuration
```

### Ajouter de nouvelles classes

```python
# Dans local_model_handler.py
self.target_classes = [
    'fork', 'knife', 'spoon',
    'bowl', 'cup', 'plate',
    'bottle', 'wine glass',
    # Ajouter ici:
    'vase', 'potted plant', 'book'
]
```

### Intégrer avec planification

```python
# Dans votre code de contrôle
def organize_table(detections):
    """Planifier l'organisation basée sur les détections."""
    for obj in detections['objects']:
        if obj['label'] == 'fork':
            target = compute_fork_position(obj)
            move_robot_to(target)
            grasp_object()
            place_at(target)
```

---

**Note**: Ce document décrit l'architecture actuelle. Pour l'utilisation pratique, voir [README_FR.md](README_FR.md).
