# ------------------------------------------------------------------------------
# Copyright (c) Microsoft
# Licensed under the MIT License.
# Written by Bin Xiao (Bin.Xiao@microsoft.com)
# ------------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
import logging
import random

import os
import cv2
import json
import pickle
import torch
import numpy as np
from easydict import EasyDict as edict

from src.dataset.BaseDataset import JointsDataset
from src.utils.imutils import im_to_torch, draw_heatmap
from src.utils.misc import to_torch
from src.utils.imutils import load_image

from .SHP2D import SHP2D
from .Tencent2D import Tencent2D
class SHP_Tencent2D(JointsDataset):
    """docstring for TencentHand"""
    def __init__(self, cfg):
        super(SHP_Tencent2D, self).__init__(cfg)
        self.shp = SHP2D(cfg.SHP)
        self.tencent = Tencent2D(cfg.TENCENT)

    def __len__(self):
        # return 100
        # return len(self.shp)
        # return len(self.shp) * 2
        return len(self.shp) + len(self.tencent)

    def _get_db(self):
        pass

    def __getitem__(self, idx):
        if idx < len(self.shp):
            return self.shp[idx]
        idx -= len(self.shp)
        return self.tencent[idx]

    def eval_result(self, outputs, batch, cfg = None):
        return self.shp.eval_result(outputs, batch, self.cfg)

    def get_preds(self, outputs, batch):
        return self.shp.get_preds(outputs, batch)