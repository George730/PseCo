_base_ = "base.py"

model = dict(
    neck=dict(
        num_outs=6,
        add_extra_convs='on_input'
    ),
    rpn_head=dict(
        anchor_generator=dict(
            type='AnchorGenerator',
            scales=[4],
            ratios=[0.5, 1.0, 2.0],
            strides=[8, 16, 32, 64, 128]),
    ),
    roi_head=dict(
        bbox_roi_extractor=dict(
            type='SingleRoIExtractor',
            roi_layer=dict(type='RoIAlign', output_size=7, sampling_ratio=0),
            out_channels=256,
            featmap_strides=[8, 16, 32, 64]),
        bbox_head=dict(
            loss_cls=dict(
                type='FocalLoss',
                use_sigmoid=True,
                gamma=2.0,
                alpha=0.25,
                loss_weight=10.0),
            num_classes=2,
        ),
    ),
    train_cfg=dict(
        rcnn=dict(
            sampler=dict(
                add_gt_as_proposals=False
            ),
        ),
    ),
)

classes = ('ghost', 'particle',)
# img_norm_cfg = dict(mean=[103.530, 116.280, 123.675], std=[1.0, 1.0, 1.0], to_rgb=False)
img_norm_cfg = dict(mean=[1.0, 1.0, 1.0], std=[1.0, 1.0, 1.0], to_rgb=False)

strong_pipeline = [
    dict(
        type="Sequential",
        transforms=[
            dict(
                type="RandResize",
                img_scale=[(1333, 480), (1333, 480)],   
                multiscale_mode="range",
                keep_ratio=True,
            ),
            dict(type="RandFlip", flip_ratio=0.5),
            dict(
                type="ShuffledSequential",
                transforms=[
                    dict(
                        type="OneOf",
                        transforms=[
                            dict(type=k)
                            for k in [
                                "Identity",
                                "AutoContrast",
                                "RandEqualize",
                                "RandSolarize",
                                "RandColor",
                                "RandContrast",
                                "RandBrightness",
                                "RandSharpness",
                                "RandPosterize",
                            ]
                        ],
                    ),
                    dict(
                        type="OneOf",
                        transforms=[
                            dict(type="RandTranslate", x=(-0.1, 0.1)),
                            dict(type="RandTranslate", y=(-0.1, 0.1)),
                            dict(type="RandRotate", angle=(-30, 30)),
                            [
                                dict(type="RandShear", x=(-30, 30)),
                                dict(type="RandShear", y=(-30, 30)),
                            ],
                        ],
                    ),
                ],
            ),
            dict(
                type="RandErase",
                n_iterations=(1, 5),
                size=[0, 0.2],
                squared=True,
            ),
        ],
        record=True,
    ),
    dict(type="Pad", size_divisor=32),
    dict(type="Normalize", **img_norm_cfg),
    dict(type="ExtraAttrs", tag="unsup_student"),
    dict(type="DefaultFormatBundle"),
    dict(
        type="Collect",
        keys=["img", "gt_bboxes", "gt_labels"],
        meta_keys=(
            "filename",
            "ori_shape",
            "img_shape",
            "img_norm_cfg",
            "pad_shape",
            "scale_factor",
            "tag",
            "transform_matrix",
            "flip",
            "flip_direction"
        ),
    ),
]
weak_pipeline = [
    dict(type="Sequential",
        transforms=[
        dict(
            type="RandResize",
            img_scale=[(1333, 480), (1333, 480)],    
            multiscale_mode="range",
            keep_ratio=True,
        ),
        dict(type="RandFlip", flip_ratio=0.5)],
        record=True,
    ),
    dict(type="Pad", size_divisor=32),
    dict(type="Normalize", **img_norm_cfg),
    dict(type="ExtraAttrs", tag="unsup_teacher"),
    dict(type="DefaultFormatBundle"),
    dict(
        type="Collect",
        keys=["img", "gt_bboxes", "gt_labels"],
        meta_keys=(
            "filename",
            "ori_shape",
            "img_shape",
            "img_norm_cfg",
            "pad_shape",
            "scale_factor",
            "tag",
            "transform_matrix",
            "flip",
            "flip_direction"
        ),
    ),
]

unsup_pipeline = [
    dict(type="LoadImageFromFile", file_client_args=dict(backend="${backend}")),
    # dict(type="LoadAnnotations", with_bbox=True),
    # generate fake labels for data format compatibility
    # dict(type='Grayscale'),
    dict(type="PseudoSamples", with_bbox=True),
    dict(
        type="MultiBranch", unsup_student=strong_pipeline, unsup_teacher=weak_pipeline
    ),
]

data = dict(
    samples_per_gpu=5,
    workers_per_gpu=2,
    train=dict(
        sup=dict(
            type="CocoDataset",
            classes=classes,
            ann_file="/home/ubuntu/PseCo/data/sup_coco_data.json",
            img_prefix="/home/ubuntu/PseCo/data/data/",
            # ann_file="/home/ubuntu/PseCo/data/coco/annotations/semi_supervised/instances_train2017.6@1.json",
            # img_prefix="/home/ubuntu/PseCo/data/coco/images/val2017",
        ),
        unsup=dict(
            type="CocoDataset",
            classes=classes,
            ann_file="/home/ubuntu/PseCo/data/coco_data.json",
            img_prefix="/home/ubuntu/PseCo/data/data/",
            # ann_file="/home/ubuntu/PseCo/data/coco/annotations/semi_supervised/instances_train2017.6@1-unlabeled.json",
            # img_prefix="/home/ubuntu/PseCo/data/coco/images/val2017",
            pipeline=unsup_pipeline,
        ),
    ),
    sampler=dict(
        train=dict(
            sample_ratio=[1, 4],
        )
    ),
)

semi_wrapper = dict(
    type="PseCo_FRCNN",
    model="${model}",
    train_cfg=dict(
        pseudo_label_initial_score_thr=0.3,
        rpn_pseudo_threshold=0.5,
        cls_pseudo_threshold=0.5,
        min_pseduo_box_size=0,
        unsup_weight=2.0,
        use_teacher_proposal=True,    
        use_MSL=True,
        # ------ PLA config ------- #
        PLA_iou_thres=0.4,
        PLA_candidate_topk=12,
    ),
    test_cfg=dict(
        inference_on="teacher"
        ),
)

fold = 1
percent = 1

custom_hooks = [
    dict(type="NumClassCheckHook"),
    dict(type="WeightSummary"),
    dict(type="MeanTeacher", momentum=0.999, warm_up=0),
    dict(type="GetCurrentIter")
]

auto_resume=True 
find_unused_parameters=True 
backend="disk"