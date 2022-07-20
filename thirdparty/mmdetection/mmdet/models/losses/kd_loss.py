# Copyright (c) OpenMMLab. All rights reserved.
import mmcv
import torch
import torch.nn as nn
import torch.nn.functional as F

from ..builder import LOSSES
from .utils import weighted_loss
import ipdb

@mmcv.jit(derivate=True, coderize=True)
@weighted_loss
def knowledge_distillation_kl_div_loss(pred,
                                       soft_label,
                                       T,
                                       detach_target=True):
    r"""Loss function for knowledge distilling using KL divergence.

    Args:
        pred (Tensor): Predicted logits with shape (N, n + 1).
        soft_label (Tensor): Target logits with shape (N, N + 1).
        T (int): Temperature for distillation.
        detach_target (bool): Remove soft_label from automatic differentiation

    Returns:
        torch.Tensor: Loss tensor with shape (N,).
    """
    assert pred.size() == soft_label.size()
    target = F.softmax(soft_label / T, dim=1)
    if detach_target:
        target = target.detach()

    kd_loss = F.kl_div(
        F.log_softmax(pred / T, dim=1), target, reduction='none').mean(1) * (
            T * T)

    return kd_loss


@LOSSES.register_module()
class KnowledgeDistillationKLDivLoss(nn.Module):
    """Loss function for knowledge distilling using KL divergence.

    Args:
        reduction (str): Options are `'none'`, `'mean'` and `'sum'`.
        loss_weight (float): Loss weight of current loss.
        T (int): Temperature for distillation.
    """

    def __init__(self, reduction='mean', loss_weight=1.0, T=10):
        super(KnowledgeDistillationKLDivLoss, self).__init__()
        assert T >= 1
        self.reduction = reduction
        self.loss_weight = loss_weight
        self.T = T

    def forward(self,
                pred,
                soft_label,
                weight=None,
                avg_factor=None,
                reduction_override=None):
        """Forward function.

        Args:
            pred (Tensor): Predicted logits with shape (N, n + 1).
            soft_label (Tensor): Target logits with shape (N, N + 1).
            weight (torch.Tensor, optional): The weight of loss for each
                prediction. Defaults to None.
            avg_factor (int, optional): Average factor that is used to average
                the loss. Defaults to None.
            reduction_override (str, optional): The reduction method used to
                override the original reduction method of the loss.
                Defaults to None.
        """
        assert reduction_override in (None, 'none', 'mean', 'sum')

        reduction = (
            reduction_override if reduction_override else self.reduction)

        loss_kd = self.loss_weight * knowledge_distillation_kl_div_loss(
            pred,
            soft_label,
            weight,
            reduction=reduction,
            avg_factor=avg_factor,
            T=self.T)

        return loss_kd

@LOSSES.register_module()
class FeatImitate_L2Loss(nn.Module):
    """Loss function for feature imitation in knowledge distilling using L2 Loss.

    Args:
        reduction (str): Options are `'none'`, `'mean'` and `'sum'`.
        loss_weight (float): Loss weight of current loss.
    """

    def __init__(self, reduction='mean', loss_weight=1.0):
        super(FeatImitate_L2Loss, self).__init__()
        self.reduction = reduction
        self.loss_weight = loss_weight
        self.relu = nn.ReLU()

    def forward(self,
                preds,
                targets,
                weight=None,
                avg_factor=None,
                reduction_override=None):
        
        self.reduction = (
            reduction_override if reduction_override else self.reduction)
        total_loss = 0

        if not isinstance(preds, list):
            preds = [preds]
            targets = [targets]

        for pred, target in zip(preds, targets):
            pred = self.relu(pred)
            target = self.relu(target)

            pred = self.normalize_feature(pred)
            target = self.normalize_feature(target)
            
            loss = torch.sum(torch.pow(torch.add(pred, target, alpha=-1) ,2)) / len(pred)
            total_loss += loss
        return self.loss_weight * (total_loss / len(preds))

    def normalize_feature(self, x, mult=1.0):
        x = x.reshape(x.size(0), -1)
        return x / x.norm(2, dim=1, keepdim=True) * mult