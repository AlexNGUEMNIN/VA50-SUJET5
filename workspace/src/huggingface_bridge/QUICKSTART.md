# Guide de Démarrage Rapide - Hugging Face Bridge

## 🚀 Installation Rapide

### 1. Environnement Docker

```bash
# À la racine du projet
./build.sh          # Construire l'image Docker
./server.sh         # Terminal 1: Lancer le serveur
./client.sh         # Terminal 2+: Lancer des clients
```

### 2. Installation des Dépendances

**Dans le conteneur Docker:**

```bash
cd ~/ros_ws/workspace/src/huggingface_bridge
pip3 install -r requirements.txt
```

### 3. Compilation du Workspace ROS

```bash
cd ~/ros_ws/workspace
catkin_make
source devel/setup.bash
```

### 4. Validation de l'Installation

```bash
cd ~/ros_ws/workspace/src/huggingface_bridge/scripts
python3 validate_installation.py
```

## 📝 Utilisation de Base

### Lancer le Système Complet

**Terminal 1: Gazebo**
```bash
source /opt/pal/gallium/setup.bash
roslaunch tiago_gazebo.launch
```

**Terminal 2: Nœud Hugging Face Bridge**
```bash
source ~/ros_ws/workspace/devel/setup.bash
roslaunch huggingface_bridge huggingface_bridge.launch
```

**Terminal 3: Test du Service**
```bash
source ~/ros_ws/workspace/devel/setup.bash

# Traiter une image
rosservice call /tiago/send_image_to_hf \
  "image_path: '/home/pal/ros_ws/workspace/pipeline/data/images/table_input.png'"

# Récupérer les positions initiales
rosservice call /tiago/get_object_positions "json_type: 'initial'"

# Récupérer les positions finales
rosservice call /tiago/get_object_positions "json_type: 'final'"
```

## 🔍 Vérification Rapide

### Vérifier que tout fonctionne

```bash
# Le nœud est actif?
rosnode list | grep huggingface

# Les services sont disponibles?
rosservice list | grep tiago

# Les topics publient?
rostopic echo /tiago/hf_status -n 1
rostopic echo /tiago/detected_objects -n 1
```

## 🧪 Tests

### Exécuter les Tests Automatiques

```bash
cd ~/ros_ws/workspace/src/huggingface_bridge/scripts

# Valider l'installation
python3 validate_installation.py

# Tester les services (le nœud doit être lancé)
python3 test_huggingface_bridge.py
```

## 📊 Résultats Attendus

### Fichiers Générés

Après un traitement réussi, vous trouverez:

```
~/ros_ws/workspace/pipeline/outputs/
├── detections_input.json      # Positions initiales des objets
├── final_positions.json        # Positions finales (cibles)
├── img_generated.png           # Image générée par l'IA
├── debug_detected_positions.png # Visualisation debug
└── masks/                      # Masques de segmentation
    ├── mask_obj_000_plate.png
    ├── mask_obj_001_fork.png
    └── mask_obj_002_knife.png
```

### Format des Positions

**detections_input.json:**
```json
[
  {
    "id": "obj_000",
    "label": "plate",
    "x_pixel": 450.77,
    "y_pixel": 179.39,
    "theta": 0.0,
    "mask_path": "outputs/masks/mask_obj_000_plate.png"
  }
]
```

**final_positions.json:**
```json
[
  {
    "id": "obj_000",
    "label": "plate",
    "x_pixel": 35.97,
    "y_pixel": 203.67,
    "theta": 1.49,
    "area": 4410.0
  }
]
```

## ⚠️ Dépannage Rapide

### Erreur: Service non disponible
```bash
# Vérifier que le nœud est lancé
rosnode list

# Relancer le nœud
roslaunch huggingface_bridge huggingface_bridge.launch
```

### Erreur: Image non trouvée
```bash
# Vérifier le chemin (doit être absolu)
ls -l /home/pal/ros_ws/workspace/pipeline/data/images/table_input.png

# Créer une image de test si nécessaire
cd ~/ros_ws/workspace/pipeline/data/images
# Copier une image test ici
```

### Erreur: Timeout du pipeline
```bash
# Augmenter le timeout dans config/huggingface_config.yaml
# processing:
#   timeout: 600  # 10 minutes au lieu de 5
```

### Erreur: Dépendances manquantes
```bash
cd ~/ros_ws/workspace/src/huggingface_bridge
pip3 install -r requirements.txt
```

## 📚 Documentation Complète

Pour plus de détails, consultez:
- **README.md** - Documentation complète du package
- **config/huggingface_config.yaml** - Configuration détaillée
- **Pipeline README** - Documentation du pipeline Python

## 🤝 Support

En cas de problème:
1. Consultez le README.md complet
2. Vérifiez les logs: `tail -f ~/.ros/log/latest/huggingface_bridge_node-*.log`
3. Ouvrez une issue sur GitHub: https://github.com/AlexNGUEMNIN/VA50-SUJET5/issues

---

**Version:** 1.0.0  
**Dernière mise à jour:** 2025-12-18
