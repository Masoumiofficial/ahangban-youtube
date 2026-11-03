# AhangBan YouTube workspace

Channel supplied by the user: https://www.youtube.com/@AhangBan
Default conversation language: Persian, unless the user requests otherwise.
Do not assume the channel's niche, audience, metrics, or spoken language from its name.


## LATEST — user returned to Colab error diagnosis (static deliveries remain complete)

User supplied wrapper CalledProcessError exit1 under Python3.13 for the motion runner.
Actual child exception is still ABSENT; root cause UNKNOWN. Upstream pinned README
lists tested Python3.10/3.11 (verified via gh API); 3.13 is a risk, NOT a proven cause.
Do not claim fixed CUDA/install/model or successful inference. No blind model retry.
motion/{process_tools.py,diagnose_runtime.py,quick_diagnostic_cell.py,test_diagnostics.py}
adds persistent streamed child errors + read-only environment checks. Notebook updated
on same branch via ff-only fetch/merge; no reset/delete, existing outputs still guarded.
Quick cell can be pasted in the SAME failed runtime without code refresh, packages,
weights, inference or upload. Old wrapper alone cannot recover missing historic stderr.
13 CPU/stdlib diagnostic tests PASS; no Colab/hardware validation. User's latest request
permits this narrow debugging, not payment/new provider uploads or a new full workflow.
Natural motion remains unproduced; completed STATIC MP4s below unchanged.

## DELIVERED — real YouTube/Instagram files delivered WITH STATIC AVA, no natural motion

User: «بیخیالش خودت انجامش بده نسخه اینستاگرام و یوتیوب رو بده بهم».
Stop handing off Colab/sites/debugging to user. Actual locally rendered downloads:
- ahangban-ava-static-youtube.mp4:145.76s,1920x1080/25,19247123bytes,
  SHA256 f31db775515403aad9f249a42c98b5abc42ff2712bc6a60d4394fc2cb6e5d747
- ahangban-ava-static-reel.mp4:47.53s,1080x1920/30,8091335bytes,
  SHA256 0dff173cae4d383e521f7f577f02d2dd8fccf69b651adba510a323309918e6a6

IMPORTANT: Ava is STATIC. No mouth/head/blinks/listening performance generated.
Assistant disclosed this limitation before building; user did NOT explicitly approve
static as replacement, so don't claim full motion request fulfilled or user accepted
that tradeoff. Names, visible tag and descriptions say static. These are full playable
files, NOT naturally animated presenter output. No model inference/new TTS/clone.
Same approved actor +corrected mic preserved. Actual source music-panel2.5D motion
retained; never describe it as moving Ava. Source AAC packet bytes copied EXACTLY
from010final-female, not reencoded/retimed/truncated. All narration voice06; original
male singing unchanged. Full3x35sYT/3x12svertical, website spoken/visible retained.

static-delivery/{build_exports.py,validate_exports.py,package_delivery.py,test_exports.py,
delivery/} contains reproducible code/plans/provenance/QA/SRT/chapters/descriptions.
Both full decode PASS, exact3644/1426frames, SAR1/BT709/nativefps, exact AAC hashes,
source/fixed-face checks and moving music region checks.13new tests PASS. Source
full010exports still SHA34a5a405.../3dbba0de... unchanged; approved covers unchanged.
Music/speech encoded frames visually inspected. Original subtitles extending into
YT left crop were masked ONLY during speech, replaced by full subtitle near Ava.
Do not remove this crop guard or add redundant fps filter (end-frame loss); graph
uses native main timing, shortest=1, source AAC copy, full source frame counts.

No publication authorized/performed.009receipt remains untouched. No active render.
Deliver actual two GitHub video links, no more homework. If user still insists on
natural presenter motion, clearly it remains unavailable/unproduced here; don't
fake it with zoom, motion loops, amplitude mouth warps or rejected MuseTalk output.
Historical failed/external routes below are NOT current next required user actions.

## HISTORICAL — different route after Colab error (now bypassed by actual static exports)

User supplied only the call line, not traceback, then «نمیشه یه راه دیگخ بزن».
Root cause UNKNOWN; do not claim fixed/install/OOM diagnosis or request the same
traceback again as the only next step. No successful model video returned.
New simpler alternative prepared: official author-linked public WEB demo at
https://modelscope.cn/studios/BadToBest/EchoMimicV3 (verified link in upstream
README, NOT actual live service availability/free queue/auth/deployed version).
content/011-ava-split-screen/web-demo/ has offline packager, 7 passing stdlib tests,
manifest + guide. downloads/ahangban-ava-web-image.png = exact approved actor;
web-speech.wav = exact preserved talk-conditioning WAV (4.48s full voice06 +.36tail).
web-upload.zip = those two +prompt/guide/provenance; no installer or new voice/face.
Begin with talk-only5s trial, not full episode; listening comes after actual result.

Agent has NOT uploaded/invoked ModelScope or any new service. Previous Google
consent is NOT blanket automatic upload consent elsewhere. Disclose user-initiated
web upload processes synthetic Ava/audio at third-party demo. No account/token/card
requested or stored. No subscriptions/payment authorized; stop if demo requests paid
access. Can't guarantee available/free/quality; never claim web demo tested or video
rendered. If user returns actual MP4, QA identity/Persian lips/head then composite
with protected corrected mic; never replace motion by still zoom or cached states.
Approved face/mic outputs and previous Colab inputs/code preserved below as history.
Working copy was rehydrated sparsely from remote current branch; absent unselected
paths aren't deletions. Check git sparse-checkout/index before assuming files lost.

## PRECEDING — 011 Ava approved; mic revised; FREE COLAB attempt (now bypassed)

User approved face/layout: «آره خوبه فقط میکروفون رو یکم طبیعی تر بکنبعد بزن بریم
سراغ حرکت لب و دهان و سر و گوش دادن آوا». Keep exact approved actor PNG SHA256
68854d222a57969ff89567530f8b4c8202d4f8b8855acac96a23e7628e861adf. Do not regenerate
or audition her face/voice again. Preserve voice06, same three010tracks, official
studio master/12portraits/logo and previous delivered files. No male, subscription,
paid compute, cloning, publication or master redesign authorized.

build_mic_revision.py produces downloads/ahangban-ava-layout-v2-01..03.jpg, not
animated videos. Old boom no longer crosses neck; isolated realistic microphone
prop keyed/despilled lower-left, original texture repair only within bounded old
prop area below gallery. Face ROI lossless exactly equal to approved layout.
Original three layout JPGs and010full exports/covers preserved. User review of
mic appearance pending, not face approval. layout-v2-manifest +user-review current;
original layout-manifest face-pending is historical. 18 local011tests validate
composition/inputs/protected assets, not generated motion.

ask_user ava_motion_runtime resolved free_colab; do NOT ask again. User informed
Google processes synthetic Ava/voice and agent has NO account/runtime access.
Experimental motion/AhangBan-Ava-Motion-Pilot.ipynb +runner prepared for USER-run
free GPU, no metered fallback. New candidate official EchoMimicV3 Flash pinned
7e89489ca51c0d008fc1963ec6c03fc5bd0b9397, NOT rejected MuseTalk. Upstream claims
12GB VRAM/8steps/up-to768; not our benchmark or guarantee on free T4. Notebook
installation/inference NOT tested in Colab; no model weights/inference executed
by agent. Arena has no NVIDIA device/Torch; official weights also network-blocked.
No proxy/mirror bypass. No active inference/render process. No animated video yet.

Pilot inputs ZIP prepared +hashes: same actor, exact reviewed hookvoice06 complete
4.48s +.36tail (121frames25fps), listening4.04s (101frames) with SILENT conditioning.
Music ONLY on playback, never drives lips during listening. Exact copied original
MP3 source hash87548f0636deaf4b5776ad24625b504dbe13679c134e5ed704ff3d645901a995.
No TTS, pitch/speed edits or human recording. Models see actor only; mic/studio/
covers/logo composited separately. Two actual generated clips required; don't call
static zoom, pixel variation or source ZIP proof of natural lips/head/listening.
User must run FREE GPU notebook and return ava-motion-pilot-results.zip or exact
error; stop if no GPU/OOM/install/precision failure, never buy/upgrade. When results
return, check provenance/decode +human identity/Persian phoneme/closed-mouth review
before full film. Never reuse old rejected MuseTalk output or silently loop a short
reaction across36s music. More details content/011-ava-split-screen/motion/README.fa.md.

