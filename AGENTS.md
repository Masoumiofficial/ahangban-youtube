# AhangBan YouTube workspace

Channel supplied by the user: https://www.youtube.com/@AhangBan
Default conversation language: Persian, unless the user requests otherwise.
Do not assume the channel's niche, audience, metrics, or spoken language from its name.

## Installed YouTube skills

For relevant requests, read `.claude/skills/<name>/SKILL.md` and follow its workflow:

- `yt-script`: scripts and hooks
- `yt-package`: title and thumbnail pairing
- `yt-edit`: transcript-based edit decisions
- `yt-comment`: comment triage and draft replies
- `yt-plan`: weekly content planning
- `yt-viral`: niche research and outlier ranking
- `yt-retention`: audience retention analysis
- `yt-shorts`: short clips from long videos
- `yt-seo`: descriptions, tags, and search queries
- `yt-chapters`: transcript-based chapters
- `yt-audit`: channel audit

Run bundled Python tools from their skill directory or by their full project-relative
path. They require Python 3 and only the standard library. Keep sibling skill folders
intact: chapters and retention import yt-edit; viral reads yt-script/hooks.json.

Upstream skills look for `~/.claude/youtube/voice.md`. If unavailable, use a completed
project-local `.claude/youtube/voice.md` if present. The blank template is at
`.claude/youtube/templates/voice.md`; it is NOT a completed voice profile. Request
three sample videos/transcripts before inferring the creator's voice; never invent it.

The scoring and text-matching tools use English-centric heuristics. Do not present
Persian hook scores, word-overlap checks, or filler detection as linguistically reliable.

Nothing here authorizes publishing, posting replies, or changing the channel.
Do not invent analytics or claim channel access. Request exports/transcripts when
needed. The optional web app in `src/` supports user-authorized read-only OAuth. It does not grant the Arena agent access to browser sessions. Never inspect session tokens or credentials; ask the user to export a dashboard report and share it for analysis. See `docs/youtube-connection.fa.md`.

## AhangBan permanent studio

Read `studio/ahangban-signature/MASTER-SPEC.fa.md` and `environment-lock.json`
before modifying studio imagery. The single empty master v1.2 is approved; do not overwrite or redesign it.
Do not generate other camera views before explicit approval. Preserve the supplied
logo and all twelve original portrait files, their identities, order and positions.
Never generate substitute celebrity faces or redraw the logo. User requested one
coherent master image and no alternative designs. A single 2D master is not a
calibrated 3D scene; do not promise guaranteed geometric identity across new views.
Main feminine voice stays voice-00; the user selected replacement masculine voice-02
in this session. The historical five-track MP4 retains voice-01; the new studio edition in
`downloads/ahangban-chavoshi-studio-review.mp4` uses the selected replacement
voice-02 for all four male turns. Voice identifiers are session-specific.

### Latest studio and presenter decision

Master v1.2: artists follow the user's numbered list RIGHT-TO-LEFT within each row;
never mirror the source photographs themselves. The master has an EMPTY logo panel.
Use the official original logo and optional glow as independent video overlays;
do not bake the wordmark back into the base without user instruction.
Ava and Sajad are the two permanent user-designated presenters. Read
`studio/ahangban-signature/Presenters/character-lock.json` before any presenter
production. Preserve their supplied identities and selected voices; do not adopt
fictional gold logos or room designs from their character boards. Sajad's manager
role is supplied by the user. No real-person identification is inferred.
The base remains empty. User-approved seating from the camera: Sajad LEFT, Ava RIGHT.
The first same-camera two-host composite is in `productions/HOSTS-VIEW-001.png`
with a separate RGBA presenter layer and shot manifest. The user accepted seating
and authorized a subtle realism refinement plus video production. Presenter v1.1
uses 95% seated scale, exposure harmonization and restrained contact shadows.
The new studio edition is documented under `content/003-chavoshi-studio/`: original
female speech, replacement male voice-02, five song samples, captions, waveform
and soft six-second logo-glow animation. The hosts are STATIC: no lip sync, facial
animation or new camera angle has been produced. No YouTube publication.


### Current next edition: user own voice / black suit

The user's latest request supersedes the previous synthetic male preference:
Sajad should use the USER'S OWN VOICE. No user voice audio has been received yet.
Do not call voice-02 the user's real voice or silently substitute a synthetic male
in the next edition. Recommend direct recording of four existing male turns;
`content/004-chavoshi-own-voice/` contains the exact scripts and pending plan.
Cloning is not provided by the current speech tool. Do not upload audio to a
third-party clone service, train a model or commit raw personal recordings without
separate user authorization. Store future raw recordings under ignored
`rendered/user-voice/sajad/`. The previous MP4 remains historical, synthetic voice-02.

The user explicitly requested BLACK SUIT as the current default, based on the
supplied cinematic reference (black shirt, no gold tie). Keep the original face
identity, glasses, hair and beard. `productions/HOSTS-VIEW-002.png` and its separate
layer/manifest hold the wardrobe-only correction. Shot 001 is retained for the
historical video. `compose_hosts.py` defaults to black/002; `--wardrobe brown`
reproduces the historical 001 only. Validate new work with `validate_hosts.py --shot 002`.
No new own-voice video, lip sync or YouTube publication has happened in this phase.

The current recording script is revision 2 in `content/004-chavoshi-own-voice/dialogue.fa.json`
and `script.fa.md`: all 11 turns have a shorter conversational rewrite. Only the
latest four entries in `recording-lines.fa.json` should be recorded by the user.
The earlier recording handoff is superseded. Ava retains voice-00 but all seven
turns require new synthesis; never pair rewritten captions with the old speech.
No new audio/video has been generated for this rewrite.


### Voice recording received; latest preference is no subscription

User uploaded `Presenters/Sajad/sajad.m4a` in ee2851d and explicitly authorized own
personal voice cloning, including third-party processing. They then selected
NO SUBSCRIPTION / LOCAL execution. Do not ask for API keys or account passwords.
The recording is 49.11s, approximately 29.64s non-silence at the documented threshold.
Only technical audio checks have occurred; no aural transcript, clone quality or
identity similarity has been verified. See `content/004-chavoshi-own-voice/VOICE-CLONING.fa.md`,
`audio-reference-analysis.json` and `voice-consent.json`.
A private mono reference with -3dB gain is under ignored `rendered/user-voice/sajad/`.
No provider upload, clone, billable call or new video render has happened.
Local OpenVoice V2 tone-color conversion with a suitable Persian base TTS is a
PROPOSED experiment, not a working Persian clone. Its native TTS language list
excludes Persian. Model assets are not available in this sandbox and their official
S3 host is outside the outbound allowlist. Hardware/installation and model access
must be resolved before claiming an actual trial. Do not substitute NC-licensed
Persian model weights as a commercially cleared AhangBan pipeline.
The user-uploaded m4a already resides in a public repo. Do not publicly commit more
raw audio or derived speaker embeddings by default; do not rewrite/delete history
without a separate user request. Prior 'recording not received' notes are historical.
