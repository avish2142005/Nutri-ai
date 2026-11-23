"""KrishiNetra Disease Severity Estimation Engine.

Combines color space segmentation (HSV & LAB), morphological contour analysis,
and lesion-to-leaf area ratio quantification to categorize severity into:
- Healthy
- Mild (1% - 15% leaf damage)
- Moderate (15% - 35% leaf damage)
- Severe (> 35% leaf damage)
"""

import io
import base64
import logging
from typing import Dict, Any, Tuple, Optional, Union
from PIL import Image
import numpy as np
import cv2

logger = logging.getLogger("KrishiNetra.Severity")


class DiseaseSeverityAnalyzer:
    """Estimates plant disease severity by segmenting leaf tissue and detecting lesions."""

    def __init__(self):
        # HSV ranges for leaf segmentation (green spectrum)
        # H: 25 to 90 (yellow-green to deep green), S: 30 to 255, V: 30 to 255
        self.leaf_lower_hsv = np.array([25, 30, 30], dtype=np.uint8)
        self.leaf_upper_hsv = np.array([95, 255, 255], dtype=np.uint8)

        # HSV ranges for disease lesions:
        # 1. Necrotic spots (brown/black/dark red)
        self.necrotic_lower_hsv1 = np.array([0, 40, 20], dtype=np.uint8)
        self.necrotic_upper_hsv1 = np.array([24, 255, 180], dtype=np.uint8)
        self.necrotic_lower_hsv2 = np.array([160, 40, 20], dtype=np.uint8)
        self.necrotic_upper_hsv2 = np.array([180, 255, 180], dtype=np.uint8)

        # 2. Chlorotic lesions (yellowing / halo)
        self.chlorotic_lower_hsv = np.array([18, 60, 100], dtype=np.uint8)
        self.chlorotic_upper_hsv = np.array([32, 255, 255], dtype=np.uint8)

    def _load_cv_image(self, image_input: Union[str, bytes, Image.Image, np.ndarray]) -> np.ndarray:
        """Convert various input types to BGR OpenCV numpy image."""
        if isinstance(image_input, str):
            bgr = cv2.imread(image_input)
            if bgr is None:
                raise ValueError(f"Could not load image from path: {image_input}")
            return bgr
        elif isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if bgr is None:
                raise ValueError("Could not decode image from bytes.")
            return bgr
        elif isinstance(image_input, Image.Image):
            rgb = np.array(image_input.convert("RGB"))
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            if len(image_input.shape) == 2:
                return cv2.cvtColor(image_input, cv2.COLOR_GRAY2BGR)
            elif image_input.shape[2] == 4:
                return cv2.cvtColor(image_input, cv2.COLOR_RGBA2BGR)
            return image_input
        else:
            raise TypeError(f"Unsupported image type: {type(image_input)}")

    def analyze(
        self,
        image_input: Union[str, bytes, Image.Image, np.ndarray],
        predicted_condition: Optional[str] = None,
        generate_annotated_mask: bool = True
    ) -> Dict[str, Any]:
        """Analyze plant leaf and compute precise disease severity metrics.
        
        Args:
            image_input: File path, bytes, PIL Image, or numpy array.
            predicted_condition: Optional predicted class name (e.g. 'Tomato___Early_blight' or 'Tomato___healthy').
            generate_annotated_mask: If True, returns a base64 encoded image showing lesion overlays.
            
        Returns:
            Dictionary with severity level, affected percentage, lesion count, and visual mask.
        """
        img_bgr = self._load_cv_image(image_input)
        h, w = img_bgr.shape[:2]

        # Resize for consistent morphological kernel behavior while preserving aspect ratio
        max_dim = 600
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            h, w = img_bgr.shape[:2]

        # Convert to HSV and LAB color spaces
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)

        # 1. Segment Entire Leaf Canopy
        # Leaf includes healthy green + chlorotic yellow + necrotic brown areas
        mask_green = cv2.inRange(hsv, self.leaf_lower_hsv, self.leaf_upper_hsv)
        mask_yellow = cv2.inRange(hsv, self.chlorotic_lower_hsv, self.chlorotic_upper_hsv)
        mask_necrotic1 = cv2.inRange(hsv, self.necrotic_lower_hsv1, self.necrotic_upper_hsv1)
        mask_necrotic2 = cv2.inRange(hsv, self.necrotic_lower_hsv2, self.necrotic_upper_hsv2)

        # Combined leaf mask
        leaf_mask = cv2.bitwise_or(mask_green, mask_yellow)
        leaf_mask = cv2.bitwise_or(leaf_mask, cv2.bitwise_or(mask_necrotic1, mask_necrotic2))

        # Morphological clean up on leaf mask
        kernel_leaf = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel_leaf)
        leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN, kernel_leaf)

        total_leaf_pixels = int(cv2.countNonZero(leaf_mask))
        total_image_pixels = h * w

        # Fallback if leaf mask didn't isolate well (e.g. extreme white background)
        if total_leaf_pixels < 0.05 * total_image_pixels:
            # Assume leaf occupies central 60% if background is already pure studio
            leaf_mask = np.ones((h, w), dtype=np.uint8) * 255
            total_leaf_pixels = total_image_pixels

        # 2. Segment Lesion Regions (Necrosis + Chlorosis) confined inside the leaf mask
        lesion_mask_raw = cv2.bitwise_or(mask_yellow, cv2.bitwise_or(mask_necrotic1, mask_necrotic2))
        lesion_mask = cv2.bitwise_and(lesion_mask_raw, lesion_mask_raw, mask=leaf_mask)

        # Morphological filtering to discard single-pixel sensor noise
        kernel_lesion = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        lesion_mask = cv2.morphologyEx(lesion_mask, cv2.MORPH_OPEN, kernel_lesion)
        lesion_mask = cv2.morphologyEx(lesion_mask, cv2.MORPH_CLOSE, kernel_lesion)

        # Find individual lesion contours
        contours, _ = cv2.findContours(lesion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter tiny specks (< 12 pixels)
        significant_contours = [c for c in contours if cv2.contourArea(c) >= 12]
        lesion_count = len(significant_contours)

        # Recalculate clean lesion pixel count
        clean_lesion_mask = np.zeros_like(lesion_mask)
        cv2.drawContours(clean_lesion_mask, significant_contours, -1, 255, -1)
        total_lesion_pixels = int(cv2.countNonZero(clean_lesion_mask))

        # 3. Calculate Affected Percentage
        if total_leaf_pixels > 0:
            affected_percentage = round((total_lesion_pixels / total_leaf_pixels) * 100.0, 2)
        else:
            affected_percentage = 0.0

        # Override if known healthy class
        if predicted_condition and "healthy" in predicted_condition.lower():
            if affected_percentage < 15.0:
                affected_percentage = 0.0
                lesion_count = 0
            severity_level = "Healthy"
            severity_code = 0
            canopy_risk = "Negligible"
            action_urgency = "Normal Monitoring"

        # 4. Severity Classification
        if affected_percentage < 1.0:
            severity_level = "Healthy"
            severity_code = 0
            canopy_risk = "Negligible"
            action_urgency = "Normal Monitoring"
        elif affected_percentage <= 15.0:
            severity_level = "Mild"
            severity_code = 1
            canopy_risk = "Low"
            action_urgency = "Proactive Cultural Scouting"
        elif affected_percentage <= 35.0:
            severity_level = "Moderate"
            severity_code = 2
            canopy_risk = "Guarded"
            action_urgency = "Biological / Targeted Intervention"
        else:
            severity_level = "Severe"
            severity_code = 3
            canopy_risk = "Critical"
            action_urgency = "Immediate Containment & Quarantine"

        severity_score = min(1.0, round(affected_percentage / 50.0, 3))

        # 5. Generate Visual Diagnostic Overlay
        overlay_base64 = None
        if generate_annotated_mask:
            annotated = img_bgr.copy()
            # Draw semi-transparent red/yellow highlight over lesions
            color_mask = np.zeros_like(img_bgr)
            # Mild yellow or severe red highlight
            highlight_color = (0, 0, 255) if severity_code >= 2 else (0, 165, 255)
            color_mask[clean_lesion_mask > 0] = highlight_color
            annotated = cv2.addWeighted(annotated, 1.0, color_mask, 0.45, 0)

            # Draw contour outlines
            cv2.drawContours(annotated, significant_contours, -1, (0, 255, 255), 1)

            # Add HUD banner
            banner_text = f"Severity: {severity_level} ({affected_percentage}%) | Spots: {lesion_count}"
            cv2.rectangle(annotated, (0, 0), (w, 32), (20, 20, 20), -1)
            cv2.putText(
                annotated,
                banner_text,
                (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            # Encode to JPEG base64
            _, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
            overlay_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

        return {
            "severity_level": severity_level,
            "severity_code": severity_code,
            "severity_score": severity_score,
            "affected_percentage": affected_percentage,
            "lesion_count": lesion_count,
            "total_leaf_pixels": total_leaf_pixels,
            "total_lesion_pixels": total_lesion_pixels,
            "canopy_spread_risk": canopy_risk,
            "action_urgency": action_urgency,
            "overlay_image": overlay_base64
        }
