import time
import os
import json
import sys
from kubernetes import client, config

def get_current_namespace(self):
    with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace", "r") as file:
        namespace = file.read().strip()
    return namespace

class TargetResolver:
    def __init__(self, backup_config, storage_config):
        self.backup_config = backup_config
        self.storage_config = storage_config

    def find_pvcs_by_labels(self, labels):
        return [] # TODO implement

    def get_pvc(self, namespace, pvc_name):
        v1 = client.CoreV1Api()
        pvc = v1.read_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace)

        pv_name = pvc.spec.volume_name
        pv = v1.read_persistent_volume(name=pv_name)

        pods = v1.list_namespaced_pod(namespace=namespace)
        attached_pods = []

        for pod in pods.items:
            for volume in pod.spec.volumes:
                if volume.persistent_volume_claim and volume.persistent_volume_claim.claim_name == pvc_name:
                    attached_pods.append(pod.metadata.name)

        return {
          pvc: pvc,
          pv: pv,
          pods: attached_pods
        }

    def targets(self):
        result = []
        for target in self.backup_config["targets"]:
            if 'url' in target:
                result.append(target)
            elif target["type"] == 'pvc':
                if 'name' in target:
                    info = get_info(get_current_namespace(), target["name"])
                    result.append({
                       type: "pvc",
                       name: target["name"],
                       namespace: get_current_namespace(),
                       pvc: info["pvc"],
                       pv: info["pv"],
                       pods: info["pods"]
                    })
                elif 'matchLabel' in target:
                    for pvc in self.find_pvcs_by_labels(target["matchLabel"]):
                        info = get_info(get_current_namespace(), pvc)
                        result.append({
                           type: "pvc",
                           name: pvc,
                           namespace: get_current_namespace(),
                           pvc: info["pvc"],
                           pv: info["pv"],
                           pods: info["pods"]
                        })

        return result

class Kentledge:
    def __init__(self):
        config.load_incluster_config()
        self.lastjob = 0

    def get_current_pod_name(self):
        return os.getenv("HOSTNAME")

    def get_own_pod(self):
        v1 = client.CoreV1Api()

        pod_name = self.get_current_pod_name()
        namespace = get_current_namespace()

        return v1.read_namespaced_pod(name=pod_name, namespace=namespace)

    def add_job(self, job):
        namespace = get_current_namespace()
        configmap_name = os.environ.get('JOBSEQUENCE_RESULT_CONFIGMAP')
        print("Fetch " + configmap_name)
        v1 = client.CoreV1Api()

        configmap = v1.read_namespaced_config_map(name=configmap_name, namespace=namespace)

        if configmap.data == None:
            configmap.data = {}

        configmap.data["job-" + str(self.lastjob) + ".yaml"] = json.dumps(job)
        v1.patch_namespaced_config_map(name=configmap_name, namespace=namespace, body=configmap)
        self.lastjob = self.lastjob + 1

    def add_backup_job(self, arg):
        pod = self.get_own_pod()

        container = pod.spec.containers[0]

        self.add_job({
            "spec": {
                "template": {
                    "spec": {
                        "restartPolicy": "Never",
                        "serviceAccountName": pod.spec.service_account_name,
                        "containers": [
                            {
                                "name": container.name,
                                "imagePullPolicy": container.image_pull_policy,
                                "image": container.image,
                                "args": ["python", "backup.py", arg]
                            }
                        ]
                    }
                }
            }
        })

    def get_cluster_storage(self, name):
        custom_api = client.CustomObjectsApi()

        return custom_api.get_cluster_custom_object(
            group="kentledge.deltachaos.de",
            version="v1alpha1",
            plural="clusterbackupstores",
            name=name
        )

    def get_backup_config(self):
        return json.loads(os.environ.get("KENTLEDGE_BACKUP"))

    def get_cluster_storage(self):
        backup_config = self.get_backup_config()
        name = backup_config["clusterBackupStore"]["name"]
        return self.get_cluster_storage(name)

    def target_resolver(self):
        return TargetResolver(self.get_backup_config(), self.get_cluster_storage())


k = Kentledge()

if len( sys.argv ) <= 1:
    for target in k.target_resolver().targets():
        print(target)
    print("Sleep")
    time.sleep(10)
else:
    print("Sleep")
    time.sleep(10)