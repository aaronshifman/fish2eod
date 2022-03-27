#!/usr/bin/env bash


wget http://gmsh.info/bin/MacOSX/gmsh-3.0.6-MacOSX.dmg -O gmsh.dmg
sudo hdiutil attach gmsh.dmg
sudo cp -R /Volumes/gmsh-3.0.6-MacOSX/Gmsh.app /Applications
sudo hdiutil unmount /Volumes/gmsh-3.0.6-MacOSX