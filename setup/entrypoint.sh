#!/bin/bash

DEFAULT_ARGS=""

INFERENCE_ARGS=${INFERENCE_ARGS:-$DEFAULT_ARGS}

exec python3 video_processor.py $INFERENCE_ARGS