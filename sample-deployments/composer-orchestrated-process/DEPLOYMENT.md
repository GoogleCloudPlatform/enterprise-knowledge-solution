# Deployment Guide
This guide provides step-by-step instructions on how to deploy the `Document Process and Understanding with Composer` sample on Google Cloud using Terraform.

## Prerequisites
To deploy this example you need:
- A [Google Cloud project](https://cloud.google.com/docs/overview#projects) with billing enabled.
- An account with the [Project Owner role](https://cloud.google.com/iam/docs/understanding-roles#resource-manager-roles) on the project. This grants the necessary permissions to create and manage resources.
- An account with the [Organization Policy Admin](https://cloud.google.com/resource-manager/docs/organization-policy/creating-managing-policies) role assigned within the organization, which is required to modify the following organization policies:
    * `compute.vmExternalIpAccess`
    * `compute.requireShieldedVm`
    * `iam.allowedPolicyMemberDomains`

    These modifications enable public IP access for the Web-UI interface while securing it through Identity Aware Proxy (IAP). If policy adjustments are not possible, you can opt to exclude the Web-UI component during deployment by setting the Terraform variable `deploy_ui` to `false`. Alternatively, you can deploy the Web-UI locally by referring to the instructions in the [Deploy Locally](../../components/webui/README.md#deploy-locally) section.

## Deploying the Sample
1. Open [Cloud Shell](https://console.cloud.google.com/cloudshell)
1. Clone this repository
1. Navigate to the Sample Directory:

    ```sh
    cd <YOUR_REPOSITORY>/sample-deployments/composer-orchestrated-process
    ```
    Where `<YOUR_REPOSITORY>` is the path to the directory where you cloned this repository.

1. Set environment variable: `PROJECT_ID`

    ```sh
    export PROJECT_ID="<your Google Cloud project id>"
    ```
1. Run the following script to setup your environment and your cloud project for running terraform:

    ```sh
    scripts/pre_tf_setup.sh
    ```
1. Initialize Terraform:

    ```sh
    terraform init
    ```
1. Create a terraform.tfvars file if it does not exist. Initialize the following Terraform variables in terraform.tfvars file:

    ```hcl
    project_id                  = # Your Google Cloud project ID.
    region                      = # The desired region for deploying resources (e.g., "us-central1", "europe-west1").
    vertex_ai_data_store_region = # The region for your Agent Builder Data Store, the possible values are ("global", "us", or "eu"). Choose a region the is align with you overal region of choice to avoid cross regional traffic.
    iap_admin_account           = # Account used for manage Oath brand and IAP
    iap_access_domains          = # List of domains granted for IAP access to the web-ui (e.g., ["domain:google.com","domain:example.com"])
    deploy_ui                   = # Toggler for the Web-UI component, boolean value true or false. If the scripts/pre_tf_setup.sh failed to set the required org-policies set this variable to false.
    webui_service_name          = # Name of the web-ui service in App engine. If you don't provide a value for this variable it will set to "default".
    ```
1. Review the proposed changes, and apply them:

    ```sh
    terraform apply
    ```
    The provisioning process may take about 30 minutes to complete.

## Updates
If you update the source code or pull the latest changes from the repository, re-run the following command to apply the changes to your deployed environment:

```sh
terraform apply
```

## Next steps
Follow the [Usage Guide](USE.md)