#!/bin/bash
# Installation script for local Hugging Face model system
# Run this inside the Docker container

set -e  # Exit on error

echo "============================================================"
echo "Installation du système de détection d'objets"
echo "Modèle local Hugging Face pour Tiago"
echo "============================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in container
if [ ! -d "/home/pal/ros_ws" ]; then
    echo -e "${YELLOW}Attention: Ce script doit être exécuté dans le conteneur Docker${NC}"
    echo "Utilisez: ./client.sh"
    exit 1
fi

echo -e "${GREEN}✓ Conteneur Docker détecté${NC}"
echo ""

# Step 1: Install Python dependencies
echo "============================================================"
echo "Étape 1/5: Installation des dépendances Python"
echo "============================================================"
cd ~/ros_ws/src/image_bridge

if pip3 install -r requirements.txt; then
    echo -e "${GREEN}✓ Dépendances Python installées${NC}"
else
    echo -e "${RED}✗ Échec de l'installation des dépendances${NC}"
    exit 1
fi
echo ""

# Step 2: Create necessary directories
echo "============================================================"
echo "Étape 2/5: Création des répertoires"
echo "============================================================"
mkdir -p ~/ros_ws/models
mkdir -p ~/ros_ws/data/images
mkdir -p ~/ros_ws/data/results
echo -e "${GREEN}✓ Répertoires créés${NC}"
echo "  - ~/ros_ws/models (modèles)"
echo "  - ~/ros_ws/data/images (images capturées)"
echo "  - ~/ros_ws/data/results (résultats)"
echo ""

# Step 3: Build ROS workspace
echo "============================================================"
echo "Étape 3/5: Compilation du workspace ROS"
echo "============================================================"
cd ~/ros_ws
if catkin_make; then
    echo -e "${GREEN}✓ Workspace compilé${NC}"
else
    echo -e "${RED}✗ Échec de la compilation${NC}"
    exit 1
fi
echo ""

# Step 4: Download model
echo "============================================================"
echo "Étape 4/5: Téléchargement du modèle de détection"
echo "============================================================"
echo "Cela peut prendre 2-3 minutes..."
echo ""

cd ~/ros_ws/src/image_bridge/scripts
if python3 download_model.py; then
    echo -e "${GREEN}✓ Modèle téléchargé${NC}"
else
    echo -e "${YELLOW}⚠ Le modèle n'a pas pu être téléchargé maintenant${NC}"
    echo "  Vous pourrez le télécharger plus tard avec:"
    echo "  python3 ~/ros_ws/src/image_bridge/scripts/download_model.py"
fi
echo ""

# Step 5: Run tests
echo "============================================================"
echo "Étape 5/5: Tests de validation"
echo "============================================================"
cd ~/ros_ws/src/image_bridge/scripts
if python3 test_setup.py; then
    echo -e "${GREEN}✓ Tous les tests sont passés${NC}"
else
    echo -e "${YELLOW}⚠ Certains tests ont échoué${NC}"
    echo "  Vérifiez les messages ci-dessus"
fi
echo ""

# Final instructions
echo "============================================================"
echo "Installation terminée!"
echo "============================================================"
echo ""
echo -e "${GREEN}Le système est prêt à être utilisé.${NC}"
echo ""
echo "Prochaines étapes:"
echo ""
echo "1. Lancer Gazebo avec Tiago (dans un terminal):"
echo "   source /opt/pal/gallium/setup.bash"
echo "   roslaunch tiago_gazebo tiago_gazebo.launch world:=pick_and_place"
echo ""
echo "2. Capturer des images (dans un autre terminal):"
echo "   cd ~/ros_ws/scripts"
echo "   python3 capture.py"
echo ""
echo "3. Lancer le nœud de traitement (dans un autre terminal):"
echo "   source ~/ros_ws/devel/setup.bash"
echo "   roslaunch image_bridge image_processing.launch"
echo ""
echo "4. Traiter les images capturées (dans un autre terminal):"
echo "   source ~/ros_ws/devel/setup.bash"
echo "   rosservice call /tiago/process_captured_images \"{}\""
echo ""
echo "5. Voir les résultats dans:"
echo "   ~/ros_ws/data/results/"
echo ""
echo "Pour plus d'informations, consultez:"
echo "  - README_FR.md (documentation complète)"
echo "  - workspace/src/image_bridge/QUICKSTART_FR.md (guide rapide)"
echo ""
echo "============================================================"
