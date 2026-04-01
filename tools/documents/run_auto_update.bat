@echo off
echo Starting Auto Update with Windows compatibility...
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set HF_HUB_DISABLE_SYMLINKS=1
python tools/documents/auto_update.py
