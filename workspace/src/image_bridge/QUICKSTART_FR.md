# Guide Rapide : Modèle Local Hugging Face

## 🚀 Démarrage Rapide (5 minutes)

### 1. Installation
```bash
cd ~/ros_ws/src/image_bridge
pip3 install -r requirements.txt
cd ~/ros_ws
catkin_make
source devel/setup.bash
```

### 2. Télécharger le modèle
```bash
cd ~/ros_ws/src/image_bridge/scripts
python3 download_model.py
```
⏱️ Cela prend environ 2-3 minutes (téléchargement de ~160 MB)

### 3. Utiliser le système

#### Option A : Traiter des images déjà capturées
```bash
# Terminal 1 : Lancer le nœud de traitement
roslaunch image_bridge image_processing.launch

# Terminal 2 : Traiter toutes les images
rosservice call /tiago/process_captured_images "{}"
```

#### Option B : Pipeline complet avec Tiago
```bash
# Terminal 1 : Lancer Gazebo
source /opt/pal/gallium/setup.bash
roslaunch tiago_gazebo tiago_gazebo.launch world:=pick_and_place

# Terminal 2 : Capturer des images
cd ~/ros_ws/scripts
python3 capture.py

# Terminal 3 : Lancer le traitement
roslaunch image_bridge image_processing.launch

# Terminal 4 : Traiter les images capturées
rosservice call /tiago/process_captured_images "{}"
```

## 📂 Où trouver les résultats ?

- **Images annotées** : `~/ros_ws/data/results/annotated_*.png`
- **Résultats JSON** : `~/ros_ws/data/results/detection_results_*.json`
- **Images capturées** : `~/ros_ws/data/images/*.png`

## 🔍 Vérification rapide

```bash
# Vérifier que le nœud fonctionne
rosnode list | grep image_processing

# Voir les détections en temps réel
rostopic echo /tiago/object_detections

# Visualiser l'image annotée
rosrun image_view image_view image:=/tiago/annotated_image
```

## ⚠️ Problèmes courants

### "Model not found"
```bash
# Re-télécharger le modèle
cd ~/ros_ws/src/image_bridge/scripts
python3 download_model.py
```

### "No images available"
```bash
# Vérifier qu'il y a des images à traiter
ls ~/ros_ws/data/images/*.png
```

### Performances lentes
```bash
# Utiliser un seuil de confiance plus élevé (moins de détections)
# Éditer image_processing.launch :
# <param name="confidence_threshold" value="0.8" />
```

## 📖 Documentation complète

Voir [README_FR.md](../../README_FR.md) pour :
- Architecture détaillée
- Configuration avancée
- Dépannage complet
- API et intégration

## 🎯 Objets détectables

Le modèle peut détecter :
- ✅ Fourchettes (fork)
- ✅ Couteaux (knife)
- ✅ Cuillères (spoon)
- ✅ Assiettes (plate, dish)
- ✅ Bols (bowl)
- ✅ Tasses/Verres (cup, wine glass)
- ✅ Table (dining table)

## 💡 Astuce

Pour tester rapidement avec vos propres images :
```bash
# Copier une image dans le dossier
cp /chemin/vers/image.png ~/ros_ws/data/images/

# Traiter
rosservice call /tiago/process_captured_images "{}"

# Voir le résultat
eog ~/ros_ws/data/results/annotated_image.png
```

---

**Besoin d'aide ?** Consultez [README_FR.md](../../README_FR.md) section Dépannage
