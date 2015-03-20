# Configuration server

Stores and imports config files from repositories, such as Gitiles.
Provides read-only access to config files and encapsulates their location.
Stores a registry of projects that use LUCI services.

## Quick examples

### Service config example
Auth service admins keep config files (client id whitelist, group import from
externa sources) as files in Gitiles. Config server is configured to import them
to `services/auth` config set. Auth service uses config component to
access its own configs. As a result, no need to implement API or UI in Auth
services for config reading/writing, no need to implement change history, config
ACLs or config rollback. Gitiles functionality is reused for that.

### Project config example
Project chromium is a tenant of Swarming service. Swarming is
chromum-independent therefore it does not contain configuration for chromium,
but chromium needs to supply its config to swarming. Chromium configs can be
stored in chromium repository and be imported into `projects/chromium` config
set. `projects.cfg` in `services/luci-config` config set contains a list of
projects served by LUCI services. For each project, Swarming uses luci-config
component to read swarming config from `projects/<project id>` config set.

## Terminology

* **service**: project-independent (in particular, chromium-independent)
  multi-tenant reusable software. Examples: swarming, isolate, auth.
- **project**: a tenant of a service. Examples: chromium, v8, skia.
- **tree**: a tree of files, belonging to a project. In Git case, it is
  a tuple (repository_url, branch_name).
- **config set**: a versioned collection of config files. Config sets have
  names, for example: `services/chrome-infra-auth`, `projects/chromium`,
  `projects/chromium/trees/master`. Config sets encapsulate location of files.
  Config service API accepts config sets instead of repository URLs.
 `services/luci-config:projects.cfg` means `projects.cfg` file in
 `services/luci-config` config set.

## Types of configs

There are two types of configs:

1. Service configs. A service may have a global project-independent config.
   Example: auth service has a whiltelist of oauth2 client ids.
   These configs are generally not interesting to project maintainers.

  Service configs live in `services/<service_id>` config sets, where
  `service_id` is an GAE app id.
  Examples: `services/luci-config`, `services/chrome-infra-auth`.
  A service typically reads config files in its own config set.

  `services/<service_id>` is always accessible to <service-id>.appspot.com.

  `services/luci-config:projects.cfg` is a project registry. It contains
  unique project ids (chromium, v8, skia) and location of project configs.
  This list is available through get_projects() API. This is how projects are
  discovered by services.

2. Project configs. Project-wide branch-independent configs for services.
   This is what a project as a tenant tells a service about itself. Examples:

  * project metadata: project name, project description, mailing list,
    owner email, team auth group, wiki link, etc.
  * list of repositories and branches that services should handle.
  * cron jobs: when and what tasks to run.

  Project configs live in `projects/<project_id>` config set. Services discover
  projects through `get_projects()` and request a config from
  `projects/<project_id>` config set. For instance, cron service reads
  `projects/<project_id>:cron.cfg` for each project in the registry.

3. Tree configs. These are repository/branch-specific configs in a project.
   Examples:

  * list of quest definitions to be scheduled when a CL for this tree is queued
    for committing.
  * list of builders that can close the tree if failed.
  * Code review info: type (rietveld vs gerrit), URL and codereview-specific
    details.

  Tree configs live in `projects/<project_id>/tree/<tree_name>` config set.

## GAE component
config component can be used by a GAE app to read configs.

## Config import
Configs are continuously imported from external sources to the datastore by
config server backend. [[|Read more:-config-import]].
