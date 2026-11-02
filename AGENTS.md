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
before modifying studio imagery. The single master is pending user approval.
Do not generate other camera views before explicit approval. Preserve the supplied
logo and all twelve original portrait files, their identities, order and positions.
Never generate substitute celebrity faces or redraw the logo. User requested one
coherent master image and no alternative designs. A single 2D master is not a
calibrated 3D scene; do not promise guaranteed geometric identity across new views.
Main feminine voice stays voice-00; the user selected replacement masculine voice-02
in this session. The previously exported MP4 still uses the earlier voice until
explicitly re-rendered. Voice identifiers are session-specific.

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
The base remains empty; left/right seat assignment is not yet chosen.
