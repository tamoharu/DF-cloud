#!/bin/bash

if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "Error: GCP credentials not found at $GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
fi

echo "Python version:"
python3 --version
echo "Python path: $(which python3)"
echo "Pip version: $(pip3 --version)"

echo "Starting processing in mode: $PROCESS_MODE"
echo "Using GCP credentials from: $GOOGLE_APPLICATION_CREDENTIALS"
echo "Arguments: $INFERENCE_ARGS"

case "$PROCESS_MODE" in
    "video")
        exec python3 video_processor.py $INFERENCE_ARGS
        ;;
    "swap")
        exec python3 swap_processor.py $INFERENCE_ARGS
        ;;
    *)
        echo "Error: Invalid PROCESS_MODE. Must be 'video' or 'swap'"
        exit 1
        ;;
esac