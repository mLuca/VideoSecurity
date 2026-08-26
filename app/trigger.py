"""Detection parsing and proximity-based trigger logic.

A recording event is triggered when a detected "Person" is positioned lower
and further to the right than a detected "German Trashbin" (e.g. someone
reaching into/standing at the bin from behind), within a small proximity
window. The window is the larger of a fixed pixel margin and a fraction of
the frame size, so the check scales with resolution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from app.config import Config


@dataclass
class Detection:
    class_name: str
    confidence: float
    xyxy: tuple[float, float, float, float]

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.xyxy
        return (x1 + x2) / 2, (y1 + y2) / 2


@dataclass
class TriggerEvent:
    person: Detection
    trashbin: Detection
    dx: float
    dy: float
    threshold_x: float
    threshold_y: float


def extract_detections(result, confidence_threshold: float) -> List[Detection]:
    """Convert an ultralytics Result into a flat list of Detections."""
    detections: List[Detection] = []
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return detections

    names = result.names
    for box in boxes:
        confidence = float(box.conf[0])
        if confidence < confidence_threshold:
            continue
        class_id = int(box.cls[0])
        class_name = names.get(class_id, str(class_id))
        x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
        detections.append(Detection(class_name, confidence, (x1, y1, x2, y2)))

    return detections


def find_trigger(
    detections: Sequence[Detection],
    frame_width: int,
    frame_height: int,
    config: Config,
) -> Optional[TriggerEvent]:
    """Return the first person/trashbin pair that satisfies the proximity rule."""
    persons = [d for d in detections if d.class_name == config.person_class_name]
    trashbins = [d for d in detections if d.class_name == config.trashbin_class_name]
    if not persons or not trashbins:
        return None

    threshold_x = max(config.trigger_max_pixels, config.trigger_max_fraction * frame_width)
    threshold_y = max(config.trigger_max_pixels, config.trigger_max_fraction * frame_height)

    for person in persons:
        px, py = person.center
        for trashbin in trashbins:
            bx, by = trashbin.center
            dx = px - bx
            dy = py - by
            # "lower and more to the right" => both offsets positive and within range
            if 0 <= dx <= threshold_x and 0 <= dy <= threshold_y:
                return TriggerEvent(person, trashbin, dx, dy, threshold_x, threshold_y)

    return None
