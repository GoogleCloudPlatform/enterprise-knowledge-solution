# Access control for different user persona

This document describes how different users will interact with the Enterprise Knowledge Solution and how you can create groups and IAM roles to enable least privilege access.

## User persona for this solution

Different users of EKS require different levels of access, depending on how they need to interact with the application to do their job. We define those jobs-to-be-done as “persona”, and map each persona to IAM roles and groups that enable the necessary access.

If the persona is a team, we recommend creating a group for all the members of that team and applying IAM roles to that group. We do not recommend granting IAM roles to individual users, as this can become difficult to manage and audit at scale. If the persona is part of an automated process such as a deployment pipeline, we recommend using a service account.

The persona are as follows:

| Persona      | Job-to-be-done                                                                                                                                                                                    | Additional Considerations                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | IAM roles                                                                                                 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Deployer** | Create and modify all the Infrastructure-as-Code (IaC) resources defined in this repository.                                                                                                      | The deployment guide includes automation to create a service account (`deployer@$PROJECT_ID.iam.gserviceaccount.com`) with the minimum set of IAM roles to deploy all the IaC resources. If you’re following the deployment guide, no further work is required to configure the deployer roles. If you want users to have                                                                                                                                                                                                                                 | [persona_roles_deployer.txt](sample-deployments/composer-orchestrated-process/persona_roles_deployer.txt) |
| **Uploader** | upload documents to EKS.                                                                                                                                                                          | The uploader might be a service account in an automated process to ingest documents from a source system, or a group of users responsible for curating the content in EKS. The uploader should take care not to expose sensitive data to the end-users of EKS (the “Reader” persona) if they are not intended to access that data, because all uploaded documents will be available to all Readers. You should not grant uploader privileges broadly to users who might add arbitrary documents unrelated to your business use case.                      | [persona_roles_uploader.txt](sample-deployments/composer-orchestrated-process/persona_roles_uploader.txt) |
| **Operator** | responsible for day-to-day management of the pipelines, including running airflow jobs, inspecting rejected documents, validating that labels are applied correctly, and general troubleshooting. | The operator has read-only access to the underlying infrastructure services of EKS, including view access to all ingested data. The operator can also access the Airflow UI to trigger workflows. We recommend that any changes to infrastructure are made through the IaC pipeline and that individual users cannot modify infrastructure directly. However, depending on your ways of working, if the team handling the operator persona should be able to modify infrastructure directly, you might also grant them the roles of the Deployer persona. | [persona_roles_operator.txt](sample-deployments/composer-orchestrated-process/persona_roles_operator.txt) |
| **Reader**   | the end-users who access the EKS web app to query and view documents.                                                                                                                             | Readers need to interact with the Web-UI, but don’t need access to the underlying Google Cloud services.                                                                                                                                                                                                                                                                                                                                                                                                                                                  | [persona_roles_reader.txt](sample-deployments/composer-orchestrated-process/persona_roles_reader.txt)     |

Depending on your operations and team structure, a single team might be responsible for multiple personas. For example, if you have an application team that is responsible for all aspects of creating and managing EKS, you could give the combined roles of the deployer, uploader, and operator persona to this team. Or, if you have separate teams responsible for deploying infrastructure vs operating the infrastructure, you might grant the roles of each persona to different teams.

## Implement least privilege access for each persona

To implement the necessary roles for each persona, do the following:

Create groups or create a service account for each persona
Set the following environment variables, using the format `group:$GROUP_ID@example.com` for groups or `serviceAccount:$SERVICE_ACCOUNT_EMAIL_ID` for service accounts.

```bash
export OPERATOR=group:eks-operators@example.com
export UPLOADER=group:eks-uploaders@example.com
export READER=group:eks-readers-1@example.com
```

Ask an administrator (or someone with the role Project IAM Admin) to run the following script, which grants the bundle of roles for each persona to the relevant principal:

```bash
cd <PATH_TO_REPOSITORY>/sample_deployments/composer-orchestrated_process
scripts/grant_persona_roles.sh
```
