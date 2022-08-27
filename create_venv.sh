#!/bin/bash

# learn more in documentation
# Official python docs: https://docs.python.org/3/library/venv.html
# Superviely developer portal: https://developer.supervise.ly/getting-started/installation#venv

if [ -d ".venv" ]; then
    echo "VENV already exists, will be removed"
    rm -rf .venv
fi

echo "VENV will be created" && \
python3 -m venv .venv && \
source .venv/bin/activate && \

echo "Install requirements..." && \
pip3 install -r requirements.txt && \

arch=$(uname -m)
ARCHFLAGS="-arch x86_64" 
if [[ $arch == arm* ]]; then
  echo "------> Running on MAC ..."
  ARCHFLAGS="-arch arm64e"
fi

CC=clang CXX=clang++ ARCHFLAGS=$ARCHFLAGS python3 -m pip install git+https://github.com/facebookresearch/detectron2.git

# pycocotools via the github repo instead of pypi for better compatibility 
pip install "git+https://github.com/open-mmlab/cocoapi.git#subdirectory=pycocotools"
# ARCHFLAGS=$ARCHFLAGS python3 -m pip install -U pycocotools

echo "Requirements have been successfully installed" && \

echo "Testing imports, please wait a minute ..." && \
python -c "import supervisely as sly" && \
echo "Success!" && \

deactivate