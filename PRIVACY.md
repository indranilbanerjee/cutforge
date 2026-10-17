# Privacy

**No telemetry.** CutForge sends nothing to its author or to any analytics service. There is no account, no sign-up
and no tracking code.

**Your AI host does the model calls.** CutForge is a set of instructions and local tools that run inside the agent you
already use (Claude Code, Cowork, Codex, Cursor, Copilot CLI, Antigravity, Hermes Agent, OpenClaw or Grok). Prompts and
outputs go to that host's model provider under its own terms and privacy policy.

**Where your data lives.** Everything a project produces (copies of the media it uses, narration, the cue sheet, renders,
QC reports, facts and decisions) is written inside the project folder you choose. The client's original folders are
only read, never changed.

**Faces and people.** Face clustering (`tools/archive/faces.py`) runs locally with downloaded open models; nothing is
uploaded. It groups faces so that the client can name them; it never identifies anyone. The AI generation tool refuses
to send an image with a detectable face to an edit or image-to-video model unless you explicitly allow a
likeness-preserving style transfer.

## Network endpoints and credentials

Nothing connects on install: there are no hooks and no MCP servers. A CutForge tool opens a network connection only
when you, or a skill you invoked, run it, and only to the endpoints below. Paid calls also need a `GO_AHEAD.txt` in the
project and stay under its budget cap.

| What | When | Endpoint | Credential |
|---|---|---|---|
| `tools/voice/tts.py`, `gen_vo.py`, `audition.py` | when you generate narration or an audition with a paid provider | `api.sarvam.ai` (text-to-speech, voice clone), `api.elevenlabs.io`, `api.openai.com` (speech) | `SARVAM_API_KEY`, `ELEVENLABS_API_KEY`, `OPENAI_API_KEY` |
| `tools/voice/stt.py` (used by `gen_vo.py`, `import_vo.py --verify`) | when narration is verified by speech-to-text | `api.sarvam.ai` (speech-to-text), `api.openai.com` (transcriptions) | the same keys |
| `tools/vfx/ai_gen.py` | when you approve an AI image or video for a shot with no camera footage | `api.wavespeed.ai` | `WAVESPEED_API_KEY` |
| `tools/fetch_models.py` | once per machine, when you fetch the face and depth models | `media.githubusercontent.com` (OpenCV Zoo YuNet and SFace), `huggingface.co` (Depth Anything V2 Small); files are verified by md5 | none |
| `tools/vfx/cutout.py` | first use, when the optional `rembg` package is installed | rembg downloads its model weights | none |
| `tools/archive/search.py` | first use, when the optional `open_clip_torch` package is installed | Hugging Face (OpenCLIP weights) | none |
| `npm install`, `render.mjs` | project setup; first render when no browser is configured | the npm registry; Remotion downloads Chrome Headless Shell unless `browser_executable` is set | none |

Keys are read from environment variables or a key file, never printed, logged or sent anywhere except the provider
they belong to.

**Deleting your data.** Delete the project folder. Uninstalling the plugin through your host removes the plugin's own
files. Downloaded models live in each project's `models/` folder.

**Questions.** Open an issue at https://github.com/indranilbanerjee/cutforge/issues, or use a private security advisory
for anything sensitive.

The code is MIT-licensed; see [LICENSE](LICENSE) for the terms of use.
