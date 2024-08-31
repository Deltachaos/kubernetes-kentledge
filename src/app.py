from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import base64
import yaml
from re import L
import kubernetes
from io import StringIO
import os
import re

class Controller(BaseHTTPRequestHandler):
  def dump(self, obj):
    self.log_message("%s", json.dumps(obj))

  def sync(self, parent, children):

    clusterRole = os.environ.get("KUBERNETES_CLUSTERROLE")
    kentledgeImage = os.environ.get("KENTLEDGE_IMAGE")
    kentledgePullPolicy = os.environ.get("KENTLEDGE_PULLPOLICY")
    jobsequenceImage = os.environ.get("JOBSEQUENCE_IMAGE")
    jobsequencePullPolicy = os.environ.get("JOBSEQUENCE_PULLPOLICY")

    configMapName = parent["metadata"]["name"]
    serviceAccountName = parent["metadata"]["name"]
    cronJobName = parent["metadata"]["name"]
    namespace = parent["metadata"]["namespace"]
    clusterRoleBinding = parent["metadata"]["namespace"] + "-" + serviceAccountName

    jobs = [
      {
        "restartPolicy": "Never",
        "serviceAccountName": serviceAccountName,
        "containers": [
          {
            "name": "runner",
            "imagePullPolicy": kentledgePullPolicy,
            "image": kentledgeImage,
            "args": ["python", "backup.py"]
          }
        ]
      }
    ]

    jobConfigs = {}
    i = 0
    for job in jobs:
      jobConfigs["job-" + str(i) + ".yaml"] = json.dumps({"spec": {"template": {"spec": job}}})
      i = i + 1

    desired_status = {
      "clusterrolebindings": len(children["ClusterRoleBinding.rbac.authorization.k8s.io/v1"]),
      "serviceaccounts": len(children["ServiceAccount.v1"]),
      "configmaps": len(children["ConfigMap.v1"]),
      "cronjobs": len(children["CronJob.batch/v1"]),
    }
    desired_resources = [
        {
          "apiVersion": "v1",
          "kind": "ServiceAccount",
          "metadata": {
            "name": serviceAccountName,
            "namespace": namespace
          },
          "automountServiceAccountToken": True
        },
        {
          "apiVersion": "rbac.authorization.k8s.io/v1",
          "kind": "ClusterRoleBinding",
          "metadata": {
            "name": clusterRoleBinding,
          },
          "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": clusterRole
          },
          "subjects": [
            {
              "kind": "ServiceAccount",
              "name": serviceAccountName,
              "namespace": namespace
            }
          ]
        },
        {
          "apiVersion": "batch/v1",
          "kind": "CronJob",
          "metadata": {
            "name": cronJobName,
            "namespace": namespace
          },
          "spec": {
            "schedule": parent["spec"]["schedule"],
            "jobTemplate": {
              "spec": {
                "backoffLimit": 1,
                "template": {
                  "spec": {
                    "serviceAccountName": serviceAccountName,
                    "volumes": [
                      {
                        "name": "jobs",
                        "configMap": {
                          "name": configMapName
                        }
                      }
                    ],
                    "containers": [
                      {
                        "name": "runner",
                        "imagePullPolicy": jobsequencePullPolicy,
                        "image": jobsequenceImage,
                        "volumeMounts": [
                          {
                            "name": "jobs",
                            "mountPath": "/jobs"
                          }
                        ]
                      }
                    ],
                    "restartPolicy": "Never"
                  }
                }
              }
            }
          }
        },
        {
          "apiVersion": "v1",
          "kind": "ConfigMap",
          "metadata": {
            "name": configMapName,
            "namespace": namespace
          },
          "data": jobConfigs
        }
    ]

    return {"status": desired_status, "children": desired_resources}

  def do_POST(self):
    observed = json.loads(self.rfile.read(int(self.headers.get("content-length"))))
    self.dump(observed)
    desired = self.sync(observed["parent"], observed["children"])
    self.dump(desired)

    self.send_response(200)
    self.send_header("Content-type", "application/json")
    self.end_headers()
    self.wfile.write(json.dumps(desired).encode())

  def do_GET(self):
    self.send_response(200)
    self.send_header("Content-type", "application/json")
    self.end_headers()
    self.wfile.write(json.dumps({"status": "ok"}).encode())

print("Listen on port 8080")
HTTPServer(("", 8080), Controller).serve_forever()