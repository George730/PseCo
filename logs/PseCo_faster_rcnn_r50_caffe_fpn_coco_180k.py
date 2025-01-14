model = dict(
    type='PseCo_FRCNN',
    model=dict(
        type='FasterRCNN',
        backbone=dict(
            type='ResNet',
            depth=50,
            num_stages=4,
            out_indices=(0, 1, 2, 3),
            frozen_stages=1,
            norm_cfg=dict(type='BN', requires_grad=False),
            norm_eval=True,
            style='caffe',
            init_cfg=dict(
                type='Pretrained',
                checkpoint='open-mmlab://detectron2/resnet50_caffe')),
        neck=dict(
            type='FPN',
            in_channels=[256, 512, 1024, 2048],
            out_channels=256,
            num_outs=6,
            add_extra_convs='on_input'),
        rpn_head=dict(
            type='RPNHead',
            in_channels=256,
            feat_channels=256,
            anchor_generator=dict(
                type='AnchorGenerator',
                scales=[4],
                ratios=[0.5, 1.0, 2.0],
                strides=[8, 16, 32, 64, 128]),
            bbox_coder=dict(
                type='DeltaXYWHBBoxCoder',
                target_means=[0.0, 0.0, 0.0, 0.0],
                target_stds=[1.0, 1.0, 1.0, 1.0]),
            loss_cls=dict(
                type='CrossEntropyLoss', use_sigmoid=True, loss_weight=1.0),
            loss_bbox=dict(type='L1Loss', loss_weight=1.0)),
        roi_head=dict(
            type='StandardRoIHead',
            bbox_roi_extractor=dict(
                type='SingleRoIExtractor',
                roi_layer=dict(
                    type='RoIAlign', output_size=7, sampling_ratio=0),
                out_channels=256,
                featmap_strides=[8, 16, 32, 64]),
            bbox_head=dict(
                type='Shared2FCBBoxHead',
                in_channels=256,
                fc_out_channels=1024,
                roi_feat_size=7,
                num_classes=2,
                bbox_coder=dict(
                    type='DeltaXYWHBBoxCoder',
                    target_means=[0.0, 0.0, 0.0, 0.0],
                    target_stds=[0.1, 0.1, 0.2, 0.2]),
                reg_class_agnostic=False,
                loss_cls=dict(
                    type='FocalLoss',
                    use_sigmoid=True,
                    loss_weight=10.0,
                    gamma=2.0,
                    alpha=0.25),
                loss_bbox=dict(type='L1Loss', loss_weight=1.0))),
        train_cfg=dict(
            rpn=dict(
                assigner=dict(
                    type='MaxIoUAssigner',
                    pos_iou_thr=0.7,
                    neg_iou_thr=0.3,
                    min_pos_iou=0.3,
                    match_low_quality=True,
                    ignore_iof_thr=-1),
                sampler=dict(
                    type='RandomSampler',
                    num=256,
                    pos_fraction=0.5,
                    neg_pos_ub=-1,
                    add_gt_as_proposals=False),
                allowed_border=-1,
                pos_weight=-1,
                debug=False),
            rpn_proposal=dict(
                nms_pre=2000,
                max_per_img=1000,
                nms=dict(type='nms', iou_threshold=0.7),
                min_bbox_size=0),
            rcnn=dict(
                assigner=dict(
                    type='MaxIoUAssigner',
                    pos_iou_thr=0.5,
                    neg_iou_thr=0.5,
                    min_pos_iou=0.5,
                    match_low_quality=False,
                    ignore_iof_thr=-1),
                sampler=dict(
                    type='RandomSampler',
                    num=512,
                    pos_fraction=0.25,
                    neg_pos_ub=-1,
                    add_gt_as_proposals=False),
                pos_weight=-1,
                debug=False)),
        test_cfg=dict(
            rpn=dict(
                nms_pre=1000,
                max_per_img=1000,
                nms=dict(type='nms', iou_threshold=0.7),
                min_bbox_size=0),
            rcnn=dict(
                score_thr=0.05,
                nms=dict(type='nms', iou_threshold=0.5),
                max_per_img=100))),
    train_cfg=dict(
        pseudo_label_initial_score_thr=0.3,
        rpn_pseudo_threshold=0.5,
        cls_pseudo_threshold=0.5,
        min_pseduo_box_size=0,
        unsup_weight=2.0,
        use_teacher_proposal=True,
        use_MSL=True,
        PLA_iou_thres=0.4,
        PLA_candidate_topk=12),
    test_cfg=dict(inference_on='teacher'))
