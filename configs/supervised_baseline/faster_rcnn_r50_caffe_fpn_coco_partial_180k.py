_base_ = "base.py"
fold = 1
percent = 1
classes = ('ghost', 'particle',)
data = dict(
    samples_per_gpu=1,
    workers_per_gpu=1,
    train=dict(
        ann_file="/home/ubuntu/PseCo/data/sup_coco_data.json",
        img_prefix="/home/ubuntu/PseCo/data/data/",
        classes=classes,
        # ann_file="../data/annotations/semi_supervised/instances_train2017.${fold}@${percent}.json",
        # img_prefix="../data/train2017/",
    ),
    val=dict(
        ann_file="/home/ubuntu/PseCo/data/sup_coco_data.json",
        img_prefix="/home/ubuntu/PseCo/data/data/",
        classes=classes,
        # ann_file="../data/annotations/semi_supervised/instances_train2017.${fold}@${percent}.json",
        # img_prefix="../data/train2017/",
    ),
    test=dict(
        ann_file="/home/ubuntu/PseCo/data/sup_coco_data.json",
        img_prefix="/home/ubuntu/PseCo/data/data/",
        classes=classes,
        # ann_file="../data/annotations/semi_supervised/instances_train2017.${fold}@${percent}.json",
        # img_prefix="../data/train2017/",
    ),
)

log_config = dict(
    interval=50,
    hooks=[
        dict(type="TextLoggerHook"),
    ],
)
