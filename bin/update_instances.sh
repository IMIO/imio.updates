#!/bin/bash
ScriptLocation="."
if [[ $0 == '/'* ]];
then ScriptLocation="`dirname $0`"
else ScriptLocation="`pwd`"/"`dirname $0`"
fi
stdbuf -o 0 $ScriptLocation/update_instances $@ 2>&1 | tee log_update_instances.txt
