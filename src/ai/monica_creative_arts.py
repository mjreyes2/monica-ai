"""
Monica AI - Creative Arts System

Gives Monica the ability to:
1. Generate images using Stable Diffusion (local) or Pillow (always available)
2. Paint and draw pictures programmatically (shapes, patterns, art styles)
3. Create simple animations / GIF movies
4. Apply artistic filters to photos
5. Generate art from text descriptions

All processing is LOCAL - no cloud APIs needed.
Outputs saved to: data/creative_output/
"""

import os
import math
import time
import random
import logging
import colorsys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger("Monica.CreativeArts")

# Try imports
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class MonicaCreativeArts:
    """
    Monica's creative and artistic capabilities.
    
    Generates images, paintings, drawings, animations, and artistic filters.
    Uses PIL/Pillow for drawing + optional Stable Diffusion for AI generation.
    """

    # Art style presets
    STYLES = {
        'abstract': {'colors': 'vibrant', 'shapes': 'organic', 'complexity': 'high'},
        'minimalist': {'colors': 'muted', 'shapes': 'geometric', 'complexity': 'low'},
        'impressionist': {'colors': 'warm', 'shapes': 'soft', 'complexity': 'medium'},
        'geometric': {'colors': 'bold', 'shapes': 'geometric', 'complexity': 'medium'},
        'watercolor': {'colors': 'pastel', 'shapes': 'organic', 'complexity': 'medium'},
        'pixel_art': {'colors': 'bright', 'shapes': 'blocky', 'complexity': 'low'},
        'mandala': {'colors': 'gradient', 'shapes': 'radial', 'complexity': 'high'},
        'landscape': {'colors': 'natural', 'shapes': 'organic', 'complexity': 'high'},
        'portrait_sketch': {'colors': 'monochrome', 'shapes': 'lines', 'complexity': 'high'},
        'pop_art': {'colors': 'neon', 'shapes': 'bold', 'complexity': 'medium'},
    }

    COLOR_PALETTES = {
        'vibrant': [(255, 50, 50), (50, 255, 50), (50, 50, 255), (255, 255, 50), (255, 50, 255), (50, 255, 255)],
        'pastel': [(255, 182, 193), (176, 224, 230), (255, 218, 185), (221, 160, 221), (152, 251, 152), (255, 255, 224)],
        'warm': [(255, 99, 71), (255, 140, 0), (255, 215, 0), (178, 34, 34), (210, 105, 30), (244, 164, 96)],
        'cool': [(70, 130, 180), (100, 149, 237), (72, 61, 139), (0, 128, 128), (95, 158, 160), (176, 196, 222)],
        'monochrome': [(30, 30, 30), (60, 60, 60), (100, 100, 100), (150, 150, 150), (200, 200, 200), (240, 240, 240)],
        'neon': [(255, 0, 102), (0, 255, 102), (102, 0, 255), (255, 255, 0), (0, 255, 255), (255, 102, 0)],
        'earth': [(139, 90, 43), (85, 107, 47), (34, 139, 34), (160, 82, 45), (210, 180, 140), (107, 142, 35)],
        'sunset': [(255, 94, 77), (255, 154, 0), (255, 206, 0), (153, 0, 76), (102, 0, 102), (255, 127, 80)],
    }

    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            try:
                from config.settings import config
                base_dir = Path(str(config.BASE_DIR))
            except Exception:
                base_dir = Path(".")

        self.base_dir = base_dir
        self.output_dir = base_dir / "data" / "creative_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Sub-directories
        (self.output_dir / "paintings").mkdir(exist_ok=True)
        (self.output_dir / "drawings").mkdir(exist_ok=True)
        (self.output_dir / "animations").mkdir(exist_ok=True)
        (self.output_dir / "filters").mkdir(exist_ok=True)
        (self.output_dir / "generated").mkdir(exist_ok=True)

        # Stable Diffusion (optional)
        self._sd_pipeline = None
        self._sd_available = False
        self._init_stable_diffusion()

        self.creation_count = 0
        logger.info("[ART] Creative Arts System initialized")
        logger.info(f"[ART] Output: {self.output_dir}")
        logger.info(f"[ART] PIL={HAS_PIL}, NumPy={HAS_NUMPY}, CV2={HAS_CV2}, StableDiffusion={self._sd_available}")

    def _init_stable_diffusion(self):
        """Try to load Stable Diffusion for AI image generation."""
        try:
            from diffusers import StableDiffusionPipeline
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            # Use a small model that works on CPU too
            self._sd_pipeline = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            ).to(device)
            self._sd_available = True
            logger.info("[ART] Stable Diffusion loaded (AI image generation available)")
        except Exception:
            logger.info("[ART] Stable Diffusion not available (using procedural art)")

    # ==================== Image Generation ====================

    def generate_image(self, prompt: str, width: int = 512, height: int = 512,
                       style: str = 'abstract') -> Optional[str]:
        """
        Generate an image from a text description.
        Uses Stable Diffusion if available, otherwise procedural generation.
        
        Returns: path to saved image
        """
        if not HAS_PIL:
            logger.error("[ART] PIL not available")
            return None

        if self._sd_available:
            return self._generate_sd(prompt, width, height)
        else:
            return self._generate_procedural(prompt, width, height, style)

    def _generate_sd(self, prompt: str, width: int, height: int) -> Optional[str]:
        """Generate image using Stable Diffusion."""
        try:
            result = self._sd_pipeline(prompt, width=width, height=height, num_inference_steps=25)
            img = result.images[0]
            path = self._save_image(img, "generated", prompt[:30])
            return path
        except Exception as e:
            logger.error(f"[ART] SD generation error: {e}")
            return self._generate_procedural(prompt, width, height, 'abstract')

    def _generate_procedural(self, prompt: str, width: int, height: int,
                              style: str) -> Optional[str]:
        """Generate art procedurally based on prompt keywords."""
        # Analyze prompt to pick style
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ['landscape', 'mountain', 'ocean', 'nature', 'sunset', 'sky']):
            return self.paint_landscape(width, height, prompt)
        elif any(w in prompt_lower for w in ['portrait', 'face', 'person', 'sketch']):
            return self.draw_portrait_sketch(width, height)
        elif any(w in prompt_lower for w in ['mandala', 'pattern', 'symmetr']):
            return self.paint_mandala(width, height)
        elif any(w in prompt_lower for w in ['geometric', 'abstract', 'shape']):
            return self.paint_abstract(width, height, style)
        elif any(w in prompt_lower for w in ['pixel', '8-bit', 'retro']):
            return self.create_pixel_art(width, height, prompt)
        elif any(w in prompt_lower for w in ['flower', 'garden', 'plant', 'tree']):
            return self.paint_flowers(width, height)
        else:
            return self.paint_abstract(width, height, style)

    # ==================== Painting Styles ====================

    def paint_abstract(self, width: int = 800, height: int = 600,
                       style: str = 'abstract') -> Optional[str]:
        """Create an abstract painting."""
        if not HAS_PIL:
            return None
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        palette_name = self.STYLES.get(style, {}).get('colors', 'vibrant')
        colors = self.COLOR_PALETTES.get(palette_name, self.COLOR_PALETTES['vibrant'])

        # Background gradient
        for y in range(height):
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * y / height)
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * y / height)
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Draw random shapes
        for _ in range(random.randint(15, 40)):
            shape_type = random.choice(['circle', 'rectangle', 'line', 'arc'])
            color = random.choice(colors)
            alpha_color = color + (random.randint(80, 200),)
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            size = random.randint(20, min(width, height) // 3)

            if shape_type == 'circle':
                draw.ellipse([x1, y1, x1+size, y1+size], fill=color, outline=None)
            elif shape_type == 'rectangle':
                draw.rectangle([x1, y1, x1+size, y1+int(size*0.7)], fill=color)
            elif shape_type == 'line':
                x2 = random.randint(0, width)
                y2 = random.randint(0, height)
                draw.line([(x1, y1), (x2, y2)], fill=color, width=random.randint(1, 8))
            elif shape_type == 'arc':
                draw.arc([x1, y1, x1+size, y1+size], 
                         random.randint(0, 180), random.randint(180, 360),
                         fill=color, width=random.randint(2, 6))

        return self._save_image(img, "paintings", f"abstract_{style}")

    def paint_landscape(self, width: int = 800, height: int = 600,
                        prompt: str = "") -> Optional[str]:
        """Create a procedural landscape painting."""
        if not HAS_PIL:
            return None
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)

        is_sunset = 'sunset' in prompt.lower()
        is_night = 'night' in prompt.lower()

        # Sky
        if is_sunset:
            sky_colors = [(255, 94, 77), (255, 165, 0), (255, 215, 0)]
        elif is_night:
            sky_colors = [(10, 10, 40), (20, 20, 80), (30, 30, 60)]
        else:
            sky_colors = [(135, 206, 235), (100, 180, 220), (70, 130, 180)]

        horizon = int(height * 0.55)
        for y in range(horizon):
            t = y / horizon
            idx = min(int(t * (len(sky_colors) - 1)), len(sky_colors) - 2)
            local_t = (t * (len(sky_colors) - 1)) - idx
            c1, c2 = sky_colors[idx], sky_colors[min(idx+1, len(sky_colors)-1)]
            r = int(c1[0] + (c2[0] - c1[0]) * local_t)
            g = int(c1[1] + (c2[1] - c1[1]) * local_t)
            b = int(c1[2] + (c2[2] - c1[2]) * local_t)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Stars for night
        if is_night:
            for _ in range(100):
                sx, sy = random.randint(0, width), random.randint(0, horizon)
                brightness = random.randint(150, 255)
                draw.point((sx, sy), fill=(brightness, brightness, brightness))

        # Mountains
        mountain_color = (80, 100, 60) if not is_night else (30, 40, 50)
        points = [(0, horizon)]
        x = 0
        while x < width:
            peak_h = random.randint(int(height * 0.15), int(height * 0.45))
            points.append((x, horizon - peak_h))
            x += random.randint(40, 120)
        points.append((width, horizon))
        if len(points) > 2:
            draw.polygon(points, fill=mountain_color)

        # Ground
        ground_color = (34, 139, 34) if not is_night else (20, 60, 20)
        for y in range(horizon, height):
            t = (y - horizon) / (height - horizon)
            r = int(ground_color[0] * (1 - t * 0.3))
            g = int(ground_color[1] * (1 - t * 0.3))
            b = int(ground_color[2] * (1 - t * 0.3))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Sun/Moon
        if is_sunset:
            sun_y = horizon - 40
            draw.ellipse([width//2 - 30, sun_y - 30, width//2 + 30, sun_y + 30],
                         fill=(255, 200, 50))
        elif is_night:
            draw.ellipse([width - 100, 40, width - 60, 80], fill=(220, 220, 240))

        return self._save_image(img, "paintings", "landscape")

    def paint_mandala(self, width: int = 800, height: int = 800) -> Optional[str]:
        """Create a mandala pattern."""
        if not HAS_PIL:
            return None
        img = Image.new('RGB', (width, height), (20, 20, 40))
        draw = ImageDraw.Draw(img)

        cx, cy = width // 2, height // 2
        colors = self.COLOR_PALETTES['sunset'] + self.COLOR_PALETTES['cool']
        num_petals = random.choice([6, 8, 12, 16])

        for ring in range(8, 0, -1):
            radius = int(min(cx, cy) * ring / 9)
            color = colors[ring % len(colors)]

            for i in range(num_petals):
                angle = (2 * math.pi * i) / num_petals
                px = cx + int(radius * math.cos(angle))
                py = cy + int(radius * math.sin(angle))
                petal_size = radius // 4

                draw.ellipse([px - petal_size, py - petal_size,
                              px + petal_size, py + petal_size], fill=color)

                # Connecting lines
                next_angle = (2 * math.pi * (i + 1)) / num_petals
                nx = cx + int(radius * math.cos(next_angle))
                ny = cy + int(radius * math.sin(next_angle))
                draw.line([(px, py), (nx, ny)], fill=color, width=2)

            # Ring circle
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                         outline=color, width=2)

        return self._save_image(img, "paintings", "mandala")

    def paint_flowers(self, width: int = 800, height: int = 600) -> Optional[str]:
        """Paint a garden of flowers."""
        if not HAS_PIL:
            return None
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)

        # Sky and ground
        for y in range(height):
            if y < height * 0.4:
                t = y / (height * 0.4)
                draw.line([(0, y), (width, y)],
                          fill=(int(135 + 50*t), int(206 - 30*t), int(235 - 50*t)))
            else:
                t = (y - height * 0.4) / (height * 0.6)
                draw.line([(0, y), (width, y)],
                          fill=(int(34 + 30*t), int(139 - 40*t), int(34 + 20*t)))

        # Draw flowers
        flower_colors = [(255, 100, 100), (255, 200, 50), (200, 100, 255),
                         (255, 150, 200), (100, 200, 255), (255, 255, 100)]

        for _ in range(random.randint(10, 25)):
            fx = random.randint(30, width - 30)
            fy = random.randint(int(height * 0.35), height - 30)
            stem_h = random.randint(40, 100)

            # Stem
            draw.line([(fx, fy), (fx, fy + stem_h)], fill=(34, 120, 34), width=3)

            # Petals
            color = random.choice(flower_colors)
            petal_size = random.randint(8, 18)
            for angle_deg in range(0, 360, 60):
                angle = math.radians(angle_deg)
                px = fx + int(petal_size * math.cos(angle))
                py = fy + int(petal_size * math.sin(angle))
                draw.ellipse([px - petal_size//2, py - petal_size//2,
                              px + petal_size//2, py + petal_size//2], fill=color)

            # Center
            draw.ellipse([fx - 5, fy - 5, fx + 5, fy + 5], fill=(255, 220, 50))

        return self._save_image(img, "paintings", "flowers")

    def draw_portrait_sketch(self, width: int = 500, height: int = 600) -> Optional[str]:
        """Draw a simple portrait sketch."""
        if not HAS_PIL:
            return None
        img = Image.new('RGB', (width, height), (245, 240, 230))
        draw = ImageDraw.Draw(img)
        cx, cy = width // 2, height // 2
        color = (40, 40, 40)

        # Head outline
        head_w, head_h = 140, 180
        draw.ellipse([cx - head_w, cy - head_h - 30, cx + head_w, cy + head_h - 30],
                     outline=color, width=3)

        # Eyes
        eye_y = cy - 60
        for ex in [cx - 50, cx + 50]:
            draw.ellipse([ex - 20, eye_y - 10, ex + 20, eye_y + 10], outline=color, width=2)
            draw.ellipse([ex - 6, eye_y - 6, ex + 6, eye_y + 6], fill=color)

        # Eyebrows
        draw.arc([cx - 75, eye_y - 35, cx - 25, eye_y - 10], 190, 350, fill=color, width=2)
        draw.arc([cx + 25, eye_y - 35, cx + 75, eye_y - 10], 190, 350, fill=color, width=2)

        # Nose
        draw.line([(cx, eye_y + 15), (cx - 5, cy + 10)], fill=color, width=2)
        draw.arc([cx - 15, cy, cx + 15, cy + 20], 20, 160, fill=color, width=2)

        # Mouth
        mouth_y = cy + 50
        draw.arc([cx - 30, mouth_y - 10, cx + 30, mouth_y + 15], 10, 170, fill=color, width=2)

        # Neck
        draw.line([(cx - 25, cy + head_h - 40), (cx - 30, cy + head_h + 40)], fill=color, width=2)
        draw.line([(cx + 25, cy + head_h - 40), (cx + 30, cy + head_h + 40)], fill=color, width=2)

        return self._save_image(img, "drawings", "portrait_sketch")

    def create_pixel_art(self, width: int = 256, height: int = 256,
                         prompt: str = "") -> Optional[str]:
        """Create pixel art."""
        if not HAS_PIL:
            return None
        pixel_size = 8
        pw, ph = width // pixel_size, height // pixel_size
        img = Image.new('RGB', (pw, ph))
        pixels = img.load()

        colors = self.COLOR_PALETTES['neon']

        # Simple pattern based on prompt
        for y in range(ph):
            for x in range(pw):
                # Create a pattern
                val = (x * 7 + y * 13 + x * y) % len(colors)
                if (x + y) % 3 == 0:
                    pixels[x, y] = colors[val]
                else:
                    pixels[x, y] = (20, 20, 30)

        # Scale up
        img = img.resize((width, height), Image.NEAREST)
        return self._save_image(img, "drawings", "pixel_art")

    # ==================== Animation / GIF ====================

    def create_animation(self, frames: int = 30, width: int = 400,
                         height: int = 400, style: str = 'pulse') -> Optional[str]:
        """Create a GIF animation."""
        if not HAS_PIL:
            return None

        images = []
        colors = self.COLOR_PALETTES['vibrant']

        for frame in range(frames):
            t = frame / frames
            img = Image.new('RGB', (width, height), (10, 10, 20))
            draw = ImageDraw.Draw(img)
            cx, cy = width // 2, height // 2

            if style == 'pulse':
                # Pulsing circles
                for i in range(5):
                    phase = (t + i * 0.2) % 1.0
                    radius = int(phase * min(cx, cy))
                    color = colors[i % len(colors)]
                    alpha = int(255 * (1 - phase))
                    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                                 outline=color, width=3)

            elif style == 'spiral':
                # Spinning spiral
                for i in range(200):
                    angle = t * 2 * math.pi + i * 0.1
                    r = i * 0.8
                    x = cx + int(r * math.cos(angle))
                    y = cy + int(r * math.sin(angle))
                    color = colors[i % len(colors)]
                    draw.ellipse([x-2, y-2, x+2, y+2], fill=color)

            elif style == 'wave':
                # Color wave
                for x in range(width):
                    for band in range(3):
                        y_offset = int(30 * math.sin(x * 0.05 + t * 2 * math.pi + band))
                        y = cy + y_offset + (band - 1) * 40
                        color = colors[band % len(colors)]
                        draw.ellipse([x-1, y-3, x+1, y+3], fill=color)

            images.append(img)

        # Save as GIF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"animation_{style}_{timestamp}.gif"
        path = str(self.output_dir / "animations" / filename)
        images[0].save(path, save_all=True, append_images=images[1:],
                       duration=50, loop=0, optimize=True)
        self.creation_count += 1
        logger.info(f"[ART] Animation saved: {path}")
        return path

    # ==================== Artistic Filters ====================

    def apply_filter(self, image_path: str, filter_name: str = 'oil_painting') -> Optional[str]:
        """Apply an artistic filter to an existing image."""
        if not HAS_PIL:
            return None
        try:
            img = Image.open(image_path)
        except Exception as e:
            logger.error(f"[ART] Cannot open image: {e}")
            return None

        if filter_name == 'oil_painting':
            img = img.filter(ImageFilter.SMOOTH_MORE)
            img = img.filter(ImageFilter.SMOOTH_MORE)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.5)
        elif filter_name == 'sketch':
            img = img.convert('L')
            img = img.filter(ImageFilter.FIND_EDGES)
            img = img.convert('RGB')
        elif filter_name == 'watercolor':
            img = img.filter(ImageFilter.BLUR)
            img = img.filter(ImageFilter.SMOOTH_MORE)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.3)
        elif filter_name == 'vintage':
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.5)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.9)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
        elif filter_name == 'neon':
            img = img.filter(ImageFilter.FIND_EDGES)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(3.0)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(2.0)
        elif filter_name == 'emboss':
            img = img.filter(ImageFilter.EMBOSS)
        elif filter_name == 'pop_art':
            img = img.quantize(colors=8).convert('RGB')
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(2.0)

        return self._save_image(img, "filters", f"filtered_{filter_name}")

    def stylize_photo_as_art(self, image_path: str, style: str = 'oil_painting') -> Optional[str]:
        """Turn a photo into art using OpenCV if available."""
        if HAS_CV2:
            try:
                img = cv2.imread(image_path)
                if img is None:
                    return self.apply_filter(image_path, style)

                if style == 'oil_painting':
                    result = cv2.xphoto.oilPainting(img, 7, 1) if hasattr(cv2, 'xphoto') else img
                elif style == 'cartoon':
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    gray = cv2.medianBlur(gray, 7)
                    edges = cv2.adaptiveThreshold(gray, 255,
                                                   cv2.ADAPTIVE_THRESH_MEAN_C,
                                                   cv2.THRESH_BINARY, 9, 9)
                    color = cv2.bilateralFilter(img, 9, 300, 300)
                    result = cv2.bitwise_and(color, color, mask=edges)
                elif style == 'pencil':
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    inv = 255 - gray
                    blur = cv2.GaussianBlur(inv, (21, 21), 0)
                    result = cv2.divide(gray, 255 - blur, scale=256)
                    result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
                else:
                    return self.apply_filter(image_path, style)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = str(self.output_dir / "filters" / f"stylized_{style}_{timestamp}.png")
                cv2.imwrite(path, result)
                self.creation_count += 1
                return path

            except Exception as e:
                logger.warning(f"[ART] CV2 stylize error: {e}")

        return self.apply_filter(image_path, style)

    # ==================== Utility ====================

    def _save_image(self, img: 'Image.Image', subfolder: str, prefix: str) -> str:
        """Save an image with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_prefix = "".join(c for c in prefix if c.isalnum() or c in '_- ')[:40]
        filename = f"{clean_prefix}_{timestamp}.png"
        path = str(self.output_dir / subfolder / filename)
        img.save(path, 'PNG')
        self.creation_count += 1
        logger.info(f"[ART] Saved: {path}")
        return path

    def get_available_styles(self) -> List[str]:
        """Get list of available art styles."""
        return list(self.STYLES.keys())

    def get_available_filters(self) -> List[str]:
        """Get list of available image filters."""
        return ['oil_painting', 'sketch', 'watercolor', 'vintage', 'neon',
                'emboss', 'pop_art', 'cartoon', 'pencil']

    def get_status(self) -> Dict[str, Any]:
        """Get creative system status."""
        return {
            'pil_available': HAS_PIL,
            'cv2_available': HAS_CV2,
            'stable_diffusion': self._sd_available,
            'output_dir': str(self.output_dir),
            'creations_count': self.creation_count,
            'styles': list(self.STYLES.keys()),
            'filters': self.get_available_filters(),
        }


# Singleton
_arts = None

def get_creative_arts() -> MonicaCreativeArts:
    """Get or create the creative arts singleton."""
    global _arts
    if _arts is None:
        _arts = MonicaCreativeArts()
    return _arts
