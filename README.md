# handy-mirror

Mirror of Hugging Face model weights that the [Handy](https://huggingface.co/Handy) transcription app depends on, distributed as **GitHub Releases** for environments that can't reliably reach `huggingface.co`.

## Why this exists

Handy runs on a range of devices, including managed/enterprise endpoints where direct access to `huggingface.co` is restricted, rate-limited, or occasionally unavailable. This repo provides a stable GitHub-hosted source for the same model weights so Handy can keep working in those environments.

If your environment *can* reach Hugging Face, prefer pulling from upstream directly — the HF cache is the authoritative source and you'll get the latest patches sooner.

## Releases

Each model is published as a separate GitHub release. Pick the release whose title matches the model your version of Handy needs.

| Model | Asset (`.gguf`) | Source | License | Release |
|---|---|---|---|---|
| `parakeet-unified-en-0.6b` | `parakeet-unified-en-0.6b-Q8_0.gguf` | [`handy-computer/parakeet-unified-en-0.6b-gguf`](https://huggingface.co/handy-computer/parakeet-unified-en-0.6b-gguf) (NVIDIA Parakeet Unified, EN) | see upstream model card | [releases](../../releases) |
| `nemotron-3.5-asr-streaming-0.6b` | `nemotron-3.5-asr-streaming-0.6b-Q8_0.gguf` | [`handy-computer/nemotron-3.5-asr-streaming-0.6b-gguf`](https://huggingface.co/handy-computer/nemotron-3.5-asr-streaming-0.6b-gguf) (NVIDIA Nemotron 3.5 ASR Streaming, multilingual) | see upstream model card | [releases](../../releases) |
| `canary-180m-flash` | `canary-180m-flash-Q8_0.gguf` | [`handy-computer/canary-180m-flash-gguf`](https://huggingface.co/handy-computer/canary-180m-flash-gguf) (NVIDIA Canary-180M-Flash, en/de/es/fr) | see upstream model card | [releases](../../releases) |

Add or retire rows as the lineup changes.

## Usage

1. Open the [Releases](../../releases) page.
2. Download the `.gguf` asset attached to the release matching your Handy version.
3. (Optional but recommended) Verify against the `.sha256` sidecar if one is attached:
   ```bash
   sha256sum -c <asset>.gguf.sha256
   ```
4. Place the `.gguf` in Handy's model directory. See the Handy app docs for the exact path on your platform.

## For maintainers

The script `mirror.py` pulls GGUFs from the `handy-computer` HF org and publishes them as releases on this repo. The allowlist in `models.json` is the source of truth for *what* to mirror; the HF org is the source of truth for *where the files live*.

### One-time setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
gh auth status   # confirm `gh` is logged in
```

The three models currently in the allowlist are also publicly available without auth, so `HF_TOKEN` is only needed if you add a gated repo later.

### Refreshing / adding a mirror

1. Edit `models.json` — each entry is one release:

   ```json
   {
     "tag": "v4",
     "repo": "handy-computer/<model-slug>-gguf",
     "title": "<friendly model name>",
     "notes": "Mirror of handy-computer/<model-slug>-gguf (Q8_0).",
     "quants": ["Q8_0"],
     "sha256": true
   }
   ```

   - `tag` — the GitHub release tag (`v1`, `v2`, …). Used as the version pin.
   - `repo` — the HF repo id, e.g. `handy-computer/parakeet-tdt-0.6b-v3-gguf`.
   - `quants` — list of quant suffixes to include; default `["Q8_0"]`. The script picks any `.gguf` whose name contains `-<QUANT>.gguf`.
   - `sha256` — whether to attach a `.sha256` sidecar to the release (default `true`).

2. Preview the work:

   ```bash
   python3 mirror.py mirror --dry-run
   ```

3. Run it for real:

   ```bash
   python3 mirror.py mirror
   ```

   Each entry is downloaded into a temp dir, attached to a fresh `gh release create` along with its `.sha256` sidecar, and the temp dir is removed on exit. The script is **idempotent**: if a release with the same `tag` already exists, it's skipped. Delete the release first (`gh release delete <tag> --repo TaylorFinklea/handy-mirror`) to re-upload.

### Discovery

To see every public model in the `handy-computer` HF org (useful when adding a new entry):

```bash
python3 mirror.py list
```

Gated repos are skipped from the mirror with a warning — set `HF_TOKEN` in the environment if you need to access one.

## License & attribution

This repo is a passive redistribution. The `.gguf` assets are sourced from community GGUF ports of the upstream models and remain under the licenses specified by their authors. See each upstream model card (linked in the table above) for the applicable license, attribution requirements, and usage restrictions.

Handy is by [Tatsuya Taguchi](https://huggingface.co/Handy). The underlying model weights (Parakeet, Canary, and others) are © NVIDIA and released under their respective open licenses; the GGUF conversions are © their respective community authors.

## Status

Active. Mirrors are refreshed when Handy bumps its model requirements or when upstream releases a new revision.
