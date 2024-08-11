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
  def matchesFilter(self, cluster, namespace):
    namespaceFilter = json.loads(os.environ['NAMESPACES'])

    for clusterFilter in namespaceFilter:
        patternCluster = re.compile(clusterFilter["clusterName"])
        if patternCluster.match(cluster):
            for filter in clusterFilter["namespaces"]:
                patternNamespace = re.compile(filter)
                if patternNamespace.match(namespace):
                    return True

            return False

    return False

  def sync(self, parent, children):
    desired_status = {
      "backups": len(children["Backup.kentledge.deltachaos.de/v1alpha1"]),
      "configmaps": len(children["ConfigMap.v1"]),
    }
    desired_resources = []

    return {"status": desired_status, "attachments": desired_resources}

  def do_POST(self):
    observed = json.loads(self.rfile.read(int(self.headers.get("content-length"))))
    print(observed)
    desired = self.sync(observed["object"], observed["attachments"])
    print("desired")
    print(desired)

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