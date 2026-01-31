"""
Floor Plan Manager
==================
Handles floor plan image and camera-to-map coordinate mapping.
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from PIL import Image
import io
import base64

from .entities import CameraZone


class FloorPlan:
    """
    Manages the floor plan image and camera zone mappings.
    """

    def __init__(self):
        self._image: Optional[Image.Image] = None
        self._image_path: Optional[str] = None
        self._zones: Dict[str, CameraZone] = {}

    @property
    def is_loaded(self) -> bool:
        return self._image is not None

    @property
    def dimensions(self) -> Tuple[int, int]:
        """Returns (width, height) of floor plan."""
        if self._image:
            return self._image.size
        return (0, 0)

    def load_image(self, path: str):
        """Load floor plan image from file."""
        self._image = Image.open(path)
        self._image_path = path

    def load_image_bytes(self, data: bytes, format: str = "PNG"):
        """Load floor plan from bytes (for Streamlit upload)."""
        self._image = Image.open(io.BytesIO(data))

    def get_image(self) -> Optional[Image.Image]:
        """Get the floor plan image."""
        return self._image

    def get_image_base64(self) -> str:
        """Get floor plan as base64 string for web display."""
        if not self._image:
            return ""
        buffer = io.BytesIO()
        self._image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

    # Zone management
    def add_zone(self, zone: CameraZone):
        """Add a camera zone mapping."""
        self._zones[zone.camera_id] = zone

    def get_zone(self, camera_id: str) -> Optional[CameraZone]:
        """Get a camera zone by ID."""
        return self._zones.get(camera_id)

    def get_all_zones(self) -> List[CameraZone]:
        """Get all camera zones."""
        return list(self._zones.values())

    def remove_zone(self, camera_id: str):
        """Remove a camera zone."""
        if camera_id in self._zones:
            del self._zones[camera_id]

    def camera_to_map(self, camera_id: str, cam_x: int, cam_y: int) -> Tuple[int, int]:
        """
        Convert camera coordinates to floor plan coordinates.
        Returns (0, 0) if camera zone not found.
        """
        zone = self._zones.get(camera_id)
        if zone:
            return zone.camera_to_map(cam_x, cam_y)
        return (0, 0)

    # Demo setup
    def setup_demo_zones(self):
        """
        Set up demo camera zones.
        Assumes a floor plan of roughly 800x600 pixels.
        """
        # Corridor camera (left side of map)
        self.add_zone(CameraZone(
            camera_id="cam_corridor",
            camera_name="Corridor A",
            map_x=50, map_y=100,
            map_width=200, map_height=400
        ))

        # Waiting room camera (center of map)
        self.add_zone(CameraZone(
            camera_id="cam_waiting",
            camera_name="Waiting Room",
            map_x=300, map_y=150,
            map_width=250, map_height=300
        ))

        # Triage area camera (right side of map)
        self.add_zone(CameraZone(
            camera_id="cam_triage",
            camera_name="Triage",
            map_x=600, map_y=100,
            map_width=150, map_height=200
        ))

    def create_demo_floor_plan(self) -> Image.Image:
        """
        Create a simple demo floor plan image.
        Used when no floor plan is uploaded.
        """
        from PIL import ImageDraw

        # Create blank floor plan
        img = Image.new('RGB', (800, 600), color='#1a1a2e')
        draw = ImageDraw.Draw(img)

        # Draw rooms/zones
        # Corridor
        draw.rectangle([40, 90, 260, 510], outline='#4a4a6a', width=2)
        draw.text((100, 70), "Corridor A", fill='#8888aa')

        # Waiting room
        draw.rectangle([290, 140, 560, 460], outline='#4a4a6a', width=2)
        draw.text((370, 120), "Waiting Room", fill='#8888aa')

        # Triage
        draw.rectangle([590, 90, 760, 310], outline='#4a4a6a', width=2)
        draw.text((640, 70), "Triage", fill='#8888aa')

        # Treatment rooms
        draw.rectangle([590, 340, 760, 510], outline='#4a4a6a', width=2)
        draw.text((620, 320), "Treatment", fill='#8888aa')

        self._image = img
        return img