Reference exact blob9fdc2fe2877e361841574806e73b38e9342829ee,720x1280/30,55.77s;
upper artist~53%,lower presenter~47%, cuts~10/39s, ten sampled frames inspected.
No reference artist identification, listening/transcription or model inference.
011 supersedes earlier faceless-only for Ava THIS request only.010finals below
and009unknown public upload receipt remain untouched; NO publication authorization.

## COMPLETED — 010 FINAL COMPLETE: female-only route selected by user

User chose ask_user option `female_only` after rejecting male07 and both audition
pairs08/09. Do NOT ask for more male voices or use them. User had approved revision02
visual/video look and both covers; preserve those designs. Current final package:
`content/010-night-playlist/final-female/`, downloads/ahangban-night-final-{youtube,reel}.mp4
plus final thumbnail/cover and an optional isolated full name-introduction MP3.
YouTube 145.76s native 1920x1080/25, 3x35s songs; vertical47.53s native1080x1920/30,
3x12s. All NARRATION voice06 female; original male singing in songs unchanged.
Reviewed female-hook and female-transition MP3s reused byte-identically; no re-synthesis.
Intro newly generated as «سیاوَش قُمیشی» per user «سیاوش قُمیشی» correction; no claim
of agent aural verification. Four new female clips +two prior female candidate clips
and two reviewed clips total8 sources. No time/pitch edits or EQ/reverb on speech.
Exact approved revision02 cover bytes copied; 2.5D card/shadow/reflection/parallax/FFT
style retained. Both final exports independently decode/QA PASS, all audio sections
source correlation>.97, native frame motion checked. 14 final tests +10 revision02
+17 original episode +44 Node tests PASS. Final listening to new utterances is pending,
not a reason to claim absolute naturalness or automatic pronunciation certification.
Old first-delivery and review-preview hashes preserved. Abandoned six final-v2
candidate MP3s moved to ignored rendered/video-010-abandoned-final-v2/audio; status.json
records this, none of the rejected male performances enters the final.
Use final-female/build_final.py +validate_final.py +package_final.py for reproducible
current files, not historical preview/first builder. Source music remains pinned to
commit d4cf777d859a0826c7dd4ccde9b7fccea4a8a503 and user URLs in descriptions.
NO publication authorized/performed for010; uploader job remains009. Preserve009
uploaded video receipt and UNKNOWN public visibility; no duplicates or secrets.

## HISTORICAL — preceding male-casting pause (superseded by female-only decision)

## Latest decision — STOP random male auditions; 08 and 09 BOTH rejected

User explicitly rejected both candidates from battle08 and battle09 despite tool
selection results returning voice08/09. Latest: «هیچ کدوم اصلا جنس صدا خیلی شخمی شده».
Do NOT synthesize with voice07, voice08 or voice09 or run another unsolicited random
pair. Ask one focused question about desired voice character / optional female-only
route. Male casting and final render remain paused. Female06 and approved revision02
video style and thumbnail/cover remain unchanged. No publication authorized.

## HISTORICAL — finalization was PAUSED: male voice-07/delivery explicitly REJECTED

User approved revision-02 VIDEO LOOK and both COVERS and asked final production,
with name correction «سیاوش قُمیشی» (not ساوش قَمیشی). Then interrupted: «صدای و نحوه
گویندگی مرد خیلی بد شده». This latest feedback rejects male voice and performance,
not just the name. Do NOT finish with male07. Keep female voice06, reviewed female
performances and approved visuals/covers unchanged. Audition fresh masculine fa
conversational pair index4; no human cloning, celebrity imitation or subscription.
Before interruption, six candidate MP3s generated in final-v2/audio (4 male07,
2 female06); NO final renderer, video mux, final package or publication ran. Their
existence is not approval. final-v2/status.json records hashes and truthful pause.
Fresh voice selection is not approval of all new sentences: make a short dry
contextual sample first; do not synthesize/rerender a whole episode blindly again.
Name correction TTS attempt was «سیاوَش قُمیشی», not aurally verified. Engine has
no direct word-stress/emotion control. Preserve all source assets, approved
thumbnail/cover bytes and 009 upload receipt; no publishing authorized for 010.

