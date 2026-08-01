# Provenance and Attribution

## Authoritative base

| Layer | Revision | Role |
|---|---|---|
| AOSP `kernel/common` | `e56cf6b09cca2151bcee244b3d334fb68685ff57` | Exact source base matching official build 15511674 |
| KernelSU | `b0bc817b4e966aa6aa830834eaf6ef765d821d40` | KernelSU v3.2.5 kernel source |
| Warsaw integration | this branch | Kconfig wiring, Android 6.6 adaptation, build profile and validation tools |

The 33-project GKI dependency lock is
`warsaw/manifests/manifest_15511674.xml`. The base source and generated
`vmlinux.symvers` were independently matched to the official Warsaw runtime
evidence before KernelSU was added.

The public branch starts with a source-snapshot root whose tree is byte-for-byte
the tree of AOSP commit `e56cf6b09cca2151bcee244b3d334fb68685ff57`. The exact
local checkout used for reconstruction was intentionally shallow and therefore
could not publish missing parent commits. Full pre-snapshot history remains at
`https://android.googlesource.com/kernel/common`; the `upstream` Git remote points
there. The snapshot-root tree object is
`c701b2cb3998ed7536f97ae358ba8fcf6c75f1f7`.

## Locked integration

- `drivers/Kconfig` SHA-256:
  `d0f5971e085cb288b7440d7a0540a080feef936cb6c62f420192b11918da740a`
- `drivers/Makefile` SHA-256:
  `ae4bf7afcbd8b1c57b02ac5f61cae216e992f2f6471cad9bafa8e400cd8f1006`
- KernelSU integrated-tree SHA-256:
  `8b072b71a3257837b9d55b93f4d6d191efc79841fa196042f73fa0abb7f1d059`
- KernelSU integrated-tree file count: `91`
- KernelSU integrated-tree byte count: `421019`
- KernelSU integration diff SHA-256:
  `be4456b6b8a1e95c4f7370289afed5800212c4b8ae948194d4e3286cb1f85e3b`

The tree hash is calculated over sorted relative paths, file sizes and per-file
SHA-256 values. `warsaw/kleaf/verify_source_state.py` recomputes these values
before every release build.

Relative to the KernelSU kernel subtree at the pinned commit, the integrated
tree has only three code/build adaptations: a fixed `CONFIG_KSU_VERSION`, the
`KSU_SECCOMP_RELEASE_REQUIRES_PF_EXITING` build define, and the matching guarded
`PF_EXITING` path in `policy/app_profile.c`. The upstream `uapi` symlink is
materialized inside `drivers/kernelsu/include/uapi` so the kernel repository is
self-contained.

`workspace_status.json` pins the base AOSP SCM identity and source timestamp so
a clean public commit does not replace the runtime-compatible `ge56cf6b09cca`
identity with the release-documentation commit hash. Product identity is the
explicit `-4k-J-x-Z-BORE-like` config suffix; `BORE-like` denotes the bundled
reversible uclamp profile, not the upstream BORE scheduler patch.

## Attribution policy

The Linux history, copyright notices, SPDX identifiers, license texts and
KernelSU notices are intentionally preserved. J-x-Z authorship applies only to
the Warsaw integration, compatibility work, build tooling and release
documentation. It does not replace the authorship of Linux, AOSP, KernelSU,
Qualcomm, LineageOS, Xiaomi or component-vendor contributors.

Public Qualcomm/Lineage and Xiaomi Annibale trees were used as research and
source-attribution references, but are not vendored here because they are not
the tested Warsaw kernel base. Their exact reference revisions remain recorded
in the private engineering audit and can be cited separately when code is later
ported from them.

## Binary boundary

The public certificate in `warsaw/kleaf/stock-gki-signing-cert.pem` is a
certificate only. It cannot sign code and does not contain Xiaomi's private key.
Stock boot images, modules, firmware and device dumps are not part of this
repository.
