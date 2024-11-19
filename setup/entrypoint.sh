#!/bin/bash

# Check for GCP credentials
if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "Error: GCP credentials not found at $GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
fi

# Show environment information
echo "Starting video processing with arguments: $INFERENCE_ARGS"
echo "Using GCP credentials from: $GOOGLE_APPLICATION_CREDENTIALS"

# Execute the main application
exec python3 video_processor.py $INFERENCE_ARGS