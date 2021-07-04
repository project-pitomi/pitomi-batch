# pitomi-batch
Check https://github.com/project-pitomi/pitomi for project pitomi
#### Sample k8s manifests

##### secret.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: secret-pitomi-batch
  namespace: hitomi
type: Opaque
data:
  mongodb: <<mongodb connection string>>
  azureStorageAccountConnectionString: <<azure storage account connection string>>

```

`<<mongodb connection string>>` something like `"mongodb://~"`

`<<azure storage account connection string>>` something like `DefaultEndpointsProtocol=https;AccountName=blahblah;AccountKey=blahblah;EndpointSuffix=blahblah`  



\* all batch pods use same image.  ( Build it with Dockerfile😀 )

##### fetch_cronjob.yaml

```yaml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: fetch
  namespace: hitomi
spec:
  schedule: "*/30 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hitomi-fetch
            image: <<Image>>
            command: ["python"]
            args: ["-m", "src", "fetch", "100"]
            env:
            - name: PITOMI_MONGO_CONNECTION_STRING
              valueFrom:
                secretKeyRef:
                  name: secret-pitomi-batch
                  key: mongodb
            - name: PITOMI_AZURE_STORAGE_ACCOUNT_CONNECTION_STRING
              valueFrom:
                secretKeyRef:
                  name: secret-pitomi-batch
                  key: azureStorageAccountConnectionString
          restartPolicy: Never

```

`<<Image>>` name:tag of your image

fetch galleries from hitomi



##### classify_cronjob.yaml

```yaml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: classifier
  namespace: hitomi
spec:
  schedule: "*/1 * * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            app: classifier
        spec:
          containers:
          - name: classifier
            image: <<Image>>
            command: ["python"]
            args: ["-m", "src", "classify", "128"]
            env:
            - name: PITOMI_MONGO_CONNECTION_STRING
              valueFrom:
                secretKeyRef:
                  name: secret-pitomi-batch
                  key: mongodb
            - name: PITOMI_AZURE_STORAGE_ACCOUNT_CONNECTION_STRING
              valueFrom:
                secretKeyRef:
                  name: secret-pitomi-batch
                  key: azureStorageAccountConnectionString
          restartPolicy: Never

```

`<<Image>>` name:tag of your image

classify fetched galleries by artist, group, ...



##### webp_cronjob.yaml

```yaml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: webp-generator
  namespace: hitomi
spec:
  schedule: "*/1 * * * *"
  concurrencyPolicy: Forbid
  startingDeadlineSeconds: 10
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            app: webp-generator
        spec:
          containers:
          - name: webp-generator
            image: <<Image>>
            command: ["python"]
            args: ["-m", "src", "build_webp", "64"]
            resources:
              requests:
                cpu: "1"
                memory: "4Gi"
            env:
            - name: PITOMI_MONGO_CONNECTION_STRING
              valueFrom:
                secretKeyRef:
                  name: secret-pitomi-batch
                  key: mongodb
            - name: PITOMI_AZURE_STORAGE_ACCOUNT_CONNECTION_STRING
              valueFrom:
                secretKeyRef:
                  name: secret-pitomi-batch
                  key: azureStorageAccountConnectionString

          restartPolicy: Never

```

`<<Image>>` name:tag of your image

convert avif images into browsable image

