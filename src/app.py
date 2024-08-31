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

    configMapName = parent["metadata"]["name"]
    serviceAccountName = parent["metadata"]["name"]
    cronJobName = parent["metadata"]["name"]
    namespace = parent["metadata"]["namespace"]
    clusterRoleBinding = parent["metadata"]["namespace"] + "-" + serviceAccountName

    desired_status = {
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
          "data": {
            "automountServiceAccountToken": True
          }
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
            "backoffLimit": 1,
            "jobTemplate": {
              "spec": {
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
                        "imagePullPolicy": "Always",
                        "image": "ghcr.io/deltachaos/kubernetes-jobsequence:main",
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
          "data": {
            "job1.yaml": "spec:\n  template:\n    spec:\n      restartPolicy: Never\n      containers:\n        - name: sleep-container\n          image: busybox\n          command: [\"sleep\", \"10\"]\n",
            "job2.yaml": "spec:\n  template:\n    spec:\n      restartPolicy: Never\n      containers:\n        - name: sleep-container\n          image: busybox\n          command: [\"sleep\", \"20\"]\n"
          }
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