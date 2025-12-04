# Guide de Dépannage - Système de Détection d'Objets

## 🔧 Problèmes Courants et Solutions

### 1. Installation et Configuration

#### Problème: `pip install` échoue avec des erreurs de dépendances

**Solution 1**: Mettre à jour pip
```bash
pip3 install --upgrade pip setuptools wheel
```

**Solution 2**: Installer les dépendances système manquantes
```bash
sudo apt-get update
sudo apt-get install -y python3-dev build-essential
```

**Solution 3**: Installer sans dépendances optionnelles
```bash
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip3 install transformers pillow opencv-python
```

#### Problème: `catkin_make` échoue

**Solution**: S'assurer que tous les fichiers Python sont bien dans les bons dossiers
```bash
cd ~/ros_ws
rm -rf build/ devel/
catkin_make clean
catkin_make
source devel/setup.bash
```

### 2. Téléchargement du Modèle

#### Problème: Le téléchargement du modèle est très lent

**Explication**: Le modèle DETR fait ~160 MB, cela peut prendre quelques minutes.

**Solutions**:
- Utiliser une connexion plus rapide
- Télécharger une seule fois, le modèle sera en cache
- Alternative: utiliser un modèle plus léger
  ```bash
  # Dans download_model.py, changer pour:
  download_model("hustvl/yolos-tiny")  # Seulement ~25 MB
  ```

#### Problème: Erreur "Connection timeout" lors du téléchargement

**Solution 1**: Augmenter le timeout
```bash
export HF_HUB_DOWNLOAD_TIMEOUT=600  # 10 minutes
python3 download_model.py
```

**Solution 2**: Télécharger manuellement depuis un autre ordinateur
1. Sur un autre PC avec bonne connexion:
   ```bash
   pip install transformers
   python -c "from transformers import DetrForObjectDetection; DetrForObjectDetection.from_pretrained('facebook/detr-resnet-50')"
   ```
2. Copier le cache Hugging Face: `~/.cache/huggingface/hub/`
3. Le transférer vers `~/ros_ws/models/` dans le conteneur

#### Problème: "Model not found locally"

**Solution**: Vérifier le chemin du modèle
```bash
ls -la ~/ros_ws/models/facebook_detr-resnet-50/
```

Si le dossier est vide:
```bash
cd ~/ros_ws/src/image_bridge/scripts
python3 download_model.py
```

### 3. Exécution du Nœud ROS

#### Problème: "roslaunch: command not found"

**Solution**: Source le setup ROS
```bash
source /opt/ros/noetic/setup.bash
source ~/ros_ws/devel/setup.bash
```

Ajouter à `~/.bashrc` pour permanence:
```bash
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
echo "source ~/ros_ws/devel/setup.bash" >> ~/.bashrc
```

#### Problème: Le nœud démarre mais crash immédiatement

**Solution 1**: Vérifier les logs
```bash
cat ~/.ros/log/latest/image_processing_node*.log
```

**Solution 2**: Lancer en mode debug
```bash
roslaunch image_bridge image_processing.launch --screen
```

**Solution 3**: Vérifier les imports Python
```bash
python3 -c "from image_bridge.local_model_handler import LocalModelHandler"
```

#### Problème: "ImportError: No module named 'transformers'"

**Solution**: Réinstaller les dépendances
```bash
cd ~/ros_ws/src/image_bridge
pip3 install -r requirements.txt --upgrade
```

### 4. Détection d'Objets

#### Problème: Aucun objet n'est détecté

**Causes possibles**:

1. **Seuil de confiance trop élevé**
   ```xml
   <!-- Dans image_processing.launch, réduire à: -->
   <param name="confidence_threshold" value="0.5" />
   ```

2. **Images de mauvaise qualité**
   - Vérifier l'éclairage dans Gazebo
   - Vérifier que la caméra fonctionne:
     ```bash
     rosrun image_view image_view image:=/xtion/rgb/image_raw
     ```

3. **Objets hors du champ de vision**
   - Vérifier que la table et les objets sont visibles
   - Ajuster les angles de capture dans `capture.py`

4. **Classes non supportées**
   - Le modèle DETR détecte 91 classes COCO
   - Vérifier que vos objets sont dans les classes supportées
   - Liste: https://gist.github.com/AruniRC/7b3dadd004da04c80198557db5da4bda

#### Problème: Trop de faux positifs

**Solution 1**: Augmenter le seuil de confiance
```xml
<param name="confidence_threshold" value="0.85" />
```

**Solution 2**: Filtrer les classes dans le code
Éditer `local_model_handler.py`:
```python
self.target_classes = [
    'fork', 'knife', 'spoon',  # Seulement ces classes
]
```

#### Problème: Détections imprécises (boîtes mal placées)

**Causes**:
- Résolution d'image trop basse
- Objets trop petits ou lointains
- Occlusion (objets cachés)

**Solutions**:
- Augmenter la hauteur du torse du robot (plus proche)
- Améliorer l'éclairage de la scène
- Utiliser un modèle plus précis (DETR-101 au lieu de DETR-50)

### 5. Performance

#### Problème: Le traitement est très lent

**Sur CPU**:
```python
# Éditer local_model_handler.py pour réduire la résolution
def detect_objects(self, image, confidence_threshold=0.7):
    # Ajouter avant le traitement:
    max_size = 480  # Au lieu de la taille originale
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.LANCZOS)
```

