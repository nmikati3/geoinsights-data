# Deployment

GeoInsights runs as scheduled **Google Cloud Run Jobs**. The pipeline, the source-enrichment job, and the cross-domain join job each ship as their own container image (built from the `Dockerfile` in the respective subfolder under `geoinsights_data/`).

Replace the placeholders below with your own values:

- `<project-id>` — your GCP project ID
- `<region>` — e.g. `us-central1`, `europe-west9`
- `<registry>` — your Artifact Registry repository name
- `<image>` — the image name you choose

## 1. Artifact Registry

- Open **Artifact Registry → Create Repository**.
- Choose a name, select **Docker** as the format, and pick the region closest to you.
- Open the repository → **Setup Instructions**, and run the suggested `gcloud auth configure-docker` command, for example:

```bash
gcloud auth configure-docker <region>-docker.pkg.dev
```

- Build and push an image:

```bash
docker buildx build --platform linux/amd64 \
  -t <region>-docker.pkg.dev/<project-id>/<registry>/<image>:latest .
```

```bash
docker push <region>-docker.pkg.dev/<project-id>/<registry>/<image>:latest
```

- After pushing, check the image for vulnerabilities in Artifact Registry and remediate as needed.

## 2. Service Accounts (IAM)

Each Cloud Run Job should use its own dedicated service account (not the default one).

- **IAM → Service Accounts → Create Service Account.**
- Grant it access to the resources it needs (Cloud Storage, BigQuery, and — if you use Secret Manager for the OpenAI key — the **Secret Manager Secret Accessor** role).

## 3. Cloud Run Jobs

- **Cloud Run → Jobs → Create Job.**
- Point it at the container image you pushed.
- Set the **number of tasks**:
  - The main `pipeline` image expects **5 parallel tasks** (one per domain), routed via the `CLOUD_RUN_TASK_INDEX` environment variable (`0`=cyber, `1`=military aid, `2`=military offensive, `3`=sanctions, `4`=summits).
- Set the required environment variables / secrets (see the "Configuration" section of the README).
- Create the job, then add a **Cloud Scheduler trigger** under **Triggers** using the service account from step 2.

## Building from a specific Dockerfile (multiple images)

The repo contains multiple Dockerfiles in subfolders. To build a specific one and push it, use `-f`:

```bash
docker buildx build --platform linux/amd64 \
  -f geoinsights_data/<subfolder>/Dockerfile \
  -t <region>-docker.pkg.dev/<project-id>/<registry>/<image>:latest --push .
```

For example, to build the cross-domain join job:

```bash
docker buildx build --platform linux/amd64 \
  -f geoinsights_data/join_datasets/Dockerfile \
  -t <region>-docker.pkg.dev/<project-id>/pipeline/join_datasets:latest --push .
```

Helpful references:

- [https://cloud.google.com/run/docs/create-jobs](https://cloud.google.com/run/docs/create-jobs)
- [https://cloud.google.com/run/docs/execute/jobs-on-schedule](https://cloud.google.com/run/docs/execute/jobs-on-schedule)

