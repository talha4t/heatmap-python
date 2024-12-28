from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image, ImageDraw
import base64
import io
import requests

app = FastAPI()

class HeatmapRequest(BaseModel):
    imageUrl: str
    jsonData: list
    point_radius: int = 10
    heatmap_opacity: int = 128


def create_heatmap_from_json(image_url, json_data, point_radius=10, heatmap_opacity=128):
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        image = Image.open(response.raw)

        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        heatmap = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(heatmap)

        for item in json_data:
            x = item['x']
            y = item['y']
            screen_width = item.get('screen_width', image.width)
            screen_height = item.get('screen_height', image.height)
            pixel_x = int(x * image.width / screen_width)
            pixel_y = int(y * image.height / screen_height)

            draw.ellipse(
                [
                    pixel_x - point_radius, pixel_y - point_radius, 
                    pixel_x + point_radius, pixel_y + point_radius
                ],
                fill=(255, 0, 0, heatmap_opacity)
            )

        heatmap_image = Image.alpha_composite(image, heatmap)
        return heatmap_image

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error downloading image: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.post("/api/getHeatMap")
async def generate_heatmap(request: HeatmapRequest):
    try:
        heatmap_image = create_heatmap_from_json(
            image_url=request.imageUrl,
            json_data=request.jsonData,
            point_radius=request.point_radius,
            heatmap_opacity=request.heatmap_opacity
        )

        buffered = io.BytesIO()
        heatmap_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return {"base64_image": img_str}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating heatmap: {e}")
