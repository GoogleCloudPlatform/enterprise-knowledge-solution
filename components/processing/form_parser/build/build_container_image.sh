#!/bin/bash  
# Bash script

if ! gcloud artifacts repositories describe dpu-form-parser-repo --location=$REGION; then 
    echo "repo not found"
    gcloud artifacts repositories create dpu-form-parser-repo --repository-format=docker --location=$REGION --description="repo build with cmd" --async
else
    echo "repo found"
fi

gcloud auth configure-docker us-central1-docker.pkg.dev
gcloud builds submit ../../components/processing/form_parser/src --pack image=$REGION-docker.pkg.dev/$PROJECT_ID/dpu-form-parser-repo/dpu-form-processor:latest --project $PROJECT_ID