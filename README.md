# OpusVideo

A virtual comedy studio. You give it a one-line premise; a crew of Claude-powered
roles writes, judges, casts, directs, performs and prompts the sketch, then image
and video model APIs render it and ffmpeg cuts the final MP4 with subtitles.

See [docs/PLAN.md](docs/PLAN.md) for the full plan and workflow diagram.

## The crew

| Role | Module | Engine |
|------|--------|--------|
| Writer (the words) | `opusvideo/roles/writer.py` | Claude |
| Comedy Advisor | `opusvideo/roles/advisor.py` | Claude |
| Examiner (script rubric + keyframe vision QA) | `opusvideo/roles/examiner.py` | Claude |
| Chief Decider | `opusvideo/roles/chief.py` | Claude |
| Role Creator (casting + visual bibles) | `opusvideo/roles/casting.py` | Claude |
| Director (scenes & shots) | `opusvideo/roles/director.py` | Claude |
| Actor (one per character, parallel) | `opusvideo/roles/actor.py` | Claude |
| Prompt Engineer | `opusvideo/roles/prompt_engineer.py` | Claude |
| Photo Generator / Video Generator | `opusvideo/media/` | `mock` or Replicate-hosted models |
| Editor | `opusvideo/media/editor.py` | ffmpeg |

The orchestrator is `opusvideo/pipeline.py` (`Studio`).

## Quick start

```bash
pip install -e ".[dev]"          # needs ffmpeg on PATH
export ANTHROPIC_API_KEY=...      # or: ant auth login

# Write + plan only (cheap, no media spend). Review runs/<id>/*.json
opusvideo "A man tries to return a pigeon to a pet store that never sold it" --stop-after plan

# Full run with offline placeholder media
opusvideo "A man tries to return a pigeon ..." --media mock

# Full run with real image/video models on Replicate
export REPLICATE_API_TOKEN=...
opusvideo "A man tries to return a pigeon ..." --media replicate --aspect 9:16 --duration 30
```

Runs are resumable: re-run with the same premise (or `--run-id`) and finished
stages are loaded from `runs/<id>/` instead of being regenerated. Delete a stage's
JSON / image / clip to redo just that stage.

## Run artifacts

```
runs/<id>/
  00_brief.json  01_pitches.json  02_pitch_choice.json
  03_draft_N.json  03_draft_N_notes.json  03_draft_N_eval.json  03_draft_N_decision.json
  04_script_final.json  05_cast.json  06_shot_list.json  07_performances.json  08_prompt_book.json
  refs/<character>.png  keyframes/<shot>_vK.png  09_qa/<shot>_vK.json
  10_final_review.json  clips/<shot>.mp4  final.mp4  final.srt
```

## Configuration

Environment variables (see `.env.example`): model (`claude-opus-5-5` default), effort
for writing vs judging roles, media provider, and Replicate model slugs. Hosted video
models name their inputs differently, so set `REPLICATE_VIDEO_IMAGE_FIELD` (and
`REPLICATE_REF_IMAGE_FIELD` for image models that take a reference image) to match
the model's API page. To add another vendor, implement `generate_image` and
`generate_video` (see `opusvideo/media/base.py`) and register it in
`opusvideo/media/__init__.py`.

All Claude calls use structured outputs (typed Pydantic contracts in
`opusvideo/schemas.py`), adaptive thinking, and server-side refusal fallbacks
(`fallbacks: "default"`).

## Tests

```bash
pytest
```

The tests run the whole pipeline offline with a fake LLM and the mock media
provider, including a revise round, keyframe regeneration, resume, and a killed script.
