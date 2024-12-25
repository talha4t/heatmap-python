from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

app = FastAPI()

class HeatMapRequest(BaseModel):
    imageUrl: str
    jsonData: list

@app.post("/api/getHeatMap")
async def generate_heatmap(request: HeatMapRequest):
    # Step 1: Download the image
    try:
        response = requests.get(request.imageUrl)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load image: {str(e)}")
    
    # Step 2: Generate the heatmap data
    width, height = image.size
    heatmap_array = np.zeros((height, width))
    
    for point in request.jsonData:
        x = int(point["x"] * width / 100)
        y = int(point["y"] * height / 100)
        # Ensure x and y are within bounds
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        heatmap_array[y, x] += 1  # Increment intensity at this point
    
    # Step 3: Create the heatmap
    plt.figure(figsize=(8, 8))
    plt.imshow(image, alpha=0.7)
    plt.imshow(heatmap_array, cmap='jet', alpha=0.5)
    plt.axis("off")

    # Step 4: Save the heatmap to a file
    heatmap_path = "heatmap_output.png"
    plt.savefig(heatmap_path, bbox_inches="tight", pad_inches=0)
    plt.close()
    
    # Step 5: Return the image as a file response
    return FileResponse(heatmap_path, media_type="image/png", filename="heatmap_output.png")
