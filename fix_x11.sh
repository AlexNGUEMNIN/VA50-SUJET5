#!/bin/bash
# Script to fix X11 permissions for Docker Gazebo GUI

echo "Fixing X11 permissions for Docker containers..."

# Allow local connections to X server
xhost +local:root

echo "X11 permissions fixed!"
echo "You can now run ./server.sh and ./client.sh"
