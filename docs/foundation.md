# Deploying Solutions to an enterprise-ready foundation

The technical prerequisites for the Enterprise Knowledge Solution are self-contained in the deployment guide of this repository. However, in large and complex enterprise environments, you might expect additional controls that go beyond the scope of this repository. For example, you might expect to sync users from your existing identity provider to Google Cloud, to enforce preventative controls against insecure cloud resource configurations, or export audit logs for all projects to an aggregated destination.

We recommend addressing this broad set of requirements through designing a cloud foundation (sometimes called a "landing zone"). A cloud foundation is the baseline of resources, configurations, and capabilities that enable companies to adopt Google Cloud for their business needs. A well-designed foundation enables consistent governance, security controls, scale, visibility, and access to shared services across all workloads in your Google Cloud environment.

Google Cloud provides guidance on how to design and implement these controls through the [Enterprise Foundation Blueprint](https://cloud.google.com/architecture/security-foundations). You can use the enterprise foundation blueprint in one of two days:

- **New customers to GCP**: quickly deploy a foundation with premade assets, to reduce the time and effort spent on planning and building the foundation. This helps accelerate the time to your first meaningful workload that provides business value.
- **Existing customers on GCP**: assess your existing environment against the recommended foundation capabilities. Where you have gaps, iterate on your existing foundation to improve controls and governance for your workloads.

Both approaches can help identify the set of capabilities that help you deploy and use the Enterprise Knowledge Solution in a way that meets enterprise best practices.

## Enterprise security controls

The foundation blueprint addresses a range of enterprise requirements, including common platform-wide security controls that go beyond the scope of any individual workload.
The following capabilities are common security controls you might expect to meet before deploying and using this Solution:

| Topic | Foundation Capability |
| --- | --- |
| [Sign up for a Cloud Customer Care plan.](https://cloud.google.com/architecture/security-foundations/summary#bringing-it) |    You have established a support contract to help with troubleshooting or incident response. |
| [External identity provider as the source of truth](https://cloud.google.com/architecture/security-foundations/authentication-authorization#external_identity_provider_as_the_source_of_truth) | You have established an identity provider to manage user account identities and SSO from a source of truth. This includes resolving issues with unmanaged consumer accounts, enforcing multi-factor authentication, and configuring other administrative controls on Cloud Identity. |
| [Super admin accounts](https://cloud.google.com/architecture/security-foundations/authentication-authorization#super_admin_accounts) | You have followed best practices for managing Super Administrator accounts |
| [Groups for access control](https://cloud.google.com/architecture/security-foundations/authentication-authorization#groups_for_access_control) | You have established groups used for access control of related teams and job functions. This includes groups for broad across the platform (persona that manage org-wide and folder-wide settings) as well as groups for a given workload (persona who develop and use that workload) |
| [Projects](https://cloud.google.com/architecture/security-foundations/organization-structure#projects) | You have existing automation or process to consistently deploy workload projects into the appropriate environment folder and with project-specific attributes  like labels, tags, Essential Contacts, etc |
| [Hybrid connectivity between an on-premises environment and Google Cloud](https://cloud.google.com/architecture/security-foundations/networking#hybrid-connectivity) | You have established private network paths between your onprem environment and GCP |
| [Centralized logging for security and audit](https://cloud.google.com/architecture/security-foundations/detective-controls#centralized-logging) | You have established a centralized logging architecture to aggregate the[ recommended set of Admin Activity logs](https://cloud.google.com/architecture/security-foundations/detective-controls#centralized-logging) from all projects into a single location. This includes enablement steps for a few types of security logs that are not enabled by default, such as Access Transparency logs. |
| [Threat monitoring with Security Command Center](https://cloud.google.com/architecture/security-foundations/detective-controls#threat-monitoring) | You have enabled Security Command Center to automatically detect threats, vulnerabilities, and misconfigurations in your Google Cloud resources |
| [Organization policy constraints](https://cloud.google.com/architecture/security-foundations/preventative-controls#organization-policy) | You have established a basic set of org policies as guardrails against common misconfigurations. |
| [Protect your resources with VPC Service Controls](https://cloud.google.com/architecture/security-foundations/operation-best-practices#protect-resources) | You have a strategy for how to define service control perimeters to mitigate data exfiltration. |
| [Restrict access to the google cloud console](https://cloud.google.com/architecture/security-foundations/summary#additional_administrative_controls_for_customers_with_sensitive_workloads) | You have a strategy for how to control trusted developer devices used to access Google Cloud services. |
| [Manage encryption keys with Cloud Key Management Service](https://cloud.google.com/architecture/security-foundations/operation-best-practices#manage-encryption) | You have a strategy for managing encryption keys, if required for regulatory or compliance reasons. |
| [Enable Assured Workloads](https://cloud.google.com/architecture/security-foundations/summary#additional_administrative_controls_for_customers_with_sensitive_workloads) | You have configured additional contractual and technical controls based on regional sovereignty requirements |