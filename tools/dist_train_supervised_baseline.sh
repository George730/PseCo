#!/usr/bin/env bash

CONFIG=configs/supervised_baseline/faster_rcnn_r50_caffe_fpn_coco_partial_180k.py
work_dir=logs            # define your experiment path here

PYTHONPATH="$(dirname $0)/..":$PYTHONPATH

python $(dirname "$0")/train.py $CONFIG --work-dir $work_dir 

