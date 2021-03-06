# ------------------------------------------------------------------------------
# Copyright (c) Microsoft
# Licensed under the MIT License.
# Written by Bin Xiao (Bin.Xiao@microsoft.com)
# ------------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
from abc import abstractmethod
from torch.utils.data import Dataset

class JointsDataset(Dataset):
    def __init__(self, cfg):
        self.cfg = cfg
        self.is_train = cfg.IS_TRAIN
        self.db = self._get_db()

    def _get_db(self):
        raise NotImplementedError

    def evaluate(self, cfg, preds, output_dir, *args, **kwargs):
        raise NotImplementedError

    def __len__(self):
        return len(self.db)

    @abstractmethod
    def __getitem__(self, idx):
        #return a dict which contains at least input, target, target_weight, meta
        #input itself is a dict as well
        pass

    @abstractmethod
    def eval_result(self, outputs, batch, cfg = None,  **kwargs):
        #should be same as self.cfg.metric item
        pass

class InferenceDataset(Dataset):
    """docstring for InferenceDataset"""
    def __init__(self, cfg):
        super(InferenceDataset, self).__init__()
        self.data_form = cfg.DATA_FORM
        self.path = cfg.DATA_PATH
        self.db = self._get_db()

    def _get_db(self):
        if self.data_form == 'img_root':
            result = []
            for img in os.listdir(self.path):
                if img.endswith('jpg') or img.endswith('png'):
                    result.append(os.path.join(self.path,img))
            return sorted(result)
        elif self.data_form == 'block_file':
            if self.path.endswith('pickle'):
                import pickle
                img = pickle.load(open(self.path,'r'))

            elif self.path.endswith('h5'):
                import h5py                
                img = h5py.File(self.path) 
            else:
                raise RuntimeError('can not load {}'.format(self.path))
            return img
        raise RuntimeError('could not recognize {}'.format(self.data_form))

    def __len__(self,):
        return len(self.db)

    @abstractmethod
    def __getitem__(self, idx):
        raise NotImplementedError

    @abstractmethod        
    def get_preds(outputs):
        pass 

    @abstractmethod
    def eval_result(self, outputs, batch, cfg = None,  **kwargs):
        #should be same as self.cfg.metric item
        pass