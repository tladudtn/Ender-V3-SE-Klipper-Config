#!/bin/sh
# Link ds18b20_sysfs.py into Klipper's extras directory
set -e
KLIPPER_DIR="${KLIPPER_DIR:-$HOME/klipper}"
SRC="$(cd "$(dirname "$0")" && pwd)/ds18b20_sysfs.py"
ln -sfn "$SRC" "$KLIPPER_DIR/klippy/extras/ds18b20_sysfs.py"
echo "Linked $SRC -> $KLIPPER_DIR/klippy/extras/ds18b20_sysfs.py"