## PREVIOUS — revision-02 visual previews approved; male speech later rejected

Latest user feedback: 010 speech unnatural again; work on words/tone, stronger
video effects, more professional realistic dimensional thumbnail and Reel cover.
Do NOT call 010 voice approved based on 008 voice selection or technical QA.
Preserve voice-06 female/07 male identities; do not silently swap, clone or use 007.
`content/010-night-playlist/revision-02/`: 3 fresh short conversational performances,
dry voice sample 16.44s (female/male/female; no music/FX/EQ/speed/pitch edits), new
independent YouTube thumbnail 1280x720 and Reel cover 1080x1920, and 39.56s native
1920x1080/25 review preview. Full episode NOT rebuilt; wait for user listening
feedback before generating remaining text and rebuilding full outputs. No direct
word-stress/emotion engine controls exist; actual changes are rewrite + resynthesis.
Projected original cover planes, thick edges, shadows, table reflections, independent
foreground/card/background motion and actual FFT line give 2.5D depth, NOT a volumetric
3D scene. Backgrounds AI-generated; original supplied artwork/faces and official
logo not regenerated. Covers built by compositing, not random AI-written logos.
Artifacts: downloads/ahangban-night-v2-{voice-preview.mp3,style-preview.mp4,
youtube-thumbnail.jpg,reel-cover.jpg}. First delivery originals and their hashes
remain intact. New metadata never claims naturalness, approval, rights or publication.
New independent preview QA PASS: full decode, every audio correlation >.97, peak
-1.9 dBFS, camera/FFT motion and cover hashes/sizes. 10 revision tests +17 original
episode tests +44 Node tests PASS; none certifies naturalness.
Source music remains pinned to 010 source manifest and 3x35s/3x12s full-version target
unchanged; short style demo uses only 8+7+7s music. No publication/account purchases.
Preserve 009 uploaded video receipt and UNKNOWN public status; never upload duplicate.

## HISTORICAL — first 010 delivery; speech later rejected, NOT published

User supplied Artist/2-video-2 on main plus three ahangban.ir URLs. Source commit
pinned at d4cf777d859a0826c7dd4ccde9b7fccea4a8a503; 3 MP3 + 3 cover blobs verified.
First song is «تو بارون که رفتی», NOT the draft generic «بارون». All new speech,
track metadata and titles corrected. Other songs: Dastaye To / Dariush, Age Ye Rooz /
Faramarz Aslani. No website pages fetched; exact user URLs included in descriptions.
`content/010-night-playlist/` contains source manifest, pinned-blob fetcher, builder,
validator, packaging, 8 fresh MP3s with historical approved voice-06 female/07 male
(the tools accepted both IDs), three generated night plates, scripts and deliveries.
Final files: downloads/ahangban-night-playlist-{youtube,reel}.mp4 plus thumbnail/cover.
YouTube 163.0s native 1920x1080/25, 3x35s music; vertical 52.21s native 1080x1920/30,
3x12s music and independently generated short speech. Logo original/unmodified;
no voice pitch/speed changes, human recordings, clones, presenters or lip sync.
Both full exported videos independently decode/QA PASS, every decoded section audio
correlates >.97 with source, peaks -2.0/-1.9 dBFS, encoded camera/FFT motion checked.
17 episode Python tests +44 Node tests PASS. Final visual frame review done; NOT
final user listening, copyright clearance or publication. Excerpts are signal/RMS
selected, NOT chorus recognition/lyrical edits or actual human listening. Captions
are proportional + silence-nudged, not word-level alignment. Original opening-concept
still is historical, not final output. Ignored rendered/ holds intermediate sources.
User authorized creation ONLY for 010; no subscription/publishing/account changes.
Existing local publisher job remains 009 — do not reuse to publish 010. Preserve the
009 upload receipt and UNKNOWN public status; don't create duplicate uploads.

## CURRENT PUBLICATION recovery — user uploaded video; public status UNKNOWN

