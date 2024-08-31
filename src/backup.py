import time
import os
import json
from kubernetes import client, config

config.load_incluster_config()

def get_current_namespace():
    with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace", "r") as file:
        namespace = file.read().strip()
    return namespace

def get_current_pod_name():
    return os.getenv("HOSTNAME")

def get_serviceaccount_name():
    config.load_incluster_config()

    v1 = client.CoreV1Api()

    pod_name = get_current_pod_name()
    namespace = get_current_namespace()

    pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)

    serviceaccount_name = pod.spec.service_account_name
    return serviceaccount_name

lastjob = 0
def add_job(job):
    global lastjob
    namespace = get_current_namespace()
    configmap_name = os.environ.get('JOBSEQUENCE_RESULT_CONFIGMAP')
    print("Fetch " + configmap_name)
    v1 = client.CoreV1Api()

    job["restartPolicy"] = "Never"
    job["serviceAccountName"] = get_serviceaccount_name()

    configmap = v1.read_namespaced_config_map(name=configmap_name, namespace=namespace)

    if configmap.data == None:
        configmap.data = {}

    configmap.data["job-" + str(lastjob) + ".yaml"] = json.dumps({"spec": {"template": {"spec": job}}})
    v1.patch_namespaced_config_map(name=configmap_name, namespace=namespace, body=configmap)
    lastjob = lastjob + 1

print("hallo test")
time.sleep(3)
print("hallo test ende")
time.sleep(10)
add_job({
    "containers": [
      {
        "name": "runner",
        "image": "busybox",
        "cmd": ["/bin/sleep", "10"]
      }
    ]
})
add_job({
    "containers": [
      {
        "name": "runner",
        "image": "busybox",
        "cmd": ["/bin/sleep", "20"]
      }
    ]
})