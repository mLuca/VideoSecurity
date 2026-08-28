import numpy as np
import pytest

import app.recorder as recorder_module
from app.recorder import EventRecorder
from app.trigger import Detection, TriggerEvent


class FakeWriter:
    instances = []

    def __init__(self, path, fourcc, fps, size):
        self.path = path
        self.frames = []
        self.released = False
        FakeWriter.instances.append(self)

    def isOpened(self):
        return True

    def write(self, frame):
        self.frames.append(frame)

    def release(self):
        self.released = True


@pytest.fixture(autouse=True)
def fake_cv2(monkeypatch):
    FakeWriter.instances = []
    imwrite_calls = []
    monkeypatch.setattr(recorder_module.cv2, "imwrite", lambda path, frame: imwrite_calls.append((path, frame)))
    monkeypatch.setattr(recorder_module.cv2, "VideoWriter_fourcc", lambda *args: 1234)
    monkeypatch.setattr(recorder_module.cv2, "VideoWriter", FakeWriter)
    return imwrite_calls


def frame(value=0):
    return np.full((4, 4, 3), value, dtype=np.uint8)


def make_recorder(make_config, **config_overrides):
    config = make_config(**config_overrides)
    return EventRecorder(config, __import__("logging").getLogger("test"), fps=2), config


def make_trigger_event():
    person = Detection("Person", 0.9, (20, 20, 40, 40))
    trashbin = Detection("German Trashbin", 0.9, (0, 0, 10, 10))
    return TriggerEvent(person, trashbin, dx=25, dy=25, threshold_x=64, threshold_y=64)


def test_no_trigger_while_idle_does_nothing(make_config, fake_cv2):
    recorder, _ = make_recorder(make_config)

    def fail():
        raise AssertionError("should not be called")

    recorder.handle_frame(frame(), None, fail, fail)

    assert fake_cv2 == []
    assert FakeWriter.instances == []


def test_trigger_starts_recording_and_saves_trigger_frame(make_config, fake_cv2):
    recorder, config = make_recorder(make_config)
    trigger_frame = frame(1)

    recorder.handle_frame(frame(), make_trigger_event(), lambda: trigger_frame, lambda: [])

    assert len(fake_cv2) == 1
    saved_path, saved_frame = fake_cv2[0]
    assert saved_path.startswith(str(config.captures_dir))
    assert saved_path.endswith("trigger.jpeg")
    assert np.array_equal(saved_frame, trigger_frame)


def test_annotated_frame_fn_not_called_while_recording(make_config):
    recorder, _ = make_recorder(make_config)
    recorder.handle_frame(frame(), make_trigger_event(), lambda: frame(1), lambda: [])

    def fail():
        raise AssertionError("annotated_frame_fn should not be called while recording")

    # Feed a post-frame: should go down the "recording" branch and never touch annotated_frame_fn.
    recorder.handle_frame(frame(), None, fail, fail)


def test_further_triggers_while_recording_are_ignored(make_config, fake_cv2):
    recorder, _ = make_recorder(make_config)
    recorder.handle_frame(frame(), make_trigger_event(), lambda: frame(1), lambda: [])

    recorder.handle_frame(frame(), make_trigger_event(), lambda: frame(2), lambda: [])

    assert len(fake_cv2) == 1  # only the first trigger saved a frame


def test_finalizes_after_post_target_frames_and_resets_to_idle(make_config, fake_cv2):
    recorder, config = make_recorder(make_config, post_time=1)  # fps=2 -> post_target_frames=2
    pre_frames = [frame(9), frame(8)]

    recorder.handle_frame(frame(), make_trigger_event(), lambda: frame(1), lambda: pre_frames)
    recorder.handle_frame(frame(10), None, lambda: None, lambda: None)  # post-frame 1
    assert FakeWriter.instances == []  # not finalized yet

    recorder.handle_frame(frame(11), None, lambda: None, lambda: None)  # post-frame 2 -> finalize

    assert len(FakeWriter.instances) == 1
    writer = FakeWriter.instances[0]
    assert len(writer.frames) == len(pre_frames) + 2
    assert writer.released

    # Back to idle: a new trigger starts a second event.
    recorder.handle_frame(frame(), make_trigger_event(), lambda: frame(3), lambda: [])
    assert len(fake_cv2) == 2
