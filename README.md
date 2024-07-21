# Kentledge

Kentledge is a Kubernetes operator designed to facilitate the backup and restore of persistent volumes (PVs) in Kubernetes, along with associated MySQL databases and S3 buckets. This project aims to provide a comprehensive backup solution that handles various types of storage efficiently, ensuring data integrity and availability.

## Features

- Backup and restore of PersistentVolumes (PVs)
- Backup and restore of MySQL databases
- Backup and restore of S3 buckets
- Support for ReadWriteOnce (RWO) and ReadWriteMany (RWX) volume modes
- Scheduling of backups using custom resources
- Retention policies for backup data
- Integration with Borg backup server

## Warning

**This project is currently under heavy development. The features described in this README are planned to be supported, but are not currently implemented.**

## Todo List

- [x] Write README with planned features :D
- [] Support basic backup functionality
- [] Support ReadWriteMany volumes
- [] Support ReadWriteOnce volumes
- [] Support MySQL backup
- [] Support S3 backup

## Installation

Kentledge is installed into your Kubernetes cluster via a Helm chart located in the `helm` subdirectory.

1. **Add the Kentledge Helm repository:**
    ```sh
    git clone https://github.com/Deltachaos/kubernetes-kentledge.git
    cd kubernetes-kentledge/helm
    ```

2. **Install the Kentledge Helm chart:**
    ```sh
    helm install kentledge .
    ```

## Custom Resource Definitions

### Backup CRD

The `Backup` CRD defines the backup schedule and targets. Here's an example manifest:

```yaml
apiVersion: kentledge.io/v1alpha1
kind: Backup
metadata:
  name: daily-backup
spec:
  schedule: "0 2 * * *"  # Cron schedule for daily backups at 2 AM
  clusterBackupStore:
    name: default-store
  targets:
    - type: mysql
      url: mysql://user:password@mysql-host:3306/database
    - type: s3
      url: s3://access-key:secret-key@s3-bucket-name
    - type: pv
      matchLabel:
        app: important-app
```

### ClusterBackupStore CRD

The `ClusterBackupStore` CRD defines the backup storage configuration, including credentials and retention policies. Here's an example manifest:

```yaml
apiVersion: kentledge.io/v1alpha1
kind: ClusterBackupStore
metadata:
  name: default-store
spec:
  borgBackupServer:
    url: borg://backup-server:repo
    credentials:
      username: borg-user
      password: borg-password
  storageClass: "default"  # Storage class for temporary volumes, defaults to emptydir
  retentionPolicy:
    keepDaily: 7
    keepWeekly: 4
    keepMonthly: 6
```

## Backup Process

The Kentledge operator creates a CronJob resource for each `Backup` custom resource. To handle ReadWriteOnce volumes, it uses a DaemonSet to mount the `/var/lib/kubelet` directories. During a backup job, the operator mounts ReadWriteOnce volumes via SSHFS if a pod using the volume is already running. Otherwise, it uses the Kubernetes native method, temporarily preventing other pods from accessing the volume. ReadWriteMany volumes are always mounted natively by Kubernetes.

## Recommendations

- **Use ReadWriteMany volumes**: While Kentledge supports both ReadWriteOnce and ReadWriteMany volumes, it is recommended to use ReadWriteMany volumes for more stable operation.
- **Comprehensive Backups**: Kentledge ensures that all targets defined in the `Backup` resource are backed up in a single run. This holistic approach guarantees consistency across different storage types.

## Contributing

We welcome contributions to Kentledge!

## License

Kentledge is licensed under the [AGPL License](https://github.com/Deltachaos/kubernetes-kentledge/blob/main/LICENSE).

## Contact

For any inquiries or issues, please open an issue on our [GitHub repository](https://github.com/Deltachaos/kubernetes-kentledge) or contact me via email at mr@deltachaos.de.
