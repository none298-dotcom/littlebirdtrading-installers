#!/usr/bin/env bash
# Export check (EXPORT-01): starts the app on a virtual screen against the synthetic fixture, lets it press the Pine export
# button once, types a path into the save window and checks that the file landed. No source, no credentials.
# usage: run.sh "<command that starts the app>" <label> <folder the save window should write to>
set -u
cmd="$1"; label="$2"; out="$3"
mkdir -p "$out" shots
python3 ci/mock/server.py ci/mock/markets.json & srv=$!
sleep 2
rm -f "$out/test.pine"
xvfb-run -a -s "-screen 0 1440x960x24" bash -c "
  openbox & sleep 3
  JAVA_TOOL_OPTIONS='-Dlbt.api=http://127.0.0.1:8787/api/app -Dlbt.favorites=US,AT -Dlbt.market=US -Dlbt.autoExport=pine' $cmd &
  pid=\$!
  sleep 40
  import -window root shots/$label-1-save-window.png
  xdotool mousemove 600 26 click 1; sleep 1
  xdotool key ctrl+a; sleep 1
  xdotool type --delay 60 '$out/test.pine'; sleep 1
  xdotool key Return; sleep 10
  import -window root shots/$label-2-after-save.png
  kill \$pid" || true
kill "$srv" 2>/dev/null
if [ -s "$out/test.pine" ]; then
  echo "PASS $label: the Pine file was saved to $out"
else
  echo "FAIL $label: nothing was saved to $out"
  exit 1
fi
