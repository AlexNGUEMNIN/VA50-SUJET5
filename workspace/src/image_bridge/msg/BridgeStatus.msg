# BridgeStatus.msg - Status message for image bridge operations

# Header with timestamp
std_msgs/Header header

# Status of the bridge
string status  # "idle", "capturing", "processing", "sending", "error"

# Current operation
string operation  # e.g., "capture_scene", "request_generation", etc.

# Number of images in buffer
int32 buffer_size

# Last error message (empty if no error)
string error_message

# Statistics
int32 total_images_processed
float32 last_operation_duration  # in seconds
