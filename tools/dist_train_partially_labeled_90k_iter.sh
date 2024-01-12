#!/usr/bin/env bash
set -x

CONFIG=configs/PseCo/PseCo_faster_rcnn_r50_caffe_fpn_coco_180k.py   
work_dir=logs           # define your experiment path here

FOLD=1
PERCENT=1

PYTHONPATH="$(dirname $0)/..":$PYTHONPATH

export unsup_start_iter=100
export unsup_warmup_iter=50

python $(dirname "$0")/train.py $CONFIG --work-dir $work_dir  \
    --cfg-options fold=${FOLD} \
                  percent=${PERCENT} \
                  runner.max_iters=1800 \
                  lr_config.step=\[600\] \