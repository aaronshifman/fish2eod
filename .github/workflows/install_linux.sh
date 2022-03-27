#!/usr/bin/env bash

wget https://gmsh.info/bin/Linux/gmsh-3.0.6-Linux64.tgz -q -O gmsh.tgz
tar -zxf gmsh.tgz
chmod +x gmsh-3.0.6-Linux64/bin/gmsh

if [[ -z "${READTHEDOCS}" ]]; then
  sudo cp gmsh-3.0.6-Linux64/bin/gmsh /usr/bin/gmsh
  sudo apt-get -y install libglu1-mesa
else
  cp gmsh-3.0.6-Linux64/bin/gmsh ./
fi

echo "Done"