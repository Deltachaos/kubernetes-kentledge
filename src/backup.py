import time

print("hallo test")
time.sleep(3)
print(os.environ.get('JOB_CONFIGMAP'))
print(os.environ.get('JOB_NAME'))
print("hallo test ende")
time.sleep(10)
