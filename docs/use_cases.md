# Use Cases: Authentication (authN) and high-level Authorization (authZ).

Representative use cases to drive discussion of distributed multi-tenant authorization needed for multi-institution pan-cancer research.

## User Story: Basic separation of individual from owned resources
BigUniversity has an existing Cancer project, and wants to allow 2 different teams to access and manage their resources. Each team has two dedicated people, and there are two people that float across both teams. They want to set up all the users and groups into Keystone so that:

UniversityA user A1, A2, Z1, and Z2 can all access and manipulate resources owned by UniversityA
UniversityB user B1, B2, Z1, and Z2 can all access and manipulate resources owned by UniversityB

Resources in question are meta data of patient, samples and their associated files as well as provenance data about experiments and derivative files.

## User Story: Service Catalog
BigUniversity wants to provide a service catalog to each of the users listed above with their relevant API endpoints created to match their identity stored in Keystone. For example, the user Jill wants to log into the DMS using her credentials (stored in keystone), and be able to get the service URI endpoints to use in command line workflows or GUI clients.


## User Story: Basic RBAC (role based access controls)
BigUniversity has an system deployment, being used by 2 development teams and managed by a separate operations team. They want to set up the operations team to be able to manipulate all resources within the deployment, and limit the development team's users to only manipulating their own meta data and files.

ROLE - A group that a user can be in, which gives them privileges - combination of user+project from identity above
ACTION - Doing something - this is specific to a service
CAPABILITY - An action that's been granted to a role (role+action)

## User Story: SSO
All users within BigUniversity need to use their existing enterprise credentials (Active Directory). Likewise, their partner at UniversityA uses enterprise credentials (LDAP).  The UniversityB partner uses google docs.  All users do not want new credentials for the system.  Management at all partners insist that existing provisioning of users(add, move and changes) shared authentication with their existing enterprise systems

## User story: Logon and Query
Alice arrives at work and logs into his desktop with his corporate username/password, and sees an email that the private cloud is now available. She clicks the link and it takes her to a sign-on page. She enters her corporate username/password and it lets her in. After exploring the features, she is ready to start using the system.  She immediately starts to query for her desired cohort.

## User story: Workflow
Alice decides to launch a workflow, using resources she found in the DMS. In the workflow, when resources are registered with the object store, if she wishes to associate them with metadata, she adds that parameter to the storage call.  e.g.
```
swift upload  container1  /tmp/FILE1  -H "content-type:text/plain" -H "X-Object-Meta-sampleId:SAMPLE1"
```
Metadata tags can include individual, sample, specimen, aliquot, analyte, slide, etc. depending on project's needs.

If no meta tags are included, the file is associated with the project.   (A generic `system` project exists for system files).   

## User story: Adding users to the DMS instance for BigUniversity
Jill is an administrator for the system at BigUniversity. She's been asked to bulk load a division of people into a proof of concept/prototype setup (Identity is being backed by DB). In doing so, she has a list of usernames that should all be added, to be broken up into groups of multiple projects by a later task.

Allow Jill to upload the list and bulk create users without identifying projects for those users a priori

## User story: Adding users to an DMS instance from BigUniversity's directory
Jill is an administrator for the system at BigUniversity. She's been asked to enable Dept A, B, C, and D for the OpenStack environment. All the members of Division X can be determined by an LDAP query against BigUniversity's directory containing a list of departments. All members of will need to log in with their corporate credentials. Jill doesn't have any update authority to the corporate directory.


## User Story: extension to support multiple openstack clusters with a single instance of Keystone
BigUniversity has partnered with IvyUniversity and wants to run two separate system clusters with a single instance of AA. IvyUniversity insists on complete autonomy and wants to run it's own instance of AA on its premises under its control.  They participate in the pan cancer study with BigUniversity, UniversityA and UniversityB.
IvyUniversity user I1, I2, Z1, and Z2 can all access and manipulate resources owned by IvyUniversity



#### AA (Authentication Authorization) Data model constructs:
```
The key constructs there are Users, Projects, and Roles to link the two.
Tokens are authenticated by user credentials through Keystone, and include metadata that is shared with the service to make permission choices.
```

#### Technical Assumptions:
```
AA management layer and VMs have access to corporate AD/LDAP
corporation has an existing AD/LDAP that will need to be integrated
AA only need (minimal) read access to LDAP/AD
AA will:
* check if the username/password is correct
* list all tenants for a user (groups the user is a member of)
* list all roles for the user/tenant (for cloud permissions)
* pulls tenant information from metadata
* only users in that project/group can access project's resources or metadata
```
