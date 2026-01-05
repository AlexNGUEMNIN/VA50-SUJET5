# 🤖 Guide d'Automatisation - Réarrangement Autonome d'Objets avec Tiago

## 📋 Table des Matières

1. [Introduction](#introduction)
2. [Architecture du Pipeline](#architecture-du-pipeline)
3. [Prérequis](#prérequis)
4. [Installation](#installation)
5. [Utilisation Rapide](#utilisation-rapide)
6. [Guide Détaillé](#guide-détaillé)
7. [Modes d'Exécution](#modes-dexécution)
8. [Topics ROS](#topics-ros)
9. [Dépannage](#dépannage)
10. [Fichiers Générés](#fichiers-générés)

---

## 🎯 Introduction

Ce système d'automatisation orchestre le pipeline complet de **réarrangement autonome d'objets** utilisant le robot Tiago dans un environnement Gazebo simulé. Il intègre :

- **Vision par ordinateur** (caméra Xtion RGB-D)
- **Intelligence Artificielle** (Modèles Hugging Face : Mask R-CNN, CLIP, Stable Diffusion)
- **Contrôle robotique** (MoveIt!, contrôleurs Tiago)

### Workflow du Pipeline

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  1. CAPTURE     │ ───▶ │  2. PIPELINE IA │ ───▶ │  3. COMMANDE    │
│  (capture.py)   │      │ (run_pipeline.py)│      │  (command.py)   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
       │                        │                        │
       ▼                        ▼                        ▼
  Images RGB/D           Positions objets          Mouvement robot
```

---

## 🏗️ Architecture du Pipeline

### Étape 1 : Capture d'Images (`capture.py`)

- Positionne la tête et le torse du robot Tiago
- Capture les images RGB via `/xtion/rgb/image_raw`
- Capture les images de profondeur via `/xtion/depth_registered/image_raw`
- Sauvegarde les données avec métadonnées et calibration caméra

### Étape 2 : Pipeline IA (`run_pipeline.py`)

Le pipeline IA exécute 3 sous-étapes :

1. **Détection d'objets** (Mask R-CNN) → `detections_input.json`
2. **Génération d'image cible** (ControlNet/Stable Diffusion) → `img_generated.png`
3. **Calcul des positions finales** → `final_positions.json`

### Étape 3 : Commande Robot (`command.py`)

- Charge les positions calculées depuis le JSON
- Utilise la profondeur pour la conversion 3D
- Planifie et exécute les mouvements via MoveIt!
- Déplace le bras vers les objets cibles

---

## ✅ Prérequis

### Environnement Docker

```bash
# L'environnement Docker Tiago doit être construit et en cours d'exécution
./build.sh      # Construire l'image Docker
./server.sh     # Lancer le serveur (terminal 1)
./client.sh     # Lancer un client (terminal 2, 3, ...)
```

### Dépendances ROS

- ROS Noetic / Melodic
- Gazebo 11+
- MoveIt!
- TIAGo packages PAL Robotics

### Dépendances Python

```bash
# Dans le conteneur Docker
cd ~/ros_ws/workspace
pip3 install -r scripts/requirements.txt
pip3 install -r pipeline/requirements.txt
```

---

## 🚀 Installation

### 1. Construire le Workspace

```bash
# Dans le conteneur Docker
cd ~/ros_ws/workspace
catkin_make -DCATKIN_ENABLE_TESTING=OFF -DDISABLE_PAL_FLAGS=ON
source devel/setup.bash
```

### 2. Rendre les scripts exécutables

```bash
chmod +x ~/ros_ws/workspace/scripts/automation_node.py
chmod +x ~/ros_ws/workspace/scripts/capture.py
chmod +x ~/ros_ws/workspace/scripts/command.py
```

### 3. Vérifier l'installation

```bash
# Vérifier que le script est accessible
python3 ~/ros_ws/workspace/scripts/automation_node.py --help
```

---

## ⚡ Utilisation Rapide

### Méthode 1 : Script Direct (Recommandée)

```bash
# Terminal 1 : Lancer Gazebo avec Tiago
source /opt/pal/gallium/setup.bash
cd ~/ros_ws/workspace/src
roslaunch tiago_gazebo.launch

# Terminal 2 : Lancer le pipeline complet
source ~/ros_ws/workspace/devel/setup.bash
cd ~/ros_ws/workspace/scripts
python3 automation_node.py
```

### Méthode 2 : Via rosrun

```bash
# Terminal 2 : Après avoir sourcé le workspace
rosrun scripts automation_node.py
```

### Méthode 3 : Via roslaunch

```bash
# Terminal 2 : Lancer via le fichier launch
roslaunch src/tiago_automation.launch
```

---

## 📖 Guide Détaillé

### Étape par Étape

#### 1. Préparation de l'Environnement

```bash
# Sur la machine hôte
./server.sh     # Terminal 1 - Serveur Docker
./client.sh     # Terminal 2 - Client 1 (Gazebo)
./client.sh     # Terminal 3 - Client 2 (Automation)
```

#### 2. Lancement de Gazebo

```bash
# Terminal 2 (dans le conteneur)
source /opt/pal/gallium/setup.bash
source ~/ros_ws/workspace/devel/setup.bash
cd ~/ros_ws/workspace/src
roslaunch tiago_gazebo.launch
```

Attendez que Gazebo soit complètement chargé (vous verrez le robot Tiago et la table avec les objets).

#### 3. Lancement du Pipeline d'Automatisation

```bash
# Terminal 3 (dans le conteneur)
source ~/ros_ws/workspace/devel/setup.bash
cd ~/ros_ws/workspace/scripts

# Option A : Pipeline complet
python3 automation_node.py

# Option B : Pipeline complet sans attendre Gazebo
python3 automation_node.py --no-wait

# Option C : Une seule étape
python3 automation_node.py --mode capture
```

#### 4. Observation du Résultat

Le script affichera :
- ✅ Le statut de chaque étape
- ⏱️ Le temps d'exécution
- 📁 Les fichiers générés
- 🎉 Le résumé final

---

## 🎛️ Modes d'Exécution

### Mode Complet (par défaut)

```bash
python3 automation_node.py --mode full
# ou simplement
python3 automation_node.py
```

Exécute les 3 étapes en séquence : Capture → Pipeline IA → Commande Robot

### Mode Capture Uniquement

```bash
python3 automation_node.py --mode capture
```

Utile pour :
- Tester la caméra
- Capturer de nouvelles images
- Déboguer les problèmes de vision

### Mode Pipeline IA Uniquement

```bash
python3 automation_node.py --mode pipeline
```

Utile pour :
- Tester les modèles IA
- Re-traiter des images existantes
- Déboguer la détection/génération

### Mode Commande Robot Uniquement

```bash
python3 automation_node.py --mode command
```

Utile pour :
- Tester le mouvement du robot
- Re-exécuter une commande avec des positions existantes
- Déboguer le contrôle MoveIt!

### Option --no-wait

```bash
python3 automation_node.py --no-wait
```

Désactive l'attente automatique que Gazebo soit prêt.

---

## 📡 Topics ROS

Le nœud d'automatisation publie sur les topics suivants :

| Topic | Type | Description |
|-------|------|-------------|
| `/tiago/automation_status` | `std_msgs/String` | Statut en temps réel du pipeline |
| `/tiago/current_step` | `std_msgs/String` | Étape en cours d'exécution |
| `/tiago/automation_complete` | `std_msgs/Bool` | Signal de fin du pipeline |

### Écouter les Topics

```bash
# Dans un nouveau terminal
rostopic echo /tiago/automation_status
rostopic echo /tiago/current_step
```

---

## 🔧 Dépannage

### Problème : "Script non trouvé"

```bash
# Vérifier les chemins
ls -la ~/ros_ws/workspace/scripts/
ls -la ~/ros_ws/workspace/pipeline/

# Vérifier les permissions
chmod +x ~/ros_ws/workspace/scripts/*.py
```

### Problème : "Topics Gazebo non disponibles"

```bash
# Vérifier que Gazebo est lancé
rostopic list | grep xtion

# Lancer avec --no-wait si nécessaire
python3 automation_node.py --no-wait
```

### Problème : "Erreur MoveIt!"

```bash
# Vérifier que les contrôleurs sont chargés
rosservice list | grep arm

# Vérifier l'état du robot
rostopic echo /joint_states
```

### Problème : "Erreur de dépendances Python"

```bash
# Installer les dépendances
pip3 install opencv-python numpy rospy
pip3 install -r ~/ros_ws/workspace/pipeline/requirements.txt
```

### Problème : "Timeout sur une étape"

Les timeouts par défaut sont :
- Capture : 60 secondes
- Pipeline IA : 300 secondes (5 minutes)
- Commande : 120 secondes

Si le pipeline IA prend plus de temps (téléchargement de modèles, GPU lent), vous pouvez modifier `STEP_CONFIG` dans `automation_node.py`.

---

## 📁 Fichiers Générés

### Images Capturées

```
~/ros_ws/data/
├── rgb_images/
│   └── scene_YYYYMMDD_HHMMSS_rgb.png
├── depth_images/
│   ├── scene_YYYYMMDD_HHMMSS_depth.png
│   └── scene_YYYYMMDD_HHMMSS_depth.npz
└── calibration/
    ├── camera_calibration.json
    └── metadata_YYYYMMDD_HHMMSS.json
```

### Sorties du Pipeline IA

```
~/ros_ws/workspace/pipeline/outputs/
├── detections_input.json       # Positions initiales des objets
├── img_generated.png           # Image cible générée
├── final_positions.json        # Positions finales pour le robot
└── debug_detected_positions.png # Image de debug
```

### Format des Fichiers JSON

#### detections_input.json
```json
[
  {
    "label": "plate",
    "x_pixel": 320,
    "y_pixel": 240,
    "confidence": 0.95
  },
  ...
]
```

#### final_positions.json
```json
{
  "objects": [
    {
      "label": "plate",
      "initial_position": {"x": 0.5, "y": 0.0, "z": 0.8},
      "final_position": {"x": 0.6, "y": 0.1, "z": 0.8}
    },
    ...
  ]
}
```

---

## 🏷️ Structure du Projet

```
VA50-SUJET5/
├── workspace/
│   ├── scripts/
│   │   ├── automation_node.py    # 🆕 Script d'automatisation principal
│   │   ├── capture.py            # Capture d'images Tiago
│   │   ├── command.py            # Commande du robot
│   │   └── requirements.txt
│   ├── pipeline/
│   │   ├── run_pipeline.py       # Pipeline IA principal
│   │   ├── src/
│   │   │   ├── detect_objects.py
│   │   │   ├── img-gene.py
│   │   │   └── generated_image_to_positions.py
│   │   ├── data/
│   │   └── outputs/
│   └── src/
│       ├── tiago_gazebo.launch
│       ├── tiago_automation.launch  # 🆕 Launch file d'automatisation
│       └── va50/
├── build.sh
├── server.sh
├── client.sh
└── README.md
```

---

## 👥 Équipe

| Rôle | Responsabilité |
|------|----------------|
| **R1** - Ingénieur Robotique | Simulation Gazebo, contrôle Tiago |
| **R2** - Ingénieur IA & ML | Pipeline Hugging Face, détection, génération |
| **R3** - Ingénieur Logiciel & Intégration | Automatisation, orchestration, documentation |

---

## 📞 Support

Pour toute question ou problème :
1. Consultez la section [Dépannage](#dépannage)
2. Vérifiez les logs ROS : `rosnode info /tiago_automation_node`
3. Ouvrez une issue sur GitHub

---

## 📄 Licence

MIT License - Projet VA50 Vision Artificielle et Systèmes Autonomes
