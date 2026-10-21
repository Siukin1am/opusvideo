# OpusVideo — Comedy Video Production Plan

A "virtual studio" that turns a one-line premise into a finished short comedy
video. Every creative and judging role is a Claude (Opus) call with its own
system prompt and a typed, schema-validated output. Only the steps Claude
cannot do itself — generating pixels — call external image/video model APIs.

## 1. The crew

| # | Role | What it does | Engine |
|---|------|--------------|--------|
| 1 | **Chief Decider** (executive producer) | Picks the winning pitch, approves/rejects each script draft, gives final sign-off on the cut. Has the last word when Advisor and Examiner disagree. | Claude |
| 2 | **Writer** (the words) | Pitches several concepts, writes the script, revises it from notes. | Claude |
| 3 | **Advisor** (comedy consultant) | Punch-up notes: what lands, what's flat, where the timing is off, callbacks to plant. | Claude |
| 4 | **Examiner** (QA / standards) | Scores scripts against a rubric (funny, clear, on-brief, producible, safe) and visually inspects every generated keyframe for character consistency and prompt match. | Claude (text + vision) |
| 5 | **Role Creator** (casting) | Designs the characters: personality, comedic trait, voice, and a *locked* visual bible reused in every image prompt so the characters look the same in every shot. | Claude |
| 6 | **Director** | Breaks the script into scenes ("sessions") and shots: shot type, camera move, action, duration, comedic timing. | Claude |
| 7 | **Actor** (one per character) | Performs each character's lines: delivery, facial expression, body language; may tweak wording to fit the voice. Runs in parallel, one call per character. | Claude |
| 8 | **Prompt Engineer** | Converts each directed shot + performance + character bible into an image prompt (keyframe) and a video prompt (motion). | Claude |
| 9 | **Photo Generator** | Renders character reference portraits and one keyframe per shot. | Image model API |
| 10 | **Video Generator** | Animates each keyframe into a clip (image-to-video). | Video model API |
| 11 | **Editor** | Concatenates clips, writes SRT subtitles from the dialogue, muxes them into the final MP4. | ffmpeg (local) |

## 2. Workflow

```
premise ─► Writer: 3 pitches ─► Chief: pick one
                                   │
                                   ▼
        ┌──────────── Writers' room loop (max N rounds) ───────────┐
        │ Writer draft ─► Advisor notes ─► Examiner scores ─►      │
        │ Chief verdict: approve │ revise (directives) │ kill      │
        └──────────────────────────────────────────────────────────┘
                                   │ approved script
                                   ▼
   Role Creator (cast + visual bibles) ─► Director (scenes & shots)
                                   │
                                   ▼
              Actors (parallel, one per character) ─► Prompt Engineer
                                   │
                                   ▼
   Photo Generator: character refs ─► keyframe per shot
        └► Examiner vision check ─► regenerate failing keyframes (max K)
                                   │
                                   ▼
             Video Generator: clip per shot (parallel)
                                   │
                                   ▼
          Editor: concat + subtitles ─► Chief final sign-off ─► final.mp4
```

## 3. Design decisions

- **Typed contracts between roles.** Each role returns a Pydantic model via
  Claude structured outputs (`client.messages.parse`), so one role's output is
  safe to feed into the next without brittle text parsing.
- **Resumable runs.** Every stage writes its artifact to
  `runs/<run-id>/<stage>.json`. Re-running the same run id skips finished
  stages, so a failed video call doesn't cost you the script again.
- **Pluggable media providers.** `mock` (offline: Pillow cards + ffmpeg stills,
  free, for development and tests) and `replicate` (one HTTP adapter that can
  drive many hosted image/video models — Flux, Kling, etc. — by changing the
  model slug and input field names in config). Adding a new vendor means one
  class with `generate_image` / `generate_video`.
- **Consistency strategy.** Character bibles are injected verbatim into every
  image prompt; character reference portraits are passed to the image model
  when it supports reference images; the Examiner checks each keyframe against
  the references with Claude vision and triggers regeneration.
- **Safety.** Refusals (`stop_reason == "refusal"`) surface as a clear error;
  server-side fallbacks (`fallbacks: "default"`) are enabled on every call. The
  Examiner's rubric includes a "punches up, not down" standards check.
- **Cost control.** Effort per role is configurable (judges at `medium`,
  writing at `high`); `--max-rounds` and `--max-shots` cap the loop sizes; the
  `mock` provider lets you iterate on the script without paying for pixels.

## 4. Milestones

1. ✅ Core: config, LLM wrapper, schemas, run store.
2. ✅ Text roles: Writer, Advisor, Examiner, Chief, Role Creator, Director, Actor, Prompt Engineer.
3. ✅ Writers' room loop + orchestrator with resume.
4. ✅ Media: mock + Replicate providers, Examiner vision QA, Editor (ffmpeg).
5. ✅ CLI + offline end-to-end test.
6. ⏭ Next: voice/TTS for the Actor (e.g. a TTS API per character voice) and lip-sync,
   music/SFX bed, a web UI to review and override each stage, cost ledger per run.
