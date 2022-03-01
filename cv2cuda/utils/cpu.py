import psutil
def query_cpu_usage():
    return psutil.getloadavg()[0]
