# Access control for different user persona

This document describes how different users will interact with the Enterprise Knowledge Solution and how you can create groups and IAM roles to enable least privilege access.

## User persona for this solution

Different users of EKS require different levels of access, depending on how they need to interact with the application to do their job. We define those jobs-to-be-done as “persona”, and map each persona to a bundle of IAM roles and groups that enable the necessary access.

If the persona is a team, we recommend creating a group for all the members of that team and applying IAM roles to that group. If the persona is part of an automated process such as a deployment pipeline, we recommend using a service account. We do not recommend granting IAM roles to individual users, as this can become difficult to manage and audit at scale.

The persona are as follows:

| Persona      | Job-to-be-done                                                                                                                                                                           | Additional Considerations                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | IAM roles                                                                                                 |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| **Deployer** | Create and modify all the Infrastructure-as-Code (IaC) resources defined in this repository                                                                                              | The deployment guide includes automation to create a service account (`deployer@$PROJECT_ID.iam.gserviceaccount.com`) with the minimum set of IAM roles to deploy all the IaC resources. If you’re following the deployment guide, no further work is required to configure the deployer roles. If you want users to have the privileges to modify resources directly outside of the deployment pipeline, you can additionally grant the bundle of Deployer roles to a group of users.                                                                                                                             | [persona_roles_DEPLOYER.txt](sample-deployments/composer-orchestrated-process/persona_roles_DEPLOYER.txt) |
| **Uploader** | upload documents to EKS                                                                                                                                                                  | The uploader might be a service account in an automated process to ingest documents from a source system, or a group of users responsible for curating the content in EKS. The uploader should take care not to expose sensitive data to the end users of EKS (the “Reader” persona) if they are not intended to access that data, because all uploaded documents will be available to all Readers. You should not grant Uploader privileges broadly to users who might add arbitrary documents unrelated to your business use case.                                                                               | [persona_roles_UPLOADER.txt](sample-deployments/composer-orchestrated-process/persona_roles_UPLOADER.txt) |
| **Operator** | Perform day-to-day management of the pipelines, including running airflow jobs, inspecting rejected documents, validating that labels are applied correctly, and general troubleshooting | The operator has read-only access to the underlying infrastructure services of EKS, including view access to all ingested data. The operator can also access the Airflow UI to trigger workflows. We recommend that any changes to infrastructure are made through the IaC pipeline and that individual users cannot modify infrastructure directly. However, depending on your ways of working, if the team handling the Operator persona should be able to modify infrastructure directly (outside of your deployment pipeline), you can additionally grant the roles of the Deployer persona to the same group. | [persona_roles_OPERATOR.txt](sample-deployments/composer-orchestrated-process/persona_roles_OPERATOR.txt) |
| **Reader**   | access the EKS web app as end user to query and view documents                                                                                                                           | Readers need to interact with the Web-UI and view documents, but don’t need access to other underlying Google Cloud services.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | [persona_roles_READER.txt](sample-deployments/composer-orchestrated-process/persona_roles_READER.txt)     |

Depending on your operations and team structure, a single team might be responsible for multiple personas. For example, if you have an application team that is responsible for all aspects of creating and managing EKS, you could give the combined roles of the Deployer, Uploader, and Operator persona to this team. Or, if you have separate teams responsible for deploying infrastructure and for operating the infrastructure, you might grant the roles of each persona to different teams.

## Implement least privilege access for each persona

To implement the necessary roles for each persona, do the following:

1. [Create groups](https://cloud.google.com/iam/docs/groups-in-cloud-console) or [create a service account](https://cloud.google.com/iam/docs/service-accounts-create) for each necessary persona.

1. Set one or more of the following environment variables with the identities for each persona, with the format `group:$GROUP_ID@example.com` for groups or `serviceAccount:$SERVICE_ACCOUNT_EMAIL_ID` for service accounts. Optionally, remove any persona variables that you will not use (for example, the default Deployer service account is already configured as part of deploying the terraform resources).

```bash
#export DEPLOYER="<YOUR_GROUP, like "group:eks-deployers@example.com">"
export OPERATOR="<YOUR_GROUP, like "group:eks-operators@example.com">"
export UPLOADER="<YOUR_GROUP, like "group:eks-uploaders@example.com">"
export READER="<YOUR_GROUP, like "group:eks-readers@example.com">"
```

1. Ask an administrator (or someone with the role Project IAM Admin) to run the following script, which grants the bundle of roles for each persona to the principal that you defined in the previous step:

```bash
cd <PATH_TO_REPOSITORY>/sample_deployments/composer-orchestrated_process
scripts/apply_persona_roles.sh
```
