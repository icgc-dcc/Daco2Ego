#!/bin/bash
. /daco2ego/set_vars.sh
thttpd -d /uploads -c /upload.cgi -p ${SERVER_PORT:-8081}
/daco2ego/monitor.sh
