#!/system/bin/sh

ui_print "- Installing J-x-Z BORE-like Scheduler Profile"
ui_print "- Default state is disabled; no scheduler value is changed"
set_perm "$MODPATH/system/bin/jxz-bore" 0 0 0755
set_perm "$MODPATH/service.sh" 0 0 0755