User ran the local tool successfully through @AhangBan channel verification and
video upload. Then custom thumbnail was rejected and later work failed with the
old generic local_or_network_error. The log proves upload completion, NOT public
visibility or a specific network/Windows/thumbnail cause. No actual video ID is
provided in chat yet. Do NOT claim publication or ask for credentials.
Preserve the existing local receipt. Recovery command MUST use -ResumeOnly
(--resume-only) in the SAME project folder. It refuses a missing saved video ID
and never creates a new upload; it skips video download/resending. Updated tool
prints saved/uploaded Video+Studio links early, retries status reads, provides
allowlisted HTTP/Google/network/filesystem diagnostics, keeps status failures
pending rather than claiming failure of the upload, and retries Windows receipt
replacement without deleting the old receipt. Thumbnail failure remains separate.
The exact root cause of the user's generic error is not established. New regression
tests are mocked/local, not proof that the fix ran on user's Windows. 44 Node tests
pass (21 publisher, 23 dashboard/UI). Wait for updated status/real video link.
The dashboard remains read-only; local publisher explicitly uses fresh OAuth upload
consent only on USER computer. Never read .env/tokens/cookies or request them in chat.
YouTube publication is authorized for latest009 only; Instagram/account changes are
not. No remote control of Windows or Google network/connector access exists in Arena.
Old delivery manifests describe generation time; do not turn published flags true
without real evidence. API may force private uploads; cannot bypass audit/restrictions.
Content ID Checks are not certified. Tokens stay in process memory only; the
non-secret receipt belongs in ignored rendered/, never in Git.

## COMPLETED — 009 production with APPROVED voice06/07; testing pause lifted

User listened to 008 and said «آره الان عااالی شد بزن بریم تدوین ویدیو ... تایم موزیک بیشتر بشه».
Do not ask them to audition the same voices again. Female voice-06 and generic male
voice-07, conversational fa, are approved in the dry sample. Keep their identities,
natural short phrasing and original speed/pitch. New sentences/final montage still
require final listening, not presumed approval. `content/009-music-film/` uses the
EXACT approved 008 MP3 performances (hash-checked) plus six new turns with these
voices. Never use human/clone/007 narration. No EQ/reverb or speed/pitch tricks.
Question-led opening; first music ~12s. 5x30s songs YouTube, 5x12s Reel (>1min on
purpose). Surreal 2D environments, energy-onset-guided camera cuts, actual FFT,
light-wipe transitions, kinetic Persian captions, original covers and unchanged logo.
No speech over music. Say/show رسانهٔ آهنگ‌بان and ahangban.ir; staged CTA between songs.
008 sample manifest is historical generation-time status; user-review.json records
subsequent explicit approval. Do not mistake its old pending flag for current state.
No publication, subscription purchase, face/lip-sync work, personal clone, real
speaker imitation, verified current-song-trend or rights/virality guarantee.

## Historical 007 production decision — audio quality subsequently rejected

The user explicitly abandoned Sajad's real recording and ALL personal cloning.
Use ONLY fresh selected Persian synthetic female **voice-05** and generic male
**voice-04**. Female03/00 and older male voices are superseded. Never route new
speech through the 004/006 episode audio; no human recording or clone fallback.
Current source, scripts, fresh synthesized MP3s, imagery and QA live in
`content/007-cosmic-ai/`. Read its README and `.claude/youtube/voice.md` first.
The user rejected presenters/lip sync. Current design is faceless, cinematic and
surreal, with original music/cover art, attractive Persian OpenType captions and
an immediate Reel hook. 5x20s music in YouTube, 5x8s in native vertical Reel.
Say/show رسانهٔ آهنگ‌بان and ahangban.ir. Stage like/comment/subscribe invitations
without speech over music. Preserve official logo and all historical masters.
The new surreal environments do NOT authorize redesigning approved studio assets.
No subscription, new voice recording, face/Colab trial, publication, celebrity
imitation, current-song-trend claim, copyright clearance or virality guarantee.
All older own-voice/clone/voice00 directions below are HISTORICAL ONLY, not pending
instructions. Do not restart them without a fresh explicit user request.

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
Historically, main feminine voice was voice-00; the user selected replacement masculine voice-02
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


