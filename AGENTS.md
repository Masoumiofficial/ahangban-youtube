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


### Laptop details and Chatterbox review

User reports Intel Core i7-8550U (displayed 1.80/1.99GHz), 8GB RAM and 60GB
storage. Do not ask them to repeat the CPU/RAM details; whether 60GB is total or
free disk and whether a discrete GPU exists remain unconfirmed. Prefer a short,
single-process CPU-first experiment; do not promise realtime generation or an
8GB memory fit without measurement.
Chatterbox reviewed at 5de7a54aa4e5e2baadb0182dde554908b48b85c2 (default branch master).
Pinned code lists 23 multilingual language IDs and NO fa. Turbo/Nano are documented
as English. Do not recommend them as native Persian TTS or fake support by adding
fa/selecting ar. ChatterboxVC takes guide AUDIO and a target-voice path, not text;
it is a candidate comparison with OpenVoice, not a tested Persian cloning engine.
It uses only the first ten seconds of the target reference; prepare a speech-rich
excerpt rather than feeding the untrimmed recording blindly. Model files are on
Hugging Face, outside this sandbox's outbound allowlist. No weights/inference or
laptop benchmark have been run. See `content/004-chavoshi-own-voice/research/`.


### First episode completed — latest user priority

User asked to stop delaying on cloning and finish the first video. Completed
`downloads/ahangban-first-video-final.mp4`: 199.22s, 1920x1080, 25fps, 17,209,035 bytes.
Actual Sajad m4a was split into four padded takes (source windows in the new
`content/004-chavoshi-own-voice/build_video.py`); all four were PCM-reextracted in QA.
Seven new Ava clips were generated with the already selected voice-00 for the
rewritten script. No old male synthetic voice or old Ava dialogue was substituted.
Black-suit presenter shot 002, official neon glow, five 12s songs, 37 speech cues,
thumbnail/title/description/chapters and technical QA are delivered. Full decode,
source hashes and peak -1.5dBFS passed; representative frames were visually checked.
See `content/004-chavoshi-own-voice/FINAL-DELIVERY.fa.md` and `delivery/`.
No actual aural/ASR/phonetic confirmation or rights clearance is claimed. User final
listening review remains important. Hosts are STATIC; no lip sync. No personalized
clone, third-party upload of the recording or YouTube publication. Cloning remains
optional future research; do not block or mislabel the finished real-recording edit.


### Cinematic presenter development (latest request)

User now requests camera angles, zoom in/out, cinematic movement and lip sync.
`content/005-cinematic-presenters/` contains a rendered 28s CAMERA-ONLY proof:
`downloads/ahangban-camera-demo-no-lipsync.mp4` (1280x720/25fps), five digital
frontal reframes with smooth zoom and speaker cuts at actual speech boundaries.
It is NOT a new perspective, facial animation or lip sync. Source 002 and both
voices unchanged; AAC copied, decoded first-28s PCM matches the original episode.
Full decode and 4 framing/timing tests passed, encoded close-ups visually reviewed.
Original final episode retained. No publication, paid purchase, external upload,
model download or lip-sync inference. Jobs JSON is a PLAN, not an executed engine.
MuseTalk upstream README reviewed at 0a89dec45a0192b824e3cf4daf96c239440c5ed8;
weights are outside current network access, dependencies need license review,
Persian/identity quality untested. Do not promise lip sync is implemented or use
amplitude-driven mouth deformation as a substitute. Cloud processing would need
provider/privacy/cost approval before sending faces/audio or purchasing anything.


### User decision: lip sync without subscription ONLY

User explicitly selected ONLY the no-subscription route. See
`content/005-cinematic-presenters/local-route.json`. Do not ask again or switch to
paid APIs/subscriptions/paid GPUs/card-requiring trials. No third-party face/audio
upload approved for this step. Local MuseTalk remains an UNEXECUTED candidate.
Prepared private pilot inputs using `prepare_lipsync_pilot.py`: male 02 full 6.284s
and female 05 first sentence 4.49s extracted from the existing MP4 as 16kHz mono
PCM, no voice synthesis. Separate draft face contexts suppress gallery portraits
so a detector cannot pick a wall portrait. These are NOT approved paste-back masks;
Ava foreground microphone still needs protection. Inputs remain under ignored
rendered/, with a fail-closed output-path guard; do not commit standalone voice
exports or processed face inputs. Crops were visually checked and WAV duration/
format asserted; no actual detector/inference or aural boundary check performed.
No lip-sync video exists. Model weights inaccessible through currently allowed
network hosts and engine/compute not validated: current status is blocked before
inference, not success. Do not claim future background work or a laptop benchmark.


### User approved FREE Colab pilot (latest decision)

After recommendation of free Colab vs laptop, user said «بزن بریم سراغش پس».
Free user-started Google Colab processing is now authorized for the short two-host
lip-sync pilot, NOT paid GPU/subscriptions/other cloud providers. Update from the
previous local-only status: see local-route.json and colab/README.fa.md. The agent
has NOT accessed a Google account, run a Colab GPU, downloaded weights or produced
lip-sync video in Arena. User must open/run the prepared notebook themselves.
Custom runner colab/run_pilot.py uses pinned MuseTalk V1.5 UNet + VAE + Whisper;
manual boxes replace all pose/detector/face-parser dependencies. Bounded mouth matte
preserves everything outside it, including Ava mic protection line. Model quality
and CUDA installation UNTESTED; static geometry/compositing and syntax tested only.
Only existing voices; 16k conditioning, original 48k playback cuts. Sources are
fetched from the user's own public repository into Google (full 17MB episode and
shot002; NOT raw sajad.m4a). Weights fetched on USER Colab from official public HF
repos with recorded revisions/hashes, no tokens/mirrors/proxies. No Drive mount,
public server or upload to other inference services. Download ZIP should contain
only two composited pilot MP4s and provenance/results, NOT WAVs/faces/weights.
No automatic full episode render; wait for actual clips + human review. Never
present notebook preparation or fake model tests as successful lip sync.
