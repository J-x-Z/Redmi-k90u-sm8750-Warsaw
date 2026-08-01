#!/system/bin/sh

MODDIR="${0%/*}"
CONFIG="/data/adb/jxz-bore-like/autostart"
LOG="/data/local/tmp/jxz-bore-like-service.log"

[ -r "$CONFIG" ] || exit 0
profile="$(cat "$CONFIG" 2>/dev/null)"
case "$profile" in
    latency|balanced|burst) ;;
    *) exit 0 ;;
esac

attempt=0
while [ "$(getprop sys.boot_completed)" != "1" ] && [ "$attempt" -lt 60 ]
do
    sleep 2
    attempt=$((attempt + 1))
done

{
    echo "$(date '+%Y-%m-%d %H:%M:%S') profile=$profile kernel=$(uname -r)"
    "$MODDIR/system/bin/jxz-bore" enable "$profile"
} >> "$LOG" 2>&1