### Historical 004 phase: user own voice / black suit — superseded by 007

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


### Actual Colab pilot RETURNED by user (latest)

User supplied main/ahangban-lipsync-pilot.zip. Retrieved exact Git blob
06757ce5358114e1d0cf6db78cf6607bc19e28b4, ZIP SHA256
f69ebac11586fa29b20eeaae2dc28916ceea1ca73aa0f1332978248e4e3f3f54.
Two genuine output MP4s + reports returned: male 6.284s / female 4.49s, 1280x720/25.
Reported execution: Tesla T4, Torch2.0.1+cu118, same pinned MuseTalk V1.5. Independent
source hashes/clip hashes/full decode passed. Zero-lag audio correlations with
original episode windows 0.9999477 male / 0.9955387 female. NOT phonetic lip approval.
Source/model reports and independent review are in 005/received-pilot/. No need to
say model execution never happened: USER ran it; AGENT still has no local weights.
Visual sampled frames showed original broad male mouth mask alters beard/chin.
Agent locally recomposited only a narrower lip ellipse [148,174,221,207] over the
exact static reference, preserving outer beard/chin. No new inference or speech.
`downloads/ahangban-lipsync-pilot-reviewed.mp4` combines refined Sajad then original
returned Ava (~10.79s). Full decode passed and encoded frames visually inspected.
`review_received_pilot.py` reproduces verification/refinement from the ZIP, no GPU.
Wait for user quality review before full-episode generation. Do NOT call technical
checks proof of natural Persian lip synchronization. No full-episode lip sync,
head/body motion, new perspective, reusable voice clone or YouTube publication.
Original full first episode, original Colab notebook and upstream source pin kept.


### Historical 006 delivery: rejected lip sync; faceless videos with old audio

User: «نه اصلا خوب نیس ... کلا بدون چهره ...» then approved faceless editorial
and requested a strong YouTube video plus Instagram Reel. Do NOT ask for approval
of the old face pilot or resume cloud/face research. 006 production-plan supersedes
005 direction; historical reports/masters remain untouched for provenance.
Completed `downloads/ahangban-faceless-youtube.mp4` 199.22s, 1920x1080/25fps,
19,501,078B / SHA ffe397583de5d92325a0ea8743f2f7bbb42f3178f1946885f99016cdc4eff95a.
Completed `downloads/ahangban-faceless-reel.mp4` 32.30s, 1080x1920/30fps,
3,514,964B / SHA 354add8ae6c10d616aabc862a0e11682424a24b790e7e59522022545ae382fa3.
YT thumbnail 1280x720 and Reel cover 1080x1920, captions/metadata and QA in 006/delivery.
Editorial dark texture, ivory/amber type, original cover stacks/gentle motion,
48-band audio-derived FFT visualizer, per-track progress/chapters and hardburned
Persian speech cues. No presenter or studio IMAGE mapped; old episode input audio
ONLY. Cover art can contain original artist/actor faces: do not claim zero faces
anywhere. Official original logo colors/composition intact on ivory badge.
YT entire AAC payload exactly matches completed own-recording episode (11 speech,
5x12s songs, 37 captions), no new synthesis. Reel is a native portrait edit, NOT
horizontal crop: ~4s real Sajad question, 5x5s existing songs, ~2s existing Ava CTA
+1.2s end-card hold. Each decoded segment compared to source and non-silent; seven
audio correlations >.95, full decode/source blobs/motion/format PASS. Reels audio
prep originally revealed all-silent output because afade happened before output
seeking; fixed using atrim + asetpts BEFORE fades. QA now asserts non-silence and
source correspondence for every actual rendered segment; never reuse that failed
intermediate. Caption x/margins tightened to 88..920 safe region and Reel rerendered.
Encoded sampled frames of both formats visually inspected; final aural cut review
still user task, no forced-alignment or rights clearance claimed. Peak decoded
stereo: YT -1.5 dBFS, Reel -2.5 dBFS. No publishing, subscription, external processing,
new recording, new voice/clone or GPU required for this edition. Intermediate WAVs
stay ignored rendered/, not public Git. Delivery README has exact rebuild commands.
