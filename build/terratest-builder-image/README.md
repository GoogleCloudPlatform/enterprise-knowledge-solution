# How to use this image

The builder image used to run integration tests in this directory is created in an internal project. This page documents how to recreate and update the image.

1. Navigate to the `build/terratest-builder-image/` directory and run the following command:

```bash
gcloud builds submit . --project=$PROJECT_ID
```

1. Define a tag value for the new build, and ensure that `BUILDER_IMAGE_TAG` in [/build/int.cloudbuild.yaml](/build/int.cloudbuild.yaml) uses the correct tag value.

# derp
