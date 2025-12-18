# VA50-SUJET5 - Réarrangement Autonome d'Objets avec Tiago

Projet de réarrangement autonome d'objets utilisant le robot Tiago et des modèles d'IA Hugging Face.

## 📦 Packages ROS

### Hugging Face Bridge

**Nœud ROS de communication bidirectionnelle entre Tiago et Hugging Face**

Le package `huggingface_bridge` permet au robot Tiago de:
- Envoyer des images capturées aux modèles IA
- Traiter les images avec Mask R-CNN, CLIP et Stable Diffusion
- Récupérer les positions initiales et finales des objets
- Orchestrer le pipeline complet de réarrangement

📖 **Documentation complète**: `workspace/src/huggingface_bridge/README.md`  
🚀 **Démarrage rapide**: `workspace/src/huggingface_bridge/QUICKSTART.md`  
🏗️ **Architecture**: `workspace/src/huggingface_bridge/ARCHITECTURE.md`

**Services ROS disponibles:**
- `/tiago/send_image_to_hf` - Traitement d'image complet
- `/tiago/get_object_positions` - Récupération des positions

**Topics ROS:**
- `/tiago/hf_status` - Statut en temps réel
- `/tiago/detected_objects` - Objets détectés

## 🏗️ Structure du Projet

```
VA50-SUJET5/
├── workspace/
│   ├── pipeline/                       # Pipeline Python IA
│   │   ├── src/
│   │   │   ├── detect_objects.py      # Détection Mask R-CNN
│   │   │   ├── img-gene.py            # Génération Stable Diffusion
│   │   │   └── generated_image_to_positions.py
│   │   └── run_pipeline.py
│   └── src/
│       ├── huggingface_bridge/        # 🆕 Package ROS Bridge
│       │   ├── scripts/
│       │   │   ├── huggingface_bridge_node.py
│       │   │   ├── test_huggingface_bridge.py
│       │   │   └── validate_installation.py
│       │   ├── src/huggingface_bridge/
│       │   │   ├── huggingface_client.py
│       │   │   ├── image_handler.py
│       │   │   └── json_handler.py
│       │   ├── config/
│       │   ├── launch/
│       │   ├── srv/
│       │   └── README.md
│       └── va50/                      # Monde Gazebo
├── build.sh
├── server.sh
└── client.sh
```

## 🚀 Installation Rapide

### 1. Environnement Docker

**Build the Docker image:**

- Run the following command in a terminal
  `./build.sh`

- To force rebuilding the image use the option `-r`

### 2. Installation des Dépendances Hugging Face

**Dans le conteneur Docker:**

```bash
cd ~/ros_ws/workspace/src/huggingface_bridge
pip3 install -r requirements.txt
```

### 3. Compilation du Workspace

```bash
cd ~/ros_ws/workspace
catkin_make
source devel/setup.bash
```

### 4. Validation

```bash
cd ~/ros_ws/workspace/src/huggingface_bridge/scripts
python3 validate_installation.py
```

## Running the container

### Running Docker Containers

- Launch the server by running the following command in a terminal
  `./server.sh`

- Launch as many client as you need by running the following command in a terminal
  `./client.sh`

- The folders `ros`, `workspace` and `share` are automatically mounted in the container, respectively as `/home/pal/.ros`, `/home/pal/ros_ws` and `/home/pal/share`
  This allows editing the workspace and looking through the logs from the development computer. Any file or folder copied to any of these folders will be accessible both from the container and the development computer.

- If the workspace is empty, i.e., only contains an empty folder `src`, run the following command in `/home/pal/ros_ws` inside the container to initialize it 
  `catkin_make -DCATKIN_ENABLE_TESTING=OFF -DDISABLE_PAL_FLAGS=ON`

### Lancer le Système Complet

**Terminal 1: Gazebo avec Tiago**
```bash
source /opt/pal/gallium/setup.bash
roslaunch tiago_gazebo.launch
```

**Terminal 2: Nœud Hugging Face Bridge**
```bash
source ~/ros_ws/workspace/devel/setup.bash
roslaunch huggingface_bridge huggingface_bridge.launch
```

**Terminal 3: Test**
```bash
source ~/ros_ws/workspace/devel/setup.bash
rosservice call /tiago/send_image_to_hf \
  "image_path: '/home/pal/ros_ws/workspace/pipeline/data/images/table_input.png'"
```

## Working with external nodes

- If the ROS master is on a remote computer (e.g., when working with a real robot), set the `ROS_MASTER_URI` by running the following command inside the container (this must be repeated for each client)
  `export ROS_MASTER_URI=http://<MASTER_COMPUTER_IP>:11311`

- You must set `ROS_IP` to the address of the host computer on the same sub-network as the compute hosting the master.

- You may want to disable the firewall
  `sudo ufw disable`

## Read TIAGo handbook

Read the [TIAGo handbook](https://docs.pal-robotics.com/tiago-single/handbook.html) to familiarize yourself with the control of the simulated or real robot

## Working with TIAGo in simulation

- Execute the following commands inside the container
  `source /opt/pal/gallium/`
  `roslaunch tiago_198_gazebo tiago_gazebo.launch`

  This will launch a simulation with the robot in an empty world. If you want to use a existing world you can launch `tiago_mapping.launch` or `tiago_navigation.launch`. The first one will launch the robot in mapping mode, the second one in localization mode (both are in the same world).

- Simulated Hokuyo LIDARs may not work properly from inside the docker. If it is the case run the following command inside the container just before launching gazebo

  `export LIBGL_ALWAYS_SOFTWARE=1`

## Working with the real TIAGo

- Run the following command inside the container (this must be repeated for each client)
  `source ~/.bashrc tiago`
  
  This command will automatically set the `ROS_MASTER_URI` and  `ROS_IP` variables (assuming the development computer is connected to the Tiago in Wifi via the default hotspot, or directly via a ethernet cable)
  
- Connect to the TIAGo computer via ssh using the following command

  `ssh pal@10.68.0.1`

  the password is `pal`

- If the TIAGo computer cannot access the container you may want to disable the firewall on the development PC

  `sudo ufw disable`

## Using JetBrains Gateway to develop with CLion and PyCharm

- Install JetBrains Gateway and run it

- While the container is running, create a new SSH connection with
  - user: pal
  - host: localhost
  - port: 22

- Select `Check Connection and Continue`, password should be left empty

- Select the IDE version and click `Installation options...` to customize Installation path and put `/home/ros/share/JetBrains/RemoteDev/dist`
  Since `/home/ros/share` is a mounted directory, the installed IDEs will remain persistent and won't need to be downloaded each time the container is launched. Also, IDE settings will be kept.

- Enter the project directory `/home/pal/ros_ws/src`

- Click `Download IDE and Connect`

- With CLion you can customize the build path as explained here: https://www.jetbrains.com/help/clion/ros-setup-tutorial.html

---

## 👥 Équipe

**Rôle R3 - Ingénieur Logiciel & Intégration**: AlexNGUEMNIN

## 📄 Licence

MIT License

## 📞 Support

Pour toute question sur le package Hugging Face Bridge:
- Consultez `workspace/src/huggingface_bridge/README.md`
- Ouvrez une issue sur GitHub
