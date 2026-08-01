#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


EXPECTED_COMMON_HEAD = "e56cf6b09cca2151bcee244b3d334fb68685ff57"
EXPECTED_CERTIFICATE_SHA256 = (
    "123c66f6dff49a034d0e586fcd4086563e5c3c79500951fd98f00a76402326ee"
)
EXPECTED_KERNELSU_COMMIT = "b0bc817b4e966aa6aa830834eaf6ef765d821d40"


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


def normalized_config(path: Path) -> list[str]:
    lines = path.read_text().splitlines()
    menu_index = lines.index("# KernelSU")
    menu_start = menu_index - 2
    menu_end = lines.index("# end of KernelSU") + 1
    del lines[menu_start:menu_end]
    result = []
    for line in lines:
        if line.startswith("CONFIG_SYSTEM_TRUSTED_KEYS="):
            result.append('CONFIG_SYSTEM_TRUSTED_KEYS=""')
        elif line.startswith("CONFIG_LOCALVERSION="):
            result.append('CONFIG_LOCALVERSION="-4k"')
        else:
            result.append(line)
    return result


def module_versions(path: Path) -> dict[str, str]:
    versions = {}
    for line in run("modprobe", "--show-modversions", str(path)).splitlines():
        parts = line.split()
        if len(parts) == 2:
            versions[parts[1]] = parts[0].lower()
    return dict(sorted(versions.items()))


def symvers(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            result[parts[1]] = parts[0].lower()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", required=True, type=Path)
    parser.add_argument("--cert", required=True, type=Path)
    parser.add_argument("--stock-config", required=True, type=Path)
    parser.add_argument("--official-symvers", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()

    dist = args.dist.expanduser().resolve()
    certificate = args.cert.expanduser().resolve()
    stock_config = args.stock_config.expanduser().resolve()
    official_symvers = args.official_symvers.expanduser().resolve()
    image = dist / "Image"
    config = dist / ".config"
    output_symvers = dist / "vmlinux.symvers"
    vmlinux = dist / "vmlinux"
    smoke = dist / "warsaw_kernelsu_sdk_smoke.ko"
    source_verification_path = dist / "source-verification.json"
    required = [
        image,
        config,
        output_symvers,
        vmlinux,
        smoke,
        source_verification_path,
        certificate,
        stock_config,
        official_symvers,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    checks = {"required_files": {"pass": not missing, "missing": missing}}
    if missing:
        status = "FAIL"
    else:
        source_verification = json.loads(source_verification_path.read_text())
        config_lines = config.read_text().splitlines()
        config_pass = (
            'CONFIG_SYSTEM_TRUSTED_KEYS="stock-gki-signing-cert.pem"' in config_lines
            and 'CONFIG_LOCALVERSION="-4k-J-x-Z-BORE-like"' in config_lines
            and "CONFIG_KSU=y" in config_lines
            and "CONFIG_KSU_VERSION=32525" in config_lines
            and normalized_config(config) == stock_config.read_text().splitlines()
        )
        checks["config"] = {
            "pass": config_pass,
            "localversion": "-4k-J-x-Z-BORE-like",
            "kernelsu": "y",
            "kernelsu_version": 32525,
        }
        checks["vmlinux_symvers"] = {
            "pass": sha256(output_symvers) == sha256(official_symvers),
            "sha256": sha256(output_symvers),
            "official_sha256": sha256(official_symvers),
        }
        certificate_data = certificate.read_bytes()
        checks["stock_certificate"] = {
            "pass": sha256(certificate) == EXPECTED_CERTIFICATE_SHA256
            and image.read_bytes().count(certificate_data) == 1,
            "sha256": sha256(certificate),
            "embedded_occurrence_count": image.read_bytes().count(certificate_data),
        }
        image_strings = run("strings", str(image))
        release_match = re.search(r"Linux version ([^ ]+)", image_strings)
        release = release_match.group(1) if release_match else ""
        vmlinux_strings = run("strings", str(vmlinux))
        checks["identity"] = {
            "pass": release.endswith("-4k-J-x-Z-BORE-like")
            and "KernelSU" in vmlinux_strings,
            "kernel_release": release,
            "kernelsu_string_present": "KernelSU" in vmlinux_strings,
        }
        versions = module_versions(smoke)
        official = symvers(official_symvers)
        crc_mismatches = {
            symbol: {"module": crc, "official": official.get(symbol, "MISSING")}
            for symbol, crc in versions.items()
            if official.get(symbol) != crc
        }
        vermagic = run("modinfo", "-F", "vermagic", str(smoke))
        signature_marker_present = smoke.read_bytes().endswith(
            b"~Module signature appended~\n"
        )
        checks["module_sdk_smoke"] = {
            "pass": vermagic.startswith(release) and not crc_mismatches,
            "vermagic": vermagic,
            "version_crc_count": len(versions),
            "version_crc_mismatches": crc_mismatches,
            "signature_marker_present": signature_marker_present,
            "runtime_loading_approved": False,
        }
        checks["kernelsu_mode"] = {
            "pass": not (dist / "kernelsu.ko").exists(),
            "built_into_image": True,
            "external_kernelsu_module_absent": not (dist / "kernelsu.ko").exists(),
        }
        checks["source_lock"] = {
            "pass": source_verification["status"] == "PASS"
            and source_verification["base_head"] == EXPECTED_COMMON_HEAD
            and source_verification["kernelsu_upstream_commit"]
            == EXPECTED_KERNELSU_COMMIT,
            "common_head": source_verification["common_head"],
            "base_head": source_verification["base_head"],
            "kernelsu_commit": source_verification["kernelsu_upstream_commit"],
        }
        status = "PASS" if all(check["pass"] for check in checks.values()) else "FAIL"

    result = {
        "schema_version": 1,
        "status": status,
        "scope": "Warsaw J-x-Z BORE-like GKI with built-in KernelSU v3.2.5",
        "dist": str(dist),
        "checks": checks,
        "runtime_validated": False,
        "device_loading_approved": False,
        "requires_lkm_free_init_boot_for_first_test": True,
    }
    args.result.expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    args.result.expanduser().resolve().write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()
