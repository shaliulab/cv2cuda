import pynvml as N # type: ignore

def init_pynvml_handlers(index):
    N.nvmlInit()
    handle = N.nvmlDeviceGetHandleByIndex(int())
    return N, handle

def query_gpu_usage(pynvml_handles):
    N, handle = pynvml_handles
    memory = N.nvmlDeviceGetMemoryInfo(handle)
    utilization_gpu = 100 * (memory.used / memory.total)
    return utilization_gpu

def query_encoder_usage(pynvml_handles):
    N, handle = pynvml_handles
    utilization_enc, _ = N.nvmlDeviceGetEncoderUtilization(handle)
    return utilization_enc
