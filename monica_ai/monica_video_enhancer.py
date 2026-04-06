"""
Monica Video Enhancer - ULTRA HIGH QUALITY Video Processing
HDR-like effects, vibrant colors, professional broadcast quality.
Optimized for real-time performance.
"""
import cv2
import numpy as np
from typing import Optional


class VideoEnhancer:
    """
    ULTRA video enhancement for broadcast-quality, vibrant video.
    Features: HDR tone mapping, bloom, vibrant colors, denoising, sharpening.
    """
    
    def __init__(self):
        self.enabled = True
        self.quality_mode = 'ultra'  # 'fast', 'balanced', 'quality', 'ultra'
        
        # ULTRA enhancement settings
        self.contrast = 1.20      # Strong contrast
        self.brightness = 12      # Good brightness
        self.saturation = 1.35    # Vibrant colors
        self.sharpness = 0.5      # Crisp sharpening
        self.bloom_intensity = 0.15  # Subtle bloom/glow
        self.vibrance = 1.2       # Color vibrance
        
        # Pre-create CLAHE for HDR-like effect (stronger settings)
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        self.clahe_color = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(4, 4))
        
        # Sharpening kernel (stronger)
        self.sharpen_kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ], dtype=np.float32)
        
        # Unsharp mask kernel
        self.unsharp_kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ], dtype=np.float32)
        
        # Frame skip for heavy operations
        self.frame_count = 0
        self.cached_lut = self._create_vibrant_lut()
        
        # Denoise settings
        self.denoise_strength = 3
        
        print("[VideoEnhancer] ✨ ULTRA HD mode initialized - Broadcast quality")
    
    def _create_vibrant_lut(self) -> np.ndarray:
        """Create lookup table for vibrant color enhancement."""
        lut = np.zeros((256, 1, 3), dtype=np.uint8)
        for i in range(256):
            # S-curve for contrast
            val = i / 255.0
            # Sigmoid-like curve for punch
            enhanced = 1 / (1 + np.exp(-10 * (val - 0.5)))
            enhanced = int(np.clip(enhanced * 255, 0, 255))
            lut[i, 0, :] = enhanced
        return lut
    
    def _apply_bloom(self, frame: np.ndarray, intensity: float = 0.15) -> np.ndarray:
        """Apply bloom/glow effect to bright areas."""
        # Extract bright areas
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        bright_mask = hsv[:, :, 2] > 200  # High value pixels
        
        # Create bloom layer
        bloom = frame.copy()
        bloom[~bright_mask] = 0
        
        # Blur for glow effect
        bloom = cv2.GaussianBlur(bloom, (21, 21), 0)
        bloom = cv2.GaussianBlur(bloom, (21, 21), 0)  # Double blur for soft glow
        
        # Add bloom to original
        frame = cv2.addWeighted(frame, 1.0, bloom, intensity, 0)
        return frame
    
    def _apply_vibrance(self, frame: np.ndarray, intensity: float = 1.2) -> np.ndarray:
        """Boost less saturated colors more than already saturated ones."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Boost saturation more for less saturated pixels
        sat = hsv[:, :, 1]
        boost = intensity + (1 - sat / 255) * (intensity - 1) * 0.5
        hsv[:, :, 1] = np.clip(sat * boost, 0, 255)
        
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    def enhance(self, frame: np.ndarray) -> np.ndarray:
        """Apply FAST HD enhancements - optimized for real-time with NO LAG."""
        if not self.enabled or frame is None:
            return frame
        
        try:
            self.frame_count += 1
            
            # REMOVED: fastNlMeansDenoisingColored - TOO SLOW (causes major lag)
            # Use bilateral filter instead if needed (much faster)
            
            # 1. FAST contrast/brightness (always - very fast)
            frame = cv2.convertScaleAbs(frame, alpha=self.contrast, beta=self.brightness)
            
            # 2. FAST CLAHE on luminance (optimized)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = self.clahe.apply(lab[:, :, 0])
            frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # 3. FAST saturation boost (single pass)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hsv = hsv.astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * self.saturation, 0, 255)
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.03, 0, 255)  # Slight brightness
            frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            
            # 4. FAST sharpening (unsharp mask - lightweight)
            if self.sharpness > 0 and self.frame_count % 2 == 0:  # Every other frame
                gaussian = cv2.GaussianBlur(frame, (3, 3), 1.0)  # Smaller kernel = faster
                frame = cv2.addWeighted(frame, 1.0 + self.sharpness * 0.5, gaussian, -self.sharpness * 0.5, 0)
            
            return frame
            
        except Exception as e:
            # Fallback to basic enhancement
            return cv2.convertScaleAbs(frame, alpha=self.contrast, beta=self.brightness)
    
    def enhance_fast(self, frame: np.ndarray) -> np.ndarray:
        """Ultra-fast enhancement - minimal processing."""
        if not self.enabled or frame is None:
            return frame
        
        # Just contrast + brightness - super fast
        return cv2.convertScaleAbs(frame, alpha=self.contrast, beta=self.brightness)
    
    def set_quality(self, level: str):
        """Set quality level: 'fast', 'balanced', 'quality', 'ultra'."""
        self.quality_mode = level
        
        if level == 'fast':
            self.contrast = 1.1
            self.brightness = 5
            self.saturation = 1.1
            self.sharpness = 0
            self.bloom_intensity = 0
            self.vibrance = 1.0
            self.denoise_strength = 0
        elif level == 'balanced':
            self.contrast = 1.15
            self.brightness = 8
            self.saturation = 1.2
            self.sharpness = 0.3
            self.bloom_intensity = 0.1
            self.vibrance = 1.1
            self.denoise_strength = 2
        elif level == 'quality':
            self.contrast = 1.18
            self.brightness = 10
            self.saturation = 1.25
            self.sharpness = 0.4
            self.bloom_intensity = 0.12
            self.vibrance = 1.15
            self.denoise_strength = 3
        elif level == 'ultra':
            self.contrast = 1.20
            self.brightness = 12
            self.saturation = 1.35
            self.sharpness = 0.5
            self.bloom_intensity = 0.15
            self.vibrance = 1.2
            self.denoise_strength = 3
        
        print(f"[VideoEnhancer] ✨ Quality set to '{level}'")


# Singleton
_enhancer: Optional[VideoEnhancer] = None

def get_video_enhancer() -> VideoEnhancer:
    global _enhancer
    if _enhancer is None:
        _enhancer = VideoEnhancer()
    return _enhancer


if __name__ == "__main__":
    import time
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    enhancer = VideoEnhancer()
    
    fps_times = []
    
    while True:
        start = time.time()
        ret, frame = cap.read()
        if not ret:
            break
        
        enhanced = enhancer.enhance(frame)
        
        # Calculate FPS
        fps_times.append(time.time() - start)
        if len(fps_times) > 30:
            fps_times.pop(0)
        fps = 1.0 / (sum(fps_times) / len(fps_times))
        
        # Show FPS
        cv2.putText(enhanced, f"FPS: {fps:.1f}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow("Enhanced Feed", enhanced)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('1'):
            enhancer.set_quality('fast')
        elif key == ord('2'):
            enhancer.set_quality('balanced')
        elif key == ord('3'):
            enhancer.set_quality('quality')
    
    cap.release()
    cv2.destroyAllWindows()
