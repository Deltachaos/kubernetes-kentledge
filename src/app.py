from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import base64
import yaml
from re import L
import kubernetes
from io import StringIO
import os
import re
import pprint

class Controller(BaseHTTPRequestHandler):
  def dump(self, obj):
    self.log_message("%s", , "this is a test")
    self.log_message("%s", pprint.pformat(obj, indent=4))

  def sync(self, parent, children):

    serviceAccountName = "kentledge" # TODO change

    desired_status = {
      "configmaps": len(children["ConfigMap.v1"]),
      "cronjobs": len(children["CronJob.batch/v1"]),
    }
    desired_resources = [
        {
          "apiVersion": "v1",
          "kind": "ConfigMap",
          "metadata": {
            "name": parent["metadata"]["name"],
            "namespace": parent["metadata"]["namespace"]
          },
          "data": {
            "job1.yaml": "spec:\n  template:\n    spec:\n      restartPolicy: Never\n      containers:\n        - name: sleep-container\n          image: busybox\n          command: [\"sleep\", \"10\"]\n",
            "job2.yaml": "spec:\n  template:\n    spec:\n      restartPolicy: Never\n      containers:\n        - name: sleep-container\n          image: busybox\n          command: [\"sleep\", \"20\"]\n"
          }
        },
        {
          "apiVersion": "batch/v1",
          "kind": "CronJob",
          "metadata": {
            "name": parent["metadata"]["name"],
            "namespace": parent["metadata"]["namespace"]
          },
          "spec": {
            "schedule": parent["spec"]["schedule"],
            "jobTemplate": {
              "spec": {
                "template": {
                  "spec": {
                    "serviceAccountName": serviceAccountName,
                    "volumes": [
                      {
                        "name": "jobs",
                        "configMap": {
                          "name": parent["metadata"]["name"]
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
        }
    ]

    return {"status": desired_status, "attachments": desired_resources}

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