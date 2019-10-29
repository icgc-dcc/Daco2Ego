#!/bin/bash
. /daco2ego/set_vars.sh
thttpd -d /uploads -c /upload.cgi -p ${PORT:-8080}
/daco2ego/monitor.sh
sleep 999999
