# J-x-Z BORE-like Scheduler Profile

This is the ABI-safe Warsaw alternative to importing the BORE scheduler patch.
It deliberately leaves scheduler structs, GKI symbol CRCs, WALT tunables and
Xiaomi scheduler modules unchanged.

The profile uses standard Android uclamp controls already present in the stock
kernel:

- `latency`: marks `top-app` and `foreground_window` latency-sensitive;
- `balanced`: also sets mild 6.25% and 3.12% utilization floors;
- `burst`: raises those temporary floors to 12.50% and 6.25%;
- `run`: launches one root command and its descendants with a per-task uclamp
  floor; Android does not permit the ADB shell domain to raise its own floor.

EAS remains enabled and the WALT governor remains in control. The module is
disabled by default. `enable` records the current-boot baseline before changing
anything, and `disable` restores that exact snapshot. A boot-ID guard prevents
stale values from an earlier boot being restored.

## Device smoke test

```sh
adb push system/bin/jxz-bore /data/local/tmp/jxz-bore
adb shell su -c 'chmod 0755 /data/local/tmp/jxz-bore'
adb shell su -c '/data/local/tmp/jxz-bore selftest'
adb shell su -c '/data/local/tmp/jxz-bore pulse balanced 10'
adb shell su -c '/data/local/tmp/jxz-bore status'
```

## KernelSU module

```sh
./build_module.sh
```

After installation, no profile starts automatically. Enable persistence only
after manual testing:

```sh
su -c 'jxz-bore autostart balanced'
```

Use `su -c 'jxz-bore autostart off'` to disable future activation and
`su -c 'jxz-bore disable'` to restore the current boot immediately.

This feature may use the **BORE-like** name, but it must not be described as the
upstream BORE scheduler implementation.
