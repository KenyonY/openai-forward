
import gc
import os
import torch
from transformers.utils import (
    is_torch_cuda_available,
    is_torch_mps_available,
    is_torch_npu_available,
    is_torch_xpu_available,
)


def torch_gc() -> None:
    gc.collect()
    if is_torch_xpu_available():
        torch.xpu.empty_cache()
    elif is_torch_npu_available():
        torch.npu.empty_cache()
    elif is_torch_mps_available():
        torch.mps.empty_cache()
    elif is_torch_cuda_available():
        torch.cuda.empty_cache()


def get_current_device() -> "torch.device":
    if is_torch_xpu_available():
        device = "xpu:{}".format(os.environ.get("LOCAL_RANK", "0"))
    elif is_torch_npu_available():
        device = "npu:{}".format(os.environ.get("LOCAL_RANK", "0"))
    elif is_torch_mps_available():
        device = "mps:{}".format(os.environ.get("LOCAL_RANK", "0"))
    elif is_torch_cuda_available():
        device = "cuda:{}".format(os.environ.get("LOCAL_RANK", "0"))
    else:
        device = "cpu"

    return torch.device(device)


def get_device_count() -> int:
    if is_torch_xpu_available():
        return torch.xpu.device_count()
    elif is_torch_npu_available():
        return torch.npu.device_count()
    elif is_torch_cuda_available():
        return torch.cuda.device_count()
    else:
        return 0
