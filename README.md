# handy-mirror

Mirror of Hugging Face model weights that the [Handy](https://huggingface.co/Handy) transcription app depends on, distributed as **GitHub Releases** for environments that can't reliably reach `huggingface.co`.

## Why this exists

Handy runs on a range of devices, including managed/enterprise endpoints where direct access to `huggingface.co` is restricted, rate-limited, or occasionally unavailable. This repo provides a stable GitHub-hosted source for the same model weights so Handy can keep working in those environments.

If your environment *can* reach Hugging Face, prefer pulling from upstream directly — the HF cache is the authoritative source and you'll get the latest patches sooner.

## Releases

Each model is published as a separate GitHub release. Pick the release whose title matches the model your version of Handy needs.

| Model | Asset (`.gguf`) | Source | License | Release |
|---|---|---|---|---|
| `parakeet-unified-en-0.6b` | `parakeet-unified-en-0.6-Q8_0.gguf` | [`nvidia/parakeet-tdt-0.6b-v2`](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2) (via a community GGUF port) | see upstream model card | [releases](../../releases) |
| `canary-180m` | `canary-180m-Q8_0.gguf` (or as published) | [`nvidia/canary-180m-flash`](https://huggingface.co/nvidia/canary-180m-flash) (via a community GGUF port) | see upstream model card | [releases](../../releases) |

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

Upload a new mirror (you have the `.gguf` locally — typically a community GGUF port of the upstream model):

```bash
# Optional: sidecar checksum for managed-device fleets to verify
sha256sum <asset>.gguf > <asset>.gguf.sha256

# Publish as a GitHub release
gh release create v<tag> <asset>.gguf [<asset>.gguf.sha256] \
  --repo TaylorFinklea/handy-mirror \
  --title "<friendly model name>" \
  --notes "Mirror of <upstream source>."
```

For example:

```bash
gh release create v1 parakeet-unified-en-0.6-Q8_0.gguf \
  --repo TaylorFinklea/handy-mirror \
  --title "parakeet unified en 0.6b" \
  --notes "mirror"
```

Tips:

- Use a single tag per release (e.g. `v1`, `v2`, …) and let the release **title** carry the model name — Handy consumers select the release whose title matches the model they need.
- Pin the upstream quantization source / revision SHA in the release notes so consumers can verify provenance.
- Attach a `.sha256` sidecar for managed-device fleets; don't rely on GitHub's digest URL alone.
- Don't re-quantize or edit the `.gguf` between source and release — this is a pure mirror.

## License & attribution

This repo is a passive redistribution. The `.gguf` assets are sourced from community GGUF ports of the upstream models and remain under the licenses specified by their authors. See each upstream model card (linked in the table above) for the applicable license, attribution requirements, and usage restrictions.

Handy is by [Tatsuya Taguchi](https://huggingface.co/Handy). The underlying model weights (Parakeet, Canary, and others) are © NVIDIA and released under their respective open licenses; the GGUF conversions are © their respective community authors.

## Status

Active. Mirrors are refreshed when Handy bumps its model requirements or when upstream releases a new revision.
