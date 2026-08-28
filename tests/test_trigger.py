from app.config import Config
from app.trigger import Detection, extract_detections, find_trigger


class FakeBox:
    def __init__(self, class_id, confidence, xyxy):
        self.cls = [class_id]
        self.conf = [confidence]
        self.xyxy = [xyxy]


class FakeResult:
    def __init__(self, boxes, names):
        self.boxes = boxes
        self.names = names


NAMES = {0: "Person", 1: "German Trashbin"}


def make_config(**overrides):
    return Config(**overrides)


def test_extract_detections_filters_low_confidence():
    result = FakeResult(
        boxes=[
            FakeBox(0, 0.9, (0, 0, 10, 10)),
            FakeBox(1, 0.2, (0, 0, 10, 10)),
        ],
        names=NAMES,
    )

    detections = extract_detections(result, confidence_threshold=0.5)

    assert len(detections) == 1
    assert detections[0].class_name == "Person"
    assert detections[0].confidence == 0.9


def test_extract_detections_maps_class_names():
    result = FakeResult(boxes=[FakeBox(1, 0.9, (0, 0, 10, 10))], names=NAMES)

    detections = extract_detections(result, confidence_threshold=0.5)

    assert detections[0].class_name == "German Trashbin"


def test_extract_detections_no_boxes_returns_empty():
    result = FakeResult(boxes=None, names=NAMES)

    assert extract_detections(result, confidence_threshold=0.5) == []


def test_detection_center():
    detection = Detection("Person", 0.9, (0, 0, 10, 20))

    assert detection.center == (5, 10)


def test_find_trigger_requires_both_classes():
    config = make_config()
    person = Detection("Person", 0.9, (0, 0, 10, 10))

    assert find_trigger([person], 640, 640, config) is None


def test_find_trigger_fires_within_threshold():
    config = make_config(trigger_max_pixels=60, trigger_max_fraction=0.1)
    trashbin = Detection("German Trashbin", 0.9, (0, 0, 10, 10))  # center (5, 5)
    person = Detection("Person", 0.9, (20, 20, 40, 40))  # center (30, 30): dx=25, dy=25

    event = find_trigger([trashbin, person], 640, 640, config)

    assert event is not None
    assert event.person is person
    assert event.trashbin is trashbin
    assert event.dx == 25
    assert event.dy == 25


def test_find_trigger_none_just_outside_threshold():
    config = make_config(trigger_max_pixels=60, trigger_max_fraction=0.1)
    trashbin = Detection("German Trashbin", 0.9, (0, 0, 10, 10))  # center (5, 5)
    # dx = 66 > threshold_x = max(60, 0.1*640=64) = 64
    person = Detection("Person", 0.9, (66, 0, 76, 10))

    assert find_trigger([trashbin, person], 640, 640, config) is None


def test_find_trigger_ignores_person_above_or_left_of_bin():
    config = make_config()
    trashbin = Detection("German Trashbin", 0.9, (100, 100, 110, 110))
    person = Detection("Person", 0.9, (0, 0, 10, 10))  # above and left

    assert find_trigger([trashbin, person], 640, 640, config) is None


def test_find_trigger_threshold_scales_with_frame_size():
    config = make_config(trigger_max_pixels=10, trigger_max_fraction=0.5)
    trashbin = Detection("German Trashbin", 0.9, (0, 0, 10, 10))  # center (5, 5)
    # On a 200px-wide frame, threshold_x = max(10, 0.5*200=100) = 100; dx=90 fits.
    person = Detection("Person", 0.9, (90, 0, 100, 10))

    assert find_trigger([trashbin, person], 200, 200, config) is not None
