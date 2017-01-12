# A Production OpenStack

On Wed Sep 14, Marion wrote:

> [Steve] has asked that we work with Kyle Ellrott to come up with
> what it would take to move the Exastack pilot to an actual
> production service.

What follows is an expansion of an ACC-internal document I wrote a
couple months ago. It's not as polished as I'd like, but I think
you'll get the gist of the major issues I think need to be addressed.
Some will impact budget, others our workflows. Very few are insignificant
enough to be ignored and a couple may lead us to a complete
re-installation of our infrastructure.

## The BIG questions

***Goals***

Communication between users of Exastack and ACC has not been clear and
consistent. One of the goals of the pilot is to provide users and ACC
alike answers to several questions:

* Which OpenStack modules are necessary, optional, and unnecessary?
* Where is redundancy necessary?
* What sort of maintenance and upgrade schedule is optimal?
* What trade-offs are best when it comes to CPU, RAM, and disk -- within our budget?
* What's the best network architecture -- within our budget?
* What auxiliary services (block storage, authentication) are needed for Exastack to meet user needs?
* Who needs what privileges, given the OHSU standard of least-privilege necessary?

Other questions have arisen since the pilot started, particularly
how best to interface with the newly expanded ITG Security Team
(SECE). This issue will throw lots of wrenches in our workflows.

***Platform***

The pilot was setup with CentOS 7 using [RDO packstack](https://www.rdoproject.org/install/quickstart/), which was relatively quick, reproducible, and used a platform with which I'm very familiar. RDO isn't the only game in town. In no particular order, there's also

* [Ubuntu Autopilot](https://www.ubuntu.com/cloud/openstack/autopilot)
* [Mirantis](https://www.mirantis.com/software/openstack/)
* [Red Hat OpenStack Platform](https://www.redhat.com/en/technologies/linux-platforms/openstack-platform)
* [From scratch](http://docs.openstack.org/project-install-guide/newton/)

Some of these cost nothing; others have a maintenance fee. Some
scale more easily. Some offer customizations. The thing is, we
haven't done anything even resembling a comparison evaluation.

### Sub-questions with budgetary impact

* compute nodes
  * how many nodes to start?
  * ideal RAM:core ratio?
  * how much local disk per node and how redundant need it be?
  * cost per node?
* control nodes
  * do we require redundancy here?
  * if so, is three (the minimum required for redundancy) enough?
* shared storage
  * worth putting on separate network?
  * size?
  * use case (object store? block storage? image archive?)
  * one big storage server or more of a distributed model?
  * do we need to support live migration of VMs?
* maintenance
  * bringing another ACC staff member up to speed
  * ongoing administrative requests
  * periodic version upgrades
  * training and documentation
* backups
  * what to backup, if anything?
  * retention policy
  * to what extent is a disaster-recovery plan needed?

### Sub-questions with little or no budgetary impact

* procedure to upgrade OpenStack software
  * do we devote hardware to alpha/beta testing next-gen releases?
* uptime requirements
* data security
  * how will PHI be identified and access audited?
  * how will "business secrets" (for lack of a better term) be identified and access audited?
  * how will VM images be vetted for use?
  * how will deployed applications be vetted for use?
  * how will we identify and remove obsolete VMs, applications, and users?
* network architecture
  * default firewall rules?
  * how will changes to firewall be managed?
  * what IPv4 space to deploy?
  * internal IPv6 allowed?
  * process for exposing an OpenStack VM to public internet?
  * process to assign DNS names to VMs?
* VM and application lifecycle
* monitoring
  * ACC is mostly an 8x5 shop. What will happen if 24x7 demands present themselves?
* authentication
  * how best to authenticate? AD? ACC LDAP? Local DB?
* authorization
  * ACLs need to be crafted per project and per service
  * e.g., who can spin up vms? reserve routed network space? alter host firewalling? allocate storage? create projects? authorize new users?
* billing model?
  * can a certain project "buy" a compute node and have exclusive rights to it?
* storage
  * will VMs be able to access lustre?
* SSL everywhere?
  * it will take time to learn how to protect some sorts of communications?

### Untested and unknown

What happens if

* the control node goes down?
* the network node goes down?
* the network itself goes down?
* a cinder or swift node loses a disk?

None of these scenarios has been tested.

