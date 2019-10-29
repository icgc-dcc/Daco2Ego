#!/bin/sh
. /daco2ego/set_vars.sh
/daco2ego/make_config.sh
touch ${LOG_FILE}
/daco2ego/daco2ego.py config >> ${LOG_FILE}
