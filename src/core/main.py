# ------------------------------------------------------------------------------
# Copyright (c) Microsoft
# Licensed under the MIT License.
# Written by Liangjian Chen(kuzphi@gmail.com)
# ------------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import time
import os

from easydict import EasyDict as edict
import numpy as np
import torch

from src import Bar
from src.core.debug import debug
from src.core.evaluate import eval_result
from src.utils.misc import AverageMeter, to_torch, to_cuda, to_cpu, combine

def train(cfg, train_loader, model, metric, log):
    data_time = AverageMeter()
    batch_time = AverageMeter()

    # switch to train mode
    model.train()
    end = time.time()
    bar = Bar('Processing', max=len(train_loader))
    for i, batch in enumerate(train_loader):
        size = batch['weight'].size(0)
        # measure data loading time
        data_time.update(time.time() - end)

        model.set_batch(batch)
        model.step()

        # debug, print intermediate result
        if cfg.DEBUG:
            debug(model.outputs, batch)

        # measure accuracy and record loss
        metric_ = model.eval_result()
        metric_['loss'] = model.loss.item() 
        metric.update(metric_, size)

        # measure elapsed time
        batch_time.update(time.time() - end)
        end = time.time()
        suffix = '({batch}/{size}) Data:{data:.1f}s Batch:{bt:.1f}s Total:{total:} ETA:{eta:} '.format(
                    batch=i + 1,
                    size=len(train_loader),
                    data=data_time.val,
                    bt=batch_time.avg,
                    total=bar.elapsed_td,
                    eta=bar.eta_td)
        for name in metric.names():
            suffix += '{}: {:.4f} '.format(name, metric[name].avg)
        bar.suffix  = suffix
        bar.next()
    log.info(bar.suffix)
    bar.finish()

def validate(cfg, val_loader, model, metric = None, log = None):
    data_time = AverageMeter()    
    batch_time = AverageMeter()

    # switch to evaluate mode
    model.eval()

    num_samples = len(val_loader.dataset)
    all_preds = []

    idx = 0
    bar = Bar('Processing', max=len(val_loader))
    with torch.no_grad():
        end = time.time()
        for i, batch in enumerate(val_loader):

            data_time.update(time.time() - end)

            size = batch['weight'].size(0)

            # measure data loading time
            data_time.update(time.time() - end)
            
            # compute output
            model.set_batch(batch)
            model.forward()
            # debug, print intermediate result
            if cfg.DEBUG:
                debug(model.outputs, batch)

            preds = model.get_preds()
            all_preds.append(preds)

            # measure elapsed time
            batch_time.update(time.time() - end)
            end = time.time()

            suffix = '({batch}/{size}) Data:{data:.1f}s Batch:{bt:.1f}s Total:{total:} ETA:{eta:} '.format(
                        batch=i + 1,
                        size=len(val_loader),
                        data=data_time.val,
                        bt=batch_time.avg,
                        total=bar.elapsed_td,
                        eta=bar.eta_td)

            if cfg.IS_VALID:
                metric_ = model.eval_result()
                metric_['loss'] = model.loss.item()
                metric.update(metric_, size)
                for name in metric.names():
                    suffix += '{}: {:.4f} '.format(name, metric[name].avg)

            bar.suffix  = suffix
            bar.next()

        if log:
            log.info(bar.suffix)
        bar.finish()

    return reduce(combine, all_preds)