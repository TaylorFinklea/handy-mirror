#!/usr/bin/env python3
"""Mirror GGUFs from the handy-computer HF org to GitHub Releases.

Two subcommands:

  list     — print every public model in the handy-computer HF org and how
             many .gguf files each one has. Useful for building the allowlist.
  mirror   — for each entry in the allowlist, download the requested quants
             from Hugging Face and publish them as a GitHub release on this
             repo. Skips gated/private HF repos with a warning. Skips a
             release whose tag already exists (idempotent — delete the
             release to force a re-upload).

Reads the allowlist from `models.json` next to this script by default.
Override with --allowlist. Set HF_TOKEN in the environment for gated repos
(though gated repos are skipped, not fetched).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.errors import GatedRepoError, RepositoryNotFoundError


DEFAULT_QUANT = "Q8_0"
DEFAULT_REPO = "TaylorFinklea/handy-mirror"
HF_ORG = "handy-computer"
HF_TOKEN_ENV = "HF_TOKEN"


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def is_gated_or_missing(api: HfApi, repo_id: str) -> tuple[bool, str | None]:
    """Return (skip, reason). skip=True means we will not try to download."""
    try:
        info = api.repo_info(repo_id, token=os.environ.get(HF_TOKEN_ENV))
        if getattr(info, "gated", False):
            return True, "gated"
        return False, None
    except GatedRepoError:
        return True, "gated"
    except RepositoryNotFoundError:
        return True, "not found"
    except Exception as e:
        msg = str(e)
        if "401" in msg or "403" in msg or "gated" in msg.lower():
            return True, "gated"
        return True, f"access error: {e}"


def list_gguf_files(api: HfApi, repo_id: str) -> list[str]:
    return [
        f for f in api.list_repo_files(
            repo_id, repo_type="model", token=os.environ.get(HF_TOKEN_ENV)
        )
        if f.endswith(".gguf")
    ]


def select_for_quants(ggufs: list[str], quants: list[str]) -> list[str]:
    out: list[str] = []
    for g in ggufs:
        for q in quants:
            if f"-{q}.gguf" in g:
                out.append(g)
                break
    return sorted(set(out))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def release_exists(repo: str, tag: str) -> bool:
    r = subprocess.run(
        ["gh", "release", "view", tag, "--repo", repo],
        capture_output=True, text=True,
    )
    return r.returncode == 0


def load_allowlist(path: Path) -> list[dict]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise SystemExit(f"allowlist must be a JSON array, got {type(raw).__name__}")
    return raw


def cmd_list(api: HfApi) -> int:
    log(f"# Models in HF org '{HF_ORG}'")
    try:
        models = list(api.list_models(author=HF_ORG))
    except Exception as e:
        log(f"failed to list org: {e}")
        return 1
    if not models:
        log("(none)")
        return 0
    for m in sorted(models, key=lambda x: x.id):
        try:
            files = list_gguf_files(api, m.id)
        except Exception:
            files = []
        suffix = ""
        try:
            skip, reason = is_gated_or_missing(api, m.id)
            if skip and reason == "gated":
                suffix = "  [gated]"
        except Exception:
            pass
        print(f"{m.id}\t{len(files)} gguf{suffix}")
    return 0


def cmd_mirror(
    api: HfApi,
    allowlist: list[dict],
    repo: str,
    dry_run: bool,
) -> int:
    failures = 0
    for entry in allowlist:
        tag = entry["tag"]
        hf_repo = entry["repo"]
        title = entry.get("title", tag)
        notes = entry.get("notes", f"Mirror of `{hf_repo}`.")
        quants = entry.get("quants", [DEFAULT_QUANT])
        attach_sha = bool(entry.get("sha256", True))

        log(f"\n== {tag}  {hf_repo}  quants={quants} ==")

        skip, reason = is_gated_or_missing(api, hf_repo)
        if skip:
            log(f"  [skip] {reason}: {hf_repo}")
            continue

        try:
            ggufs = list_gguf_files(api, hf_repo)
        except Exception as e:
            log(f"  [fail] cannot list files in {hf_repo}: {e}")
            failures += 1
            continue

        wanted = select_for_quants(ggufs, quants)
        if not wanted:
            log(f"  [skip] no GGUFs match quants={quants} (have: {ggufs})")
            continue
        log(f"  assets: {wanted}")

        if release_exists(repo, tag):
            log(f"  [skip] release {tag} already exists in {repo} (delete to re-upload)")
            continue

        if dry_run:
            log("  [dry-run] would download + upload")
            continue

        with tempfile.TemporaryDirectory(prefix="hf-mirror-") as tmp:
            tmpdir = Path(tmp)
            local_files: list[Path] = []
            for fname in wanted:
                log(f"  download {fname}")
                hf_hub_download(
                    repo_id=hf_repo,
                    filename=fname,
                    local_dir=str(tmpdir),
                    token=os.environ.get(HF_TOKEN_ENV),
                )
                local_files.append(tmpdir / fname)

            sidecars: list[Path] = []
            if attach_sha:
                for lp in local_files:
                    sp = lp.with_name(lp.name + ".sha256")
                    sp.write_text(f"{sha256_file(lp)}  {lp.name}\n")
                    sidecars.append(sp)

            cmd = [
                "gh", "release", "create", tag,
                *[str(p) for p in local_files],
                *[str(p) for p in sidecars],
                "--repo", repo,
                "--title", title,
                "--notes", notes,
            ]
            log(f"  upload: {len(local_files)} gguf + {len(sidecars)} sha256")
            r = subprocess.run(cmd)
            if r.returncode != 0:
                log(f"  [fail] gh release create returned {r.returncode}")
                failures += 1
                continue
            log(f"  [ok] release {tag} published")
    log(f"\nDone. {len(allowlist)} entries, {failures} failed.")
    return 0 if failures == 0 else 1


def main() -> int:
    if shutil.which("gh") is None:
        log("error: `gh` CLI not found on PATH; install from https://cli.github.com")
        return 2

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default=os.environ.get("MIRROR_REPO", DEFAULT_REPO),
                   help=f"destination GitHub repo (default: {DEFAULT_REPO})")
    p.add_argument("--allowlist", type=Path, default=Path(__file__).parent / "models.json",
                   help="path to the allowlist JSON")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list every model in the handy-computer HF org")
    m = sub.add_parser("mirror", help="download + upload the allowlist as releases")
    m.add_argument("--dry-run", action="store_true", help="print what would happen; don't download or upload")
    args = p.parse_args()

    api = HfApi(token=os.environ.get(HF_TOKEN_ENV))

    if args.cmd == "list":
        return cmd_list(api)
    if args.cmd == "mirror":
        allowlist = load_allowlist(args.allowlist)
        return cmd_mirror(api, allowlist, args.repo, args.dry_run)
    return 2


if __name__ == "__main__":
    sys.exit(main())
