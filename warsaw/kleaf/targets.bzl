load("//build/bazel_common_rules/dist:dist.bzl", "copy_to_dist_dir")
load("//build/kernel/kleaf:kernel.bzl", "ddk_module", "kernel_build")
load("//common:modules.bzl", "get_gki_modules_list", "get_kunit_modules_list")


def warsaw_kernel(name, defconfig_fragments, extra_module_outs = None, smoke_name = None):
    if extra_module_outs == None:
        extra_module_outs = []

    kernel_build(
        name = name,
        srcs = ["//common:kernel_aarch64_sources"],
        outs = [
            "Image",
            "Image.gz",
            "Image.lz4",
            "System.map",
            "modules.builtin",
            "modules.builtin.modinfo",
            "vmlinux",
            "vmlinux.symvers",
        ],
        implicit_outs = [
            "certs/signing_key.pem",
            "certs/signing_key.x509",
            "scripts/sign-file",
        ],
        module_outs = extra_module_outs,
        module_implicit_outs = get_gki_modules_list("arm64") + get_kunit_modules_list("arm64"),
        build_config = "//common:kernel_aarch64_build_config",
        make_goals = [
            "Image",
            "Image.gz",
            "Image.lz4",
            "modules",
        ],
        collect_unstripped_modules = True,
        defconfig_fragments = defconfig_fragments,
        strip_modules = True,
        keep_module_symvers = True,
        kmi_symbol_list = "//common:android/abi_gki_aarch64",
        additional_kmi_symbol_lists = [
            "//common:aarch64_additional_kmi_symbol_lists",
            "//build/kernel/kleaf:user_kmi_symbol_lists",
        ],
        trim_nonlisted_kmi = True,
        kmi_symbol_list_strict_mode = True,
        protected_exports_list = "//common:android/abi_gki_protected_exports_aarch64",
        protected_modules_list = "//common:gki_aarch64_protected_modules",
        system_trusted_key = ":stock-gki-signing-cert.pem",
        pack_module_env = True,
        ddk_module_defconfig_fragments = [
            "//build/kernel/kleaf/impl/defconfig:signing_modules_disabled",
        ],
    )

    data = [
        ":" + name,
        ":" + name + "_headers",
        ":" + name + "_modules_prepare",
        ":" + name + "_uapi_headers",
    ]
    if smoke_name:
        ddk_module(
            name = smoke_name,
            srcs = ["module_smoke.c"],
            out = smoke_name + ".ko",
            kernel_build = ":" + name,
            deps = ["//common:all_headers"],
        )
        data.append(":" + smoke_name)

    copy_to_dist_dir(
        name = name + "_dist",
        data = data,
        flat = True,
    )