dataset_type = 'CocoDataset'
data_root = 'data/coco/'
img_norm_cfg = dict(mean=[1.0, 1.0, 1.0], std=[1.0, 1.0, 1.0], to_rgb=False)
train_pipeline = [
    dict(type='LoadImageFromFile', file_client_args=dict(backend='disk')),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(
        type='Sequential',
        transforms=[
            dict(
                type='RandResize',
                img_scale=[(1333, 480), (1333, 480)],
                multiscale_mode='range',
                keep_ratio=True),
            dict(type='RandFlip', flip_ratio=0.5),
            dict(
                type='OneOf',
                transforms=[
                    dict(type='Identity'),
                    dict(type='AutoContrast'),
                    dict(type='RandEqualize'),
                    dict(type='RandSolarize'),
                    dict(type='RandColor'),
                    dict(type='RandContrast'),
                    dict(type='RandBrightness'),
                    dict(type='RandSharpness'),
                    dict(type='RandPosterize')
                ])
        ],
        record=True),
    dict(type='Pad', size_divisor=32),
    dict(
        type='Normalize',
        mean=[0.0, 0.0, 0.0],
        std=[1.0, 1.0, 1.0],
        to_rgb=False),
    dict(type='ExtraAttrs', tag='sup'),
    dict(type='DefaultFormatBundle'),
    dict(
        type='Collect',
        keys=['img', 'gt_bboxes', 'gt_labels'],
        meta_keys=('filename', 'ori_shape', 'img_shape', 'img_norm_cfg',
                   'pad_shape', 'scale_factor', 'tag'))
]
test_pipeline = [
    dict(type='LoadImageFromFile', file_client_args=dict(backend='disk')),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(1333, 480),
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='RandomFlip'),
            dict(
                type='Normalize',
                mean=[0.0, 0.0, 0.0],
                std=[1.0, 1.0, 1.0],
                to_rgb=False),
            dict(type='Pad', size_divisor=32),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img'])
        ])
]
data = dict(
    samples_per_gpu=5,
    workers_per_gpu=2,
    train=dict(
        type='SemiDataset',
        sup=dict(
            type='CocoDataset',
            ann_file='/home/ubuntu/PseCo/data/sup_coco_data.json',
            img_prefix='/home/ubuntu/PseCo/data/data/',
            pipeline=[
                dict(
                    type='LoadImageFromFile',
                    file_client_args=dict(backend='disk')),
                dict(type='LoadAnnotations', with_bbox=True),
                dict(
                    type='Sequential',
                    transforms=[
                        dict(
                            type='RandResize',
                            img_scale=[(1333, 480), (1333, 480)],
                            multiscale_mode='range',
                            keep_ratio=True),
                        dict(type='RandFlip', flip_ratio=0.5),
                        dict(
                            type='OneOf',
                            transforms=[
                                dict(type='Identity'),
                                dict(type='AutoContrast'),
                                dict(type='RandEqualize'),
                                dict(type='RandSolarize'),
                                dict(type='RandColor'),
                                dict(type='RandContrast'),
                                dict(type='RandBrightness'),
                                dict(type='RandSharpness'),
                                dict(type='RandPosterize')
                            ])
                    ],
                    record=True),
                dict(type='Pad', size_divisor=32),
                dict(
                    type='Normalize',
                    mean=[0.0, 0.0, 0.0],
                    std=[1.0, 1.0, 1.0],
                    to_rgb=False),
                dict(type='ExtraAttrs', tag='sup'),
                dict(type='DefaultFormatBundle'),
                dict(
                    type='Collect',
                    keys=['img', 'gt_bboxes', 'gt_labels'],
                    meta_keys=('filename', 'ori_shape', 'img_shape',
                               'img_norm_cfg', 'pad_shape', 'scale_factor',
                               'tag'))
            ],
            classes=('ghost', 'particle')),
        unsup=dict(
            type='CocoDataset',
            ann_file='/home/ubuntu/PseCo/data/coco_data.json',
            img_prefix='/home/ubuntu/PseCo/data/data/',
            pipeline=[
                dict(
                    type='LoadImageFromFile',
                    file_client_args=dict(backend='disk')),
                dict(type='PseudoSamples', with_bbox=True),
                dict(
                    type='MultiBranch',
                    unsup_student=[
                        dict(
                            type='Sequential',
                            transforms=[
                                dict(
                                    type='RandResize',
                                    img_scale=[(1333, 480), (1333, 480)],
                                    multiscale_mode='range',
                                    keep_ratio=True),
                                dict(type='RandFlip', flip_ratio=0.5),
                                dict(
                                    type='ShuffledSequential',
                                    transforms=[
                                        dict(
                                            type='OneOf',
                                            transforms=[
                                                dict(type='Identity'),
                                                dict(type='AutoContrast'),
                                                dict(type='RandEqualize'),
                                                dict(type='RandSolarize'),
                                                dict(type='RandColor'),
                                                dict(type='RandContrast'),
                                                dict(type='RandBrightness'),
                                                dict(type='RandSharpness'),
                                                dict(type='RandPosterize')
                                            ]),
                                        dict(
                                            type='OneOf',
                                            transforms=[{
                                                'type': 'RandTranslate',
                                                'x': (-0.1, 0.1)
                                            }, {
                                                'type': 'RandTranslate',
                                                'y': (-0.1, 0.1)
                                            }, {
                                                'type': 'RandRotate',
                                                'angle': (-30, 30)
                                            },
                                                        [{
                                                            'type':
                                                            'RandShear',
                                                            'x': (-30, 30)
                                                        }, {
                                                            'type':
                                                            'RandShear',
                                                            'y': (-30, 30)
                                                        }]])
                                    ]),
                                dict(
                                    type='RandErase',
                                    n_iterations=(1, 5),
                                    size=[0, 0.2],
                                    squared=True)
                            ],
                            record=True),
                        dict(type='Pad', size_divisor=32),
                        dict(
                            type='Normalize',
                            mean=[1.0, 1.0, 1.0],
                            std=[1.0, 1.0, 1.0],
                            to_rgb=False),
                        dict(type='ExtraAttrs', tag='unsup_student'),
                        dict(type='DefaultFormatBundle'),
                        dict(
                            type='Collect',
                            keys=['img', 'gt_bboxes', 'gt_labels'],
                            meta_keys=('filename', 'ori_shape', 'img_shape',
                                       'img_norm_cfg', 'pad_shape',
                                       'scale_factor', 'tag',
                                       'transform_matrix', 'flip',
                                       'flip_direction'))
                    ],
                    unsup_teacher=[
                        dict(
                            type='Sequential',
                            transforms=[
                                dict(
                                    type='RandResize',
                                    img_scale=[(1333, 480), (1333, 480)],
                                    multiscale_mode='range',
                                    keep_ratio=True),
                                dict(type='RandFlip', flip_ratio=0.5)
                            ],
                            record=True),
                        dict(type='Pad', size_divisor=32),
                        dict(
                            type='Normalize',
                            mean=[1.0, 1.0, 1.0],
                            std=[1.0, 1.0, 1.0],
                            to_rgb=False),
                        dict(type='ExtraAttrs', tag='unsup_teacher'),
                        dict(type='DefaultFormatBundle'),
                        dict(
                            type='Collect',
                            keys=['img', 'gt_bboxes', 'gt_labels'],
                            meta_keys=('filename', 'ori_shape', 'img_shape',
                                       'img_norm_cfg', 'pad_shape',
                                       'scale_factor', 'tag',
                                       'transform_matrix', 'flip',
                                       'flip_direction'))
                    ])
            ],
            filter_empty_gt=False,
            classes=('ghost', 'particle'))),
    val=dict(
        type='CocoDataset',
        ann_file='/home/ubuntu/PseCo/data/sup_coco_data.json',
        img_prefix='/home/ubuntu/PseCo/data/data/',
        pipeline=[
            dict(
                type='LoadImageFromFile',
                file_client_args=dict(backend='disk')),
            dict(
                type='MultiScaleFlipAug',
                img_scale=(1333, 480),
                flip=False,
                transforms=[
                    dict(type='Resize', keep_ratio=True),
                    dict(type='RandomFlip'),
                    dict(
                        type='Normalize',
                        mean=[0.0, 0.0, 0.0],
                        std=[1.0, 1.0, 1.0],
                        to_rgb=False),
                    dict(type='Pad', size_divisor=32),
                    dict(type='ImageToTensor', keys=['img']),
                    dict(type='Collect', keys=['img'])
                ])
        ]),
    test=dict(
        type='CocoDataset',
        ann_file='/home/ubuntu/PseCo/data/sup_coco_data.json',
        img_prefix='/home/ubuntu/PseCo/data/data/',
        pipeline=[
            dict(
                type='LoadImageFromFile',
                file_client_args=dict(backend='disk')),
            dict(
                type='MultiScaleFlipAug',
                img_scale=(1333, 480),
                flip=False,
                transforms=[
                    dict(type='Resize', keep_ratio=True),
                    dict(type='RandomFlip'),
                    dict(
                        type='Normalize',
                        mean=[0.0, 0.0, 0.0],
                        std=[1.0, 1.0, 1.0],
                        to_rgb=False),
                    dict(type='Pad', size_divisor=32),
                    dict(type='ImageToTensor', keys=['img']),
                    dict(type='Collect', keys=['img'])
                ])
        ]),
    sampler=dict(
        train=dict(
            type='SemiBalanceSampler',
            sample_ratio=[1, 4],
            by_prob=True,
            epoch_length=7330)))
