import time
import os
from kubernetes import client, config

config.load_incluster_config()

v1 = client.CoreV1Api()

print("hallo test")
time.sleep(3)
print(os.environ.get('JOB_CONFIGMAP'))
print(os.environ.get('JOB_NAME'))
print("hallo test ende")
time.sleep(10)
