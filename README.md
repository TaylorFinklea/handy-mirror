# handy-mirror

Mirror of Hugging Face model weights that the [Handy](https://huggingface.co/Handy) transcription app depends on, distributed as **GitHub Releases** for environments that can't reliably reach `huggingface.co`.

## Why this exists

Handy runs on a range of devices, including managed/enterprise endpoints where direct access to `huggingface.co` is restricted, rate-limited, or occasionally unavailable. This repo provides a stable GitHub-hosted source for the same model weights so Handy can keep working in those environments.

If your environment *can* reach Hugging Face, prefer pulling from upstream directly — the HF cache is the authoritative source and you'll get the latest patches sooner.

## Releases

Each model is published as a separate GitHub release. Pick the release that matches the Handy version you run.

| Model | HF upstream | License | Release |
|---|---|---|---|
| `parakeet-unified` | [`nvidia/parakeet-tdt-0.6b-v2`](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2) | see upstream model card | [releases](../../releases) |
| `canary-180m` | [`nvidia/canary-180m-flash`](https://huggingface.co/nvidia/canary-180m-flash) | see upstream model card | [releases](../../releases) |

(Edit this table as you add or retire mirrors.)

## Usage

1. Open the [Releases](../../releases) page.
2. Download the asset attached to the release matching your Handy version (typically a `.tar.gz` containing the full model directory).
3. Verify the checksum:
   ```bash
   sha256sum -c <model>-v<version>.tar.gz.sha256
   ```
4. Extract into Handy's model directory. See the Handy app docs for the exact path on your platform.

## For maintainers

Refresh or add a mirror:

```bash
# 1. Download from Hugging Face
huggingface-cli download <org>/<model> --local-dir ./<model>

# 2. Repackage and checksum
tar -C <model> -czf <model>-v<version>.tar.gz .
sha256sum <model>-v<version>.tar.gz > <model>-v<version>.tar.gz.sha256

# 3. Create a GitHub release and attach both files
gh release create <model>-v<version> \
  <model>-v<version>.tar.gz \
  <model>-v<version>.tar.gz.sha256 \
  --title "<model> v<version>" \
  --notes "Mirror of <org>/<model> at upstream revision <sha>."
```

Tips:

- Pin the release tag to the upstream revision SHA so consumers can verify they're getting the same bytes the mirror was built from.
- Keep the `.sha256` next to the tarball — managed-device fleets should verify before installing.
- Don't modify weights between upstream and the archive; this is a pure mirror.

## License & attribution

This repo is a passive redistribution. All model weights are mirrored from their original upstream repositories and remain under the licenses specified by their authors. See each upstream model card (linked in the table above) for the applicable license, attribution requirements, and usage restrictions.

Handy is by [Tatsuya Taguchi](https://huggingface.co/Handy). The underlying model weights (Parakeet, Canary, and others) are © NVIDIA and released under their respective open licenses.

## Status

Active. Mirrors are refreshed when Handy bumps its model requirements or when upstream releases a new revision.
