from pathlib import Path

import pytest

from opusvideo.config import Settings
from opusvideo.media.editor import probe_duration
from opusvideo.media.mock import MockProvider
from opusvideo.pipeline import ScriptKilled, Studio
from opusvideo.schemas import Brief
from opusvideo.store import RunStore

from .fakes import FakeLLM


def make(tmp_path: Path, llm: FakeLLM) -> Studio:
    s = Settings()
    s.media_provider = "mock"
    return Studio(s, llm, MockProvider(), RunStore(tmp_path / "run"))


def test_full_run_produces_video_with_subtitles(tmp_path):
    llm = FakeLLM()
    out = make(tmp_path, llm).run(Brief(premise="a man returns a pigeon", duration_sec=10))

    assert out and out.exists()
    assert probe_duration(out) == pytest.approx(7, abs=0.5)
    srt = out.with_suffix(".srt").read_text()
    assert "Gary: I'd like to return this pigeon." in srt
    assert "Pigeon: He's not my type either." in srt
    # one revise round then approve; each shot regenerated once after examiner QA
    assert llm.calls.count("Writer") == 3  # pitch, draft, revise
    assert llm.calls.count("Actor") == 2
    assert llm.calls.count("Examiner") == 2 + 4  # 2 script evals + 4 keyframe reviews
    assert (tmp_path / "run" / "keyframes" / "S1-01_v1.png").exists()


def test_resume_skips_finished_stages(tmp_path):
    make(tmp_path, FakeLLM()).run(Brief(premise="p"), stop_after="plan")
    llm = FakeLLM()
    make(tmp_path, llm).run(Brief(premise="p"), stop_after="plan")
    assert llm.calls == []


def test_chief_can_kill_script(tmp_path):
    with pytest.raises(ScriptKilled):
        make(tmp_path, FakeLLM(verdicts=("kill",))).run(Brief(premise="p"))
