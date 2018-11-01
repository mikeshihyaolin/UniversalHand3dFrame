from __future__ import absolute_import

import numpy as np
import os
import shutil
import torch 
import time
import yaml
import pickle
import warnings
from easydict import EasyDict as edict

class AverageMeter(object):
    """Computes and stores the average and current value"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        val = float(val)
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count if self.count != 0 else 0

class MetricMeter(object):
    """docstring for MetricMeter"""
    def __init__(self, metric_item):
        super(MetricMeter, self).__init__()
        self.metric = {}
        for name in metric_item:
            self.metric[name] = AverageMeter()

    def update(self, metric_update, size):
        for name in self.metric:
            if metric_update.has_key(name):
                self.metric[name].update(metric_update[name], size)
            else:
                raise Exception("{} does not found in update dic".format(name))
    def __getitem__(self, idx):
        return self.metric[idx]

    def names(self):
        return self.metric.keys()
def to_numpy(tensor):
    if torch.is_tensor(tensor):
        return tensor.cpu().numpy()
    elif type(tensor).__module__ != 'numpy':
        raise ValueError("Cannot convert {} to numpy array"
                         .format(type(tensor)))
    return tensor

def to_torch(ndarray):
    if type(ndarray).__module__ == 'numpy':
        return torch.from_numpy(ndarray).float()
    elif not torch.is_tensor(ndarray):
        raise ValueError("Cannot convert {} to torch tensor"
                         .format(type(ndarray)))
    return ndarray.float()

def to_cpu(outputs):
    if isinstance(outputs,dict):
        return {key: to_cpu(outputs[key]) for key in outputs}
    if isinstance(outputs,list):
        return [to_cpu(output) for output in outputs]
    if isinstance(outputs, torch.Tensor):
        return outputs.detach().cpu() if outputs.is_cuda else outputs        
    # return outputs
    raise Exception("Unrecognized type {}".format(type(output)))

def to_cuda(outputs):
    if isinstance(outputs,dict): 
        return {key: to_cuda(outputs[key]) for key in outputs}
    if isinstance(outputs,list):
        return [to_cuda(output) for output in outputs]
    if isinstance(outputs, torch.Tensor):
        return outputs if not outputs.is_cuda else outputs.cuda()

    raise Exception("Unrecognized type {}".format(type(output)))
    # return outputs

def combine(x , y):
    assert type(x) == type(y), 'combine two different type items {} and {}'.format(type(x), type(y))
    if isinstance(x, dict):
        assert x.keys() == y.keys()
        return {kx: combine(x[kx],y[kx]) for kx in x}
    if isinstance(x, list):
        assert len(x) == len(y), 'lists size does not match'
        return [combine(a,b) for a, b in zip(x, y)]
    if isinstance(x, torch.Tensor):
        return torch.cat([x,y], 0)
    if isinstance(x, np.ndarray):
        return np.concatenate([x,y], 0)
    raise Exception("Unrecognized type {}".format(type(x)))

def get_config(fpath, type = 'train'):
    cfg = yaml.load(open(fpath))
    cfg = edict(cfg)

    tag = time.asctime(time.localtime(time.time()))
    tag = tag[4:-5] #remove day of the week and year
    
    if type == 'train':
        cfg.TAG = "_".join([tag, type, cfg.MODEL.NAME, cfg.TRAIN.DATASET.NAME])
        cfg.LOG.PATH = os.path.join(cfg.OUTPUT_DIR,cfg.TAG,'log.json')
        cfg.CHECKPOINT = os.path.join(cfg.OUTPUT_DIR,cfg.TAG)
        cfg.START_EPOCH = cfg.CURRENT_EPOCH #fresuming training
    if type == 'infer':
        cfg.TAG = "_".join([tag, type, cfg.MODEL.NAME, cfg.DATASET.NAME])
        cfg.CHECKPOINT = os.path.join(cfg.OUTPUT_DIR,cfg.TAG)
        cfg.IMG_RESULT = os.path.join(cfg.CHECKPOINT, 'img_result')
    return cfg

def save_config(cfg, fpath):
    cfg.RESUME_TRAINING = 1
    configpath = os.path.join(fpath, 'config.yml')
    yaml.dump(cfg, open(configpath,"w"))

def save_checkpoint(state, preds, cfg, log, is_best, fpath, filename='checkpoint.pth.tar', snapshot=None):
    preds = to_numpy(preds)
    latest_filepath = os.path.join(fpath, 'latest')

    if not os.path.exists(latest_filepath):
        os.makedirs(latest_filepath)

    log.save(latest_filepath)
    save_config(cfg, latest_filepath)
    torch.save(state, os.path.join(latest_filepath, filename))
    preds.dump(os.path.join(latest_filepath, 'preds.npy'))
    if snapshot and state['epoch'] % snapshot == 0:
        shutil.copytree(latest_filepath, os.path.join(fpath, str(state['epoch'])))

    if is_best:
        best_path = os.path.join(fpath, "best")
        if os.path.exists(best_path):
            shutil.rmtree(best_path)
        shutil.copytree(latest_filepath, best_path)

def save_preds(preds, checkpoint='checkpoint', filename='preds.pickle'):
    if not os.path.exists(checkpoint):
        os.makedirs(checkpoint)
    filepath = os.path.join(checkpoint, filename)
    pickle.dump(preds, open(filepath,"w"))
