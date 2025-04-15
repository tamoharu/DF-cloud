import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from typing import Dict
from pathlib import Path

import video_processor
import swap_processor

app = FastAPI()


class DetectVideoRequestBody(BaseModel):
    video_path: str


class SwapVideoRequestBody(BaseModel):
    user_dir: str
    video_dir: str


class ResponseBody(BaseModel):
    success: bool


@app.post("/detect-video", response_model=ResponseBody)
async def detect_video(request: DetectVideoRequestBody):
    video_path = request.video_path
    try:
        await video_processor.run(video_path)
        return ResponseBody(success=True)
    except Exception as e:
        return ResponseBody(success=False)


@app.post("/swap-video", response_model=ResponseBody)
async def swap_video(request: SwapVideoRequestBody):
    user_dir = request.user_dir
    video_dir = request.video_dir
    try:
        await swap_processor.run(user_dir, video_dir)
        return ResponseBody(success=True)
    except Exception as e:
        return ResponseBody(success=False)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)