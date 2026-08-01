#!/usr/bin/env python3

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


BASE_HEAD = "e56cf6b09cca2151bcee244b3d334fb68685ff57"
BASE_TREE = "c701b2cb3998ed7536f97ae358ba8fcf6c75f1f7"
EXPECTED_INTEGRATION_DIFF = (
    "be4456b6b8a1e95c4f7370289afed5800212c4b8ae948194d4e3286cb1f85e3b"
)
EXPECTED_KERNELSU_TREE = (
    "8b072b71a3257837b9d55b93f4d6d191efc79841fa196042f73fa0abb7f1d059"
)
EXPECTED_KERNELSU_FILES = 91
EXPECTED_KERNELSU_SIZE = 421019
EXPECTED_FRAGMENT = "11aea380c63537602f2dd7aa78ccf5e297a5b9da5d8854d0abb1a8345c99290f"
EXPECTED_CERTIFICATE = "123c66f6dff49a034d0e586fcd4086563e5c3c79500951fd98f00a76402326ee"
EXPECTED_SCMVERSION = "-ge56cf6b09cca-ab15511674"
EXPECTED_SOURCE_DATE_EPOCH = 1779954526


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_sha256(root: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    file_count = 0
    total_size = 0
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        digest.update(relative.encode() + b"\0")
        digest.update(str(len(data)).encode() + b"\0")
        digest.update(hashlib.sha256(data).digest())
        file_count += 1
        total_size += len(data)
    return digest.hexdigest(), file_count, total_size


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    common = workspace / "common"
    package = workspace / "warsaw_enhanced"
    workspace_status = json.loads((common / "workspace_status.json").read_text())
    actual_status = run(
        "git",
        "-C",
        str(common),
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ).stdout.splitlines()
    root_commit = run(
        "git", "-C", str(common), "rev-list", "--max-parents=0", "HEAD"
    ).stdout.splitlines()
    if len(root_commit) != 1:
        raise SystemExit(f"expected one source-snapshot root, found {len(root_commit)}")
    root_tree = run(
        "git", "-C", str(common), "rev-parse", f"{root_commit[0]}^{{tree}}"
    ).stdout.strip()
    actual_diff = run(
        "git",
        "-C",
        str(common),
        "diff",
        root_commit[0],
        "--binary",
        "--",
        "drivers/Kconfig",
        "drivers/Makefile",
    ).stdout.encode()
    tree_hash, file_count, total_size = tree_sha256(common / "drivers/kernelsu")
    checks = {
        "base_snapshot_tree": root_tree == BASE_TREE,
        "common_status_clean": not actual_status,
        "tracked_integration_diff": sha256_bytes(actual_diff)
        == EXPECTED_INTEGRATION_DIFF,
        "kernelsu_tree": tree_hash == EXPECTED_KERNELSU_TREE,
        "kernelsu_file_count": file_count == EXPECTED_KERNELSU_FILES,
        "kernelsu_total_size": total_size == EXPECTED_KERNELSU_SIZE,
        "config_fragment": sha256(package / "jxz-kernelsu.fragment")
        == EXPECTED_FRAGMENT,
        "public_certificate": sha256(package / "stock-gki-signing-cert.der")
        == EXPECTED_CERTIFICATE,
        "scmversion": workspace_status.get("SCMVERSION") == EXPECTED_SCMVERSION,
        "source_date_epoch": workspace_status.get("SOURCE_DATE_EPOCH")
        == EXPECTED_SOURCE_DATE_EPOCH,
    }
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "base_head": BASE_HEAD,
        "base_snapshot_commit": root_commit[0],
        "base_snapshot_tree": root_tree,
        "checks": checks,
        "common_head": run("git", "-C", str(common), "rev-parse", "HEAD").stdout.strip(),
        "kernelsu_upstream_commit": "b0bc817b4e966aa6aa830834eaf6ef765d821d40",
        "kernelsu_tree_sha256": tree_hash,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
