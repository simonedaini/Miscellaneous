!#/bin/bash

rm kayn
pyinstaller kayn.py --onefile --hidden-import=pynput.keyboard._xorg --hidden-import=pynput.mouse._xorg
mv dist/kayn kayn
rm -rf dist build __pycache__ kayn.spec