# Redmi K90 Ultra / Warsaw SM8750 Kernel

This repository contains the first reproducible J-x-Z kernel source release
for the Xiaomi `warsaw` engineering device. The SoC is **SM8750**; `sm3750`
was an earlier naming typo and is not used here.

## What is included

- exact AOSP Android 15 GKI 6.6 base at
  `e56cf6b09cca2151bcee244b3d334fb68685ff57`;
- KernelSU v3.2.5 kernel sources based on
  `b0bc817b4e966aa6aa830834eaf6ef765d821d40`;
- the Android 6.6 seccomp-release compatibility fix used by the tested image;
- `CONFIG_LOCALVERSION="-4k-J-x-Z-BORE-like"` and the locked Kleaf build target;
- a public stock GKI signing certificate used only as a trust anchor;
- boot-image packaging and ABI verification tools;
- the reversible **J-x-Z BORE-like** uclamp profile.

## Runtime status

The kernel image built from this source booted successfully with `fastboot
boot` on the target device and reached a boot-complete Android desktop. The
runtime release was:

```text
6.6.118-android15-8-ge56cf6b09cca-ab15511674-4k-J-x-Z-BORE-like
```

Built-in KernelSU worked from the documented engineering bootstrap command
line, SELinux remained Enforcing, and the old external KernelSU LKM was absent.
No boot, init_boot, vendor_boot, DTBO, hypervisor or firmware partition needs to
be written to reproduce the temporary-boot test.

## Deliberate boundaries

This is a **hybrid kernel source**, not a fabricated full OEM drop:

- stock Warsaw DTB and DTBO remain authoritative;
- stock vendor modules and firmware remain in use unless a replacement passes
  independent ABI and runtime validation;
- Xiaomi Annibale/K90 sibling-product source is not copied into this repository
  or presented as Warsaw source;
- no stock image, proprietary module, firmware, private signing key or modem
  data is distributed here.

The failed container configuration experiment is not shipped in this public
tree. It changed thousands of GKI symbol CRCs. Docker-grade kernel namespaces
and cgroups must wait for rebuildable vendor modules or an official Warsaw
source release.

The upstream BORE patch is also excluded because it changes scheduler data
structures. `warsaw/bore-like/` uses existing Android uclamp controls, preserves
EAS/WALT and can restore the exact current-boot baseline. The `BORE-like` uname
branding identifies this compatible profile; it does not claim the upstream
BORE scheduler patch is present.

## Start here

1. Read `PROVENANCE.md`.
2. Follow `BUILDING.md` on Linux x86-64.
3. Run all offline verification before creating a boot image.
4. Test with `fastboot boot` only.
5. Never flash both bootable slots during early validation.

There is no warranty. Keep known-good boot and init_boot images available before
testing any custom kernel.
