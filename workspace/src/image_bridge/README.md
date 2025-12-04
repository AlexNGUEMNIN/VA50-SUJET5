# Image Bridge Node

ROS middleware node for communication between Tiago robot (Gazebo simulation) and Hugging Face AI models for autonomous object rearrangement.

## Overview

The `image_bridge` node serves as a communication bridge in a pipeline that:
1. Captures images from Tiago's cameras
2. Sends them to AI models for processing (segmentation, captioning, generation)
3. Receives generated images and forwards them to the robot control system
4. Estimates object poses for manipulation

## Features

- **Multiple Camera Support**: Subscribes to RGB and depth camera topics
- **AI Model Integration**: Connects to Hugging Face models via REST API
- **Asynchronous Processing**: Queue-based system for non-blocking AI requests
- **Image Format Conversion**: Handles ROS messages, OpenCV arrays, PIL images, and base64 encoding
- **Circular Buffer**: Maintains history of recent images
- **ROS Services**: Provides services for scene capture, image generation, and pose estimation
- **Status Monitoring**: Publishes real-time status information

## Installation

### Prerequisites

- ROS Noetic
- Python 3.8+
- OpenCV
- cv_bridge

### Dependencies

Install Python dependencies:

```bash
pip3 install requests pillow numpy
```

### Build

```bash
cd ~/ros_ws
catkin_make
source devel/setup.bash
```

## Configuration

### Environment Variables

Set your Hugging Face API token:

```bash
export HUGGINGFACE_API_TOKEN="your_token_here"
```

### Parameters

Edit `config/params.yaml` to customize:

- **Models**: Configure which Hugging Face models to use
- **Topics**: Customize ROS topic names
- **Buffer Size**: Number of images to keep in memory
- **Timeouts**: API request timeouts
- **Debug Settings**: Enable image saving for debugging

## Usage

### Launch the Node

```bash
roslaunch image_bridge image_bridge.launch
```

### With Custom Parameters

```bash
roslaunch image_bridge image_bridge.launch config_file:=/path/to/custom_params.yaml
```

## ROS Interface

### Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/xtion/rgb/image_raw` | `sensor_msgs/Image` | RGB camera feed from Tiago |
| `/xtion/depth/image_raw` | `sensor_msgs/Image` | Depth camera feed from Tiago |
| `/ai_model/generated_image` | `sensor_msgs/Image` | Generated images from AI models |

### Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/image_bridge/to_ai_model` | `sensor_msgs/Image` | Images sent to AI models |
| `/image_bridge/to_robot` | `sensor_msgs/Image` | Processed images for robot |
| `/image_bridge/segmentation_masks` | `sensor_msgs/Image` | Segmentation results |
| `/image_bridge/status` | `image_bridge/BridgeStatus` | Node status information |

### Services

#### `/image_bridge/capture_scene`

Capture current scene and send to AI model.

```bash
rosservice call /image_bridge/capture_scene "capture_rgb: true
capture_depth: true
model_endpoint: ''"
```

#### `/image_bridge/request_generation`

Request image generation from text prompt.

```bash
rosservice call /image_bridge/request_generation "prompt: 'A table with organized objects'
source_image:
  header:
    seq: 0
    stamp: {secs: 0, nsecs: 0}
    frame_id: ''
  height: 0
  width: 0
  encoding: ''
  is_bigendian: 0
  step: 0
  data: []
model_name: ''
guidance_scale: 7.5
num_inference_steps: 50"
```

#### `/image_bridge/get_target_poses`

Get target object poses from current and target images.

```bash
rosservice call /image_bridge/get_target_poses [...]
```

## Architecture

### Pipeline Flow

```
Tiago Camera → image_bridge → Hugging Face API → image_bridge → Robot Control
     ↓              ↓                 ↓                 ↓              ↓
  RGB/Depth    Conversion      AI Processing      Conversion    Pose Commands
```

### Modules

- **config.py**: Configuration management
- **image_utils.py**: Image format conversions (ROS ↔ OpenCV ↔ base64)
- **huggingface_client.py**: Async API client for Hugging Face
- **ros_interface.py**: ROS pub/sub/service management
- **image_bridge_node.py**: Main node orchestration

## Supported AI Models

### Image Segmentation
- Mask R-CNN variants
- Default: `facebook/maskformer-swin-base-coco`

### Image Understanding
- CLIP for zero-shot classification
- Default: `openai/clip-vit-base-patch32`

### Image Captioning
- BLIP and similar models
- Default: `Salesforce/blip-image-captioning-base`

### Image Generation
- Stable Diffusion models
- Default: `stabilityai/stable-diffusion-2-1`

## Troubleshooting

### No images received

Check if Tiago simulation is running and camera topics are publishing:

```bash
rostopic list | grep xtion
rostopic hz /xtion/rgb/image_raw
```

### API errors

Verify your Hugging Face token is set and valid:

```bash
echo $HUGGINGFACE_API_TOKEN
```

Check API status and model availability on Hugging Face website.

### Node crashes

Check logs for detailed error messages:

```bash
rosnode info image_bridge_node
cat ~/.ros/log/latest/image_bridge_node*.log
```

## Development

### Adding New Models

1. Add model ID to `config/params.yaml`
2. Create method in `huggingface_client.py` if needed
3. Update service handlers in `ros_interface.py`

### Debugging

Enable debug image saving:

```yaml
save_debug_images: true
debug_image_path: "~/ros_ws/data/bridge_debug"
```

## License

MIT License

## Authors

Alex NGUEMNIN - VA50 Project

## Acknowledgments

- PAL Robotics for Tiago robot platform
- Hugging Face for AI model infrastructure
- ROS community
