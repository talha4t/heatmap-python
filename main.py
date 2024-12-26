from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import requests
from io import BytesIO
from PIL import Image
import base64
import folium
from folium.plugins import HeatMap
import os

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
    
    # Step 2: Get the image size and prepare coordinates
    width, height = image.size
    heatmap_data = []

    for point in request.jsonData:
        try:
            x = point["x"] * width / 100  # Convert x percentage to pixel
            y = point["y"] * height / 100  # Convert y percentage to pixel
            heatmap_data.append([height - y, x])  # Invert y-axis for image coordinate system
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid data format in JSON")
    
    # Step 3: Save the image as a base64-encoded string
    image_path = "base_image.png"
    image.save(image_path)
    with open(image_path, "rb") as img_file:
        encoded_image = base64.b64encode(img_file.read()).decode()

    # Step 4: Create a Folium map overlay
    map_center = [height / 2, width / 2]
    folium_map = folium.Map(location=map_center, zoom_start=0, width="100%", height="100%", max_bounds=True)

    # Overlay the image
    folium.raster_layers.ImageOverlay(
        image=f"data:image/png;base64,{encoded_image}",
        bounds=[[0, 0], [height, width]],
        opacity=1,
    ).add_to(folium_map)

    # Add heatmap layer
    HeatMap(heatmap_data, radius=15, blur=20, max_zoom=1).add_to(folium_map)

    # Save the Folium map to an HTML file
    output_html = "heatmap_output.html"
    folium_map.save(output_html)

    # Step 5: Return the HTML file as a response
    return FileResponse(output_html, media_type="text/html", filename="heatmap_output.html")