**Avec GPU disponible**:
```bash
# Vérifier que CUDA est détecté
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Si False mais GPU présent, réinstaller PyTorch avec CUDA:
pip3 uninstall torch torchvision
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

#### Problème: "CUDA out of memory"

**Solution**: Forcer l'utilisation du CPU
```bash
export CUDA_VISIBLE_DEVICES=""
roslaunch image_bridge image_processing.launch
```

Ou éditer `local_model_handler.py`:
```python
self.device = torch.device("cpu")  # Ligne ~29
```

### 6. Communication ROS

#### Problème: Le service `/tiago/process_captured_images` n'existe pas

**Solution**: Vérifier que le nœud tourne
```bash
# Lister les nœuds actifs
rosnode list

# Si image_processing_node n'apparaît pas:
roslaunch image_bridge image_processing.launch

# Vérifier les services
rosservice list | grep tiago
```

#### Problème: Le topic `/tiago/object_detections` ne publie rien

**Cause**: Mode batch vs temps réel

**Solutions**:
1. **Mode batch**: Appeler le service explicitement
   ```bash
   rosservice call /tiago/process_captured_images "{}"
   ```

2. **Mode temps réel**: Vérifier que le nœud s'abonne à la caméra
   ```bash
   rostopic info /xtion/rgb/image_raw
   # Devrait montrer image_processing_node comme subscriber
   ```

#### Problème: "No images available" lors du service call

**Solution**: S'assurer qu'il y a des images à traiter
```bash
ls ~/ros_ws/data/images/*.png

# Si vide, capturer d'abord:
cd ~/ros_ws/scripts
python3 capture.py
```

### 7. Visualisation

#### Problème: Impossible de voir les images annotées

**Solution 1**: Utiliser image_view
```bash
rosrun image_view image_view image:=/tiago/annotated_image
```

**Solution 2**: Ouvrir directement les fichiers
```bash
eog ~/ros_ws/data/results/annotated_*.png
```

**Solution 3**: Si dans Docker sans X11
```bash
# Depuis l'hôte, monter le dossier et ouvrir
ls workspace/data/results/
```

#### Problème: RViz ne démarre pas

**Solution**: Vérifier X11 forwarding
```bash
echo $DISPLAY
xhost +local:docker  # Sur l'hôte
```

### 8. Intégration avec Capture

#### Problème: Les images capturées sont noires

**Solution**: Vérifier que Gazebo est lancé et que le robot voit la scène
```bash
# Vérifier le stream caméra
rostopic hz /xtion/rgb/image_raw

# Visualiser
rosrun image_view image_view image:=/xtion/rgb/image_raw
```

#### Problème: Le robot ne bouge pas pendant la capture

**Solution**: Vérifier les controllers
```bash
rostopic list | grep controller
rostopic info /head_controller/command
rostopic info /torso_controller/command
```

Si les topics n'existent pas, le monde Gazebo n'est peut-être pas le bon.

### 9. Erreurs Spécifiques

#### "RuntimeError: CUDA error: out of memory"
→ Voir section 5 (Performance)

#### "OSError: [Errno 28] No space left on device"
```bash
# Libérer de l'espace
rm -rf ~/.cache/huggingface/hub/models--*/.cache
docker system prune -a
```

#### "FileNotFoundError: config.json"
→ Le modèle n'est pas complètement téléchargé, re-télécharger

#### "cv2.error: OpenCV(4.x.x) ... error: (-215:Assertion failed)"
→ Image corrompue ou format invalide, vérifier les fichiers PNG

### 10. Validation et Tests

#### Comment vérifier que tout fonctionne?

**Test complet**:
```bash
cd ~/ros_ws/src/image_bridge/scripts
python3 test_setup.py
```

Tous les tests doivent être ✅ PASS

**Test manuel rapide**:
```bash
# 1. Vérifier le modèle
python3 -c "from image_bridge.local_model_handler import LocalModelHandler; h=LocalModelHandler(); print('OK' if h.load_detection_model() else 'FAIL')"

# 2. Vérifier ROS
rosnode list | grep image_processing

# 3. Vérifier les services
rosservice list | grep tiago

# 4. Test de détection
rosservice call /tiago/process_captured_images "{}"
```

## 📞 Obtenir de l'aide

Si le problème persiste:

1. **Collecter les informations**:
   ```bash
   # Versions
   python3 --version
   pip3 list | grep -E "torch|transformers|opencv"
   
   # Logs ROS
   cat ~/.ros/log/latest/image_processing_node*.log
   
   # État du système
   free -h  # RAM disponible
   df -h    # Espace disque
   ```

2. **Vérifier la documentation**:
   - [README_FR.md](README_FR.md) - Documentation principale
   - [QUICKSTART_FR.md](workspace/src/image_bridge/QUICKSTART_FR.md) - Guide rapide

3. **Créer une issue** sur GitHub avec:
   - Description du problème
   - Messages d'erreur complets
   - Logs pertinents
   - Étapes pour reproduire

## 🎓 Ressources Supplémentaires

- **DETR Paper**: https://arxiv.org/abs/2005.12872
- **Hugging Face Transformers**: https://huggingface.co/docs/transformers
- **PyTorch**: https://pytorch.org/docs/stable/index.html
- **ROS Tutorials**: http://wiki.ros.org/ROS/Tutorials
- **Tiago Documentation**: https://docs.pal-robotics.com/tiago-single/

---

**Dernière mise à jour**: Décembre 2024