evaluation = dict(
    interval=10000, metric='bbox', type='SubModulesDistEvalHook', start=20000)
optimizer = dict(type='SGD', lr=0.001, momentum=0.9, weight_decay=0.0001)
optimizer_config = dict(grad_clip=None)
lr_config = dict(
    policy='step',
    warmup='linear',
    warmup_iters=500,
    warmup_ratio=0.001,
    step=[600])
runner = dict(type='IterBasedRunner', max_iters=1800)
checkpoint_config = dict(
    interval=5000, by_epoch=False, max_keep_ckpts=10, create_symlink=False)
log_config = dict(
    interval=50, hooks=[dict(type='TextLoggerHook', by_epoch=False)])
custom_hooks = [
    dict(type='NumClassCheckHook'),
    dict(type='WeightSummary'),
    dict(type='MeanTeacher', momentum=0.999, warm_up=0),
    dict(type='GetCurrentIter')
]
dist_params = dict(backend='nccl')
log_level = 'INFO'
load_from = None
resume_from = None
workflow = [('train', 1)]
mmdet_base = '../../thirdparty/mmdetection/configs/_base_'
strong_pipeline = [
    dict(
        type='Sequential',
        transforms=[
            dict(
                type='RandResize',
                img_scale=[(1333, 480), (1333, 480)],
                multiscale_mode='range',
                keep_ratio=True),
            dict(type='RandFlip', flip_ratio=0.5),
            dict(
                type='ShuffledSequential',
                transforms=[
                    dict(
                        type='OneOf',
                        transforms=[
                            dict(type='Identity'),
                            dict(type='AutoContrast'),
                            dict(type='RandEqualize'),
                            dict(type='RandSolarize'),
                            dict(type='RandColor'),
                            dict(type='RandContrast'),
                            dict(type='RandBrightness'),
                            dict(type='RandSharpness'),
                            dict(type='RandPosterize')
                        ]),
                    dict(
                        type='OneOf',
                        transforms=[{
                            'type': 'RandTranslate',
                            'x': (-0.1, 0.1)
                        }, {
                            'type': 'RandTranslate',
                            'y': (-0.1, 0.1)
                        }, {
                            'type': 'RandRotate',
                            'angle': (-30, 30)
                        },
                                    [{
                                        'type': 'RandShear',
                                        'x': (-30, 30)
                                    }, {
                                        'type': 'RandShear',
                                        'y': (-30, 30)
                                    }]])
                ]),
            dict(
                type='RandErase',
                n_iterations=(1, 5),
                size=[0, 0.2],
                squared=True)
        ],
        record=True),
    dict(type='Pad', size_divisor=32),
    dict(
        type='Normalize',
        mean=[1.0, 1.0, 1.0],
        std=[1.0, 1.0, 1.0],
        to_rgb=False),
    dict(type='ExtraAttrs', tag='unsup_student'),
    dict(type='DefaultFormatBundle'),
    dict(
        type='Collect',
        keys=['img', 'gt_bboxes', 'gt_labels'],
        meta_keys=('filename', 'ori_shape', 'img_shape', 'img_norm_cfg',
                   'pad_shape', 'scale_factor', 'tag', 'transform_matrix',
                   'flip', 'flip_direction'))
]
weak_pipeline = [
    dict(
        type='Sequential',
        transforms=[
            dict(
                type='RandResize',
                img_scale=[(1333, 480), (1333, 480)],
                multiscale_mode='range',
                keep_ratio=True),
            dict(type='RandFlip', flip_ratio=0.5)
        ],
        record=True),
    dict(type='Pad', size_divisor=32),
    dict(
        type='Normalize',
        mean=[1.0, 1.0, 1.0],
        std=[1.0, 1.0, 1.0],
        to_rgb=False),
    dict(type='ExtraAttrs', tag='unsup_teacher'),
    dict(type='DefaultFormatBundle'),
    dict(
        type='Collect',
        keys=['img', 'gt_bboxes', 'gt_labels'],
        meta_keys=('filename', 'ori_shape', 'img_shape', 'img_norm_cfg',
                   'pad_shape', 'scale_factor', 'tag', 'transform_matrix',
                   'flip', 'flip_direction'))
]
unsup_pipeline = [
    dict(type='LoadImageFromFile', file_client_args=dict(backend='disk')),
    dict(type='PseudoSamples', with_bbox=True),
    dict(
        type='MultiBranch',
        unsup_student=[
            dict(
                type='Sequential',
                transforms=[
                    dict(
                        type='RandResize',
                        img_scale=[(1333, 480), (1333, 480)],
                        multiscale_mode='range',
                        keep_ratio=True),
                    dict(type='RandFlip', flip_ratio=0.5),
                    dict(
                        type='ShuffledSequential',
                        transforms=[
                            dict(
                                type='OneOf',
                                transforms=[
                                    dict(type='Identity'),
                                    dict(type='AutoContrast'),
                                    dict(type='RandEqualize'),
                                    dict(type='RandSolarize'),
                                    dict(type='RandColor'),
                                    dict(type='RandContrast'),
                                    dict(type='RandBrightness'),
                                    dict(type='RandSharpness'),
                                    dict(type='RandPosterize')
                                ]),
                            dict(
                                type='OneOf',
                                transforms=[{
                                    'type': 'RandTranslate',
                                    'x': (-0.1, 0.1)
                                }, {
                                    'type': 'RandTranslate',
                                    'y': (-0.1, 0.1)
                                }, {
                                    'type': 'RandRotate',
                                    'angle': (-30, 30)
                                },
                                            [{
                                                'type': 'RandShear',
                                                'x': (-30, 30)
                                            }, {
                                                'type': 'RandShear',
                                                'y': (-30, 30)
                                            }]])
                        ]),
                    dict(
                        type='RandErase',
                        n_iterations=(1, 5),
                        size=[0, 0.2],
                        squared=True)
                ],
                record=True),
            dict(type='Pad', size_divisor=32),
            dict(
                type='Normalize',
                mean=[1.0, 1.0, 1.0],
                std=[1.0, 1.0, 1.0],
                to_rgb=False),
            dict(type='ExtraAttrs', tag='unsup_student'),
            dict(type='DefaultFormatBundle'),
            dict(
                type='Collect',
                keys=['img', 'gt_bboxes', 'gt_labels'],
                meta_keys=('filename', 'ori_shape', 'img_shape',
                           'img_norm_cfg', 'pad_shape', 'scale_factor', 'tag',
                           'transform_matrix', 'flip', 'flip_direction'))
        ],
        unsup_teacher=[
            dict(
                type='Sequential',
                transforms=[
                    dict(
                        type='RandResize',
                        img_scale=[(1333, 480), (1333, 480)],
                        multiscale_mode='range',
                        keep_ratio=True),
                    dict(type='RandFlip', flip_ratio=0.5)
                ],
                record=True),
            dict(type='Pad', size_divisor=32),
            dict(
                type='Normalize',
                mean=[1.0, 1.0, 1.0],
                std=[1.0, 1.0, 1.0],
                to_rgb=False),
            dict(type='ExtraAttrs', tag='unsup_teacher'),
            dict(type='DefaultFormatBundle'),
            dict(
                type='Collect',
                keys=['img', 'gt_bboxes', 'gt_labels'],
                meta_keys=('filename', 'ori_shape', 'img_shape',
                           'img_norm_cfg', 'pad_shape', 'scale_factor', 'tag',
                           'transform_matrix', 'flip', 'flip_direction'))
        ])
]
thres = 0.9
refresh = False
fp16 = dict(loss_scale='dynamic')
classes = ('ghost', 'particle')
fold = 1
percent = 1
auto_resume = True
find_unused_parameters = True
backend = 'disk'
work_dir = 'logs'
cfg_name = 'PseCo_faster_rcnn_r50_caffe_fpn_coco_180k'
gpu_ids = range(0, 1)
