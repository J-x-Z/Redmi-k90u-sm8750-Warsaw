#!/usr/bin/env python3

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


EXPECTED_STOCK_BOOT_SHA256 = (
    "0ecd07a132d02f49c111e470898b35d18cf8d725817b5214c7819a23ea7d0442"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(*args: str) -> str:
    return subprocess.run(
        list(args),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def unpack(tool: Path, image: Path, output: Path) -> list[str]:
    output.mkdir(parents=True)
    command = run(
        sys.executable,
        str(tool),
        "--boot_img",
        str(image),
        "--out",
        str(output),
        "--format=mkbootimg",
    )
    return shlex.split(command)


def parse_args(values: list[str]) -> dict[str, str]:
    parsed = {}
    index = 0
    while index < len(values):
        key = values[index]
        if not key.startswith("--") or index + 1 >= len(values):
            raise ValueError(f"unexpected unpack argument sequence: {values}")
        parsed[key] = values[index + 1]
        index += 2
    return parsed


def arm64_header(path: Path) -> dict[str, object]:
    header = path.read_bytes()[:64]
    return {
        "text_offset": int.from_bytes(header[8:16], "little"),
        "image_size": int.from_bytes(header[16:24], "little"),
        "flags": int.from_bytes(header[24:32], "little"),
        "magic_hex": header[56:60].hex(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock-boot", required=True, type=Path)
    parser.add_argument("--candidate-image", required=True, type=Path)
    parser.add_argument("--expected-image-sha256", required=True)
    parser.add_argument("--unpack-tool", required=True, type=Path)
    parser.add_argument("--mkbootimg-tool", required=True, type=Path)
    parser.add_argument("--cmdline", default="")
    parser.add_argument("--partition-size", type=int, default=100663296)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()

    stock_boot = args.stock_boot.expanduser().resolve()
    candidate = args.candidate_image.expanduser().resolve()
    output = args.output.expanduser().resolve()
    result_path = args.result.expanduser().resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    if sha256(stock_boot) != EXPECTED_STOCK_BOOT_SHA256:
        raise SystemExit("stock boot hash mismatch")
    if sha256(candidate) != args.expected_image_sha256.lower():
        raise SystemExit("candidate Image hash mismatch")

    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        stock_dir = temporary_path / "stock"
        output_dir = temporary_path / "output"
        stock_args = parse_args(unpack(args.unpack_tool, stock_boot, stock_dir))
        stock_kernel = Path(stock_args["--kernel"])
        stock_ramdisk = Path(stock_args["--ramdisk"])
        stock_checks = {
            "header_version": stock_args.get("--header_version"),
            "cmdline": stock_args.get("--cmdline"),
            "kernel_sha256": sha256(stock_kernel),
            "kernel_size": stock_kernel.stat().st_size,
            "ramdisk_sha256": sha256(stock_ramdisk),
            "ramdisk_size": stock_ramdisk.stat().st_size,
            "arm64_header": arm64_header(stock_kernel),
        }
        candidate_header = arm64_header(candidate)
        stock_pass = (
            stock_checks["header_version"] == "4"
            and stock_checks["cmdline"] == ""
            and stock_checks["ramdisk_size"] == 0
            and stock_checks["arm64_header"]["magic_hex"] == "41524d64"
        )
        candidate_pass = (
            candidate_header["magic_hex"] == "41524d64"
            and candidate_header["text_offset"]
            == stock_checks["arm64_header"]["text_offset"]
            and candidate_header["flags"] == stock_checks["arm64_header"]["flags"]
            and candidate_header["image_size"] >= candidate.stat().st_size
        )
        if not stock_pass or not candidate_pass:
            raise SystemExit("boot or candidate Image is outside the locked profile")

        output.parent.mkdir(parents=True, exist_ok=True)
        run(
            sys.executable,
            str(args.mkbootimg_tool),
            "--header_version",
            "4",
            "--kernel",
            str(candidate),
            "--ramdisk",
            str(stock_ramdisk),
            "--cmdline",
            args.cmdline,
            "--output",
            str(output),
        )
        output_args = parse_args(unpack(args.unpack_tool, output, output_dir))
        output_kernel = Path(output_args["--kernel"])
        output_ramdisk = Path(output_args["--ramdisk"])
        output_checks = {
            "header_version": output_args.get("--header_version"),
            "cmdline": output_args.get("--cmdline"),
            "kernel_sha256": sha256(output_kernel),
            "kernel_size": output_kernel.stat().st_size,
            "ramdisk_sha256": sha256(output_ramdisk),
            "ramdisk_size": output_ramdisk.stat().st_size,
            "arm64_header": arm64_header(output_kernel),
            "boot_image_sha256": sha256(output),
            "boot_image_size": output.stat().st_size,
        }
        output_pass = (
            output_checks["header_version"] == stock_checks["header_version"]
            and output_checks["cmdline"] == args.cmdline
            and output_checks["kernel_sha256"] == args.expected_image_sha256.lower()
            and output_checks["kernel_size"] == candidate.stat().st_size
            and output_checks["ramdisk_sha256"] == stock_checks["ramdisk_sha256"]
            and output_checks["ramdisk_size"] == stock_checks["ramdisk_size"]
            and output_checks["arm64_header"] == candidate_header
            and output_checks["boot_image_size"] <= args.partition_size
        )

    result = {
        "schema_version": 1,
        "status": "PASS" if stock_pass and candidate_pass and output_pass else "FAIL",
        "scope": "Warsaw Android boot V4 temporary image with kernel-only replacement",
        "stock_boot": {
            "path": str(stock_boot),
            "sha256": EXPECTED_STOCK_BOOT_SHA256,
            "file_size": stock_boot.stat().st_size,
            "unpacked": stock_checks,
        },
        "candidate_image": {
            "path": str(candidate),
            "sha256": sha256(candidate),
            "file_size": candidate.stat().st_size,
            "arm64_header": candidate_header,
        },
        "test_boot": {"path": str(output), "unpacked": output_checks},
        "partition_size": args.partition_size,
        "intentional_cmdline_delta": args.cmdline,
        "kernel_only_replacement_verified": output_pass,
        "temporary_boot_only": True,
        "partition_write_approved": False,
        "runtime_validated": False,
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
