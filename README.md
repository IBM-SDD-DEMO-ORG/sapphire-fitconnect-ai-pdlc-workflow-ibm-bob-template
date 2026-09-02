# AI PDLC Workflow Sidekick for Brownfield Product Teams

## Table of Contents

- [What This Sidekick Does](#1-what-this-sidekick-does)
- [Team Roles (Recommended)](#2-team-roles-recommended)
- [One-Time Setup for a New Product Team](#3-one-time-setup-for-a-new-product-team)
  - [Step 1: Curate AGENTS.md with system context](#step-1-curate-agentsmd-with-system-context)
  - [Step 2: Configure global/local constitution source](#step-2-configure-globallocal-constitution-source)
  - [Step 3: Configure role mappings and approval policy](#step-3-configure-role-mappings-and-approval-policy)
  - [Step 4: Generate the effective constitution](#step-4-generate-the-effective-constitution)
  - [Step 5: Validate sidekick readiness](#step-5-validate-sidekick-readiness)
- [Brownfield Workspace Initialization](#4-brownfield-workspace-initialization)
- [Feature Introduction Steps](#feature-introduction-steps)
  - [Step 1: Specify](#step-1-specify)
  - [Step 2: Clarify](#step-2-clarify)
  - [Step 3: Plan](#step-3-plan)
  - [Step 4: Tasks](#step-4-tasks)
  - [Step 5: Implement](#step-5-implement)
  - [Step 5: Raise PRs](#step-5-raise-prs)

---

This repository is the sidekick orchestrator for product teams building features across one or more existing (brownfield) services.

It provides a governed Product Development Lifecycle using Spec-Kit based agents:

- `speckit.constitution`
- `speckit.specify`, `speckit.plan`, `speckit.tasks`, `speckit.analyze`, `speckit.implement`
- PR and approval gate agents

Use this README as the operating instructions for onboarding a new team and running feature delivery end-to-end.

## 1. What This Sidekick Does

In a brownfield setup, changes usually span multiple existing repos. This sidekick repo centralizes:

- Story-level specification, plan, tasks, and workflow state
- Governance via effective constitution
- Approval checkpoints by role
- Cross-repo orchestration with traceability from story to PRs

## 2. Team Roles (Recommended)

Configure role mappings in `settings.yaml`.

- Application Engineer (submitter): runs the workflow and drives implementation
- Product Owner: approves specification PR gate
- FDE/FDA: approves plan and tasks gates
- Architect: curates `AGENTS.md` and constitution constraints

Hard rules expected by this workflow:

- Approvals must be GitHub PR approvals (chat confirmation is not a gate)
- Submitter cannot self-approve their own gate
- Spec gate must pass before planning
- Plan/tasks gates must pass before implementation

## 3. One-Time Setup for a New Product Team

Follow these steps in order.

### Step 1: Curate AGENTS.md with system context

Update root `AGENTS.md` with:

- Repos: each codebase, role, stack
- Task routing by repo
- Data flow summary
- Cross-repo workflows
- Infrastructure constraints

Keep it concise but complete enough for an agent to infer impact boundaries.

### Step 2: Configure global/local constitution source

Update `settings.yaml` under:

- `constitution.global_source.mode`
- `constitution.global_source.path` (for local source), or GitHub source details

Common modes:

- `local`: pull global rules from a sibling directory (default in this repo)
- `github`: fetch global rules from a remote repo path
- `none`: local constitution only

### Step 3: Configure role mappings and approval policy

In `settings.yaml`, configure:

- `pdlc.submitter_role`
- `pdlc.approvals.spec/plan/tasks`
- `pdlc.roles.<role>.github_team` and/or `github_users`

At least one identity per active role should be set.

### Step 4: Generate the effective constitution

SDD Flow supports creation of constitution for 3 different scenarios:
1. Local constitution only: This is when you need rules specific for your product.
2. Global constitution only: This is when there are some organization wide (global) rules already available and you only want to use them for your product.
3. Local + Global: This is when you want to use global rules and then augment them with your local product specific rules.

For local constitution generation (needed for option 1 & 3), run the below in IBM Bob Chat. This is not needed for option 2:

```text
/speckit.constitution <your-tech-rules>
```

Expected outcome:

- local constitution is created/updated


Next, run the constitution resolution command. This is needed for all 3 scenarios.
```text
/constitution.resolve
```

Expected outcome:
- `.specify/runtime/effective-constitution.md` is produced

Do not start the workflow until effective constitution exists.

### Step 5: Validate sidekick readiness

Before first feature, confirm:

- `AGENTS.md` is filled for your product architecture
- `settings.yaml` contains valid role mappings
- `.specify/runtime/effective-constitution.md` exists


## 4. Brownfield Workspace Initialization

After the above steps are done, we have an instantiated sidekick reposity specific to the project. Now, create one parent folder and clone repos as siblings:

```text
<PRODUCT_HOME>/
	ai-pdlc-sidekick-template/   # this sidekick repo
	service-a/
	service-b/
	web-app/
	org-policy-files/           # optional global constitution source
```

Why this matters:

- The sidekick must reason over multiple sibling repos
- `AGENTS.md` and task routing map changes to the correct repo(s)


## Feature Introduction Steps

## Step 1: Specify

Get the JIRA story id for the feature you need to develop. With the JIRA story id, invoke the /speckit.specify command. 

`/speckit.specify DPDE-30`

> 

This step will fetch the JIRA story, identify the affected repositories and create the spec file. If you do not agree with the repo list and wish to change it, you can type the changes needed in the chat window. After it has created the spec file, it will push the changes to the github. It will also ask to run /speckit.clarify as a text task

## Step 2: Clarify

Next, run

`/speckit.clarify DPDE-30`

> 

Here, Bob will ask in case it needs any further clarification on the requirements. Once all questions are answered, it will raise a PR and return the PR number in the chat window.

> 

This PR has to be approved by product_owner before moving to the next step.

## Step 3: Plan

After the spec PR is approved, run

`/speckit.plan DPDE-30`

> 

Plan is a comparatively heavier task since it reads through the codebases and understands the code structure. This phase is responsible for creating contracts, making architectural decisions and creating a plan for the implementation. The artifacts generated from this phase needs to be reviewed explicitly and corrected via iterations of vibe if needed. If the artifacts created here are not properly reviewed and incorrect, implementation will not be grounded. This also goes via a PR approval process.

> 

Once the plan PR is approved, JIRA stories are created for each of the repositories and linked to th eoriginal story.

> 

## Step 4: Tasks

Next, run

`/speckit.tasks DPDE-30`

> 

Here, low level tasks are generated. After this is generated, run 

`/speckit.analyze DPDE-30`

> 

This will try to find out if there are any inconsistencies between the spec, plan and task. If if finds anything, it will correct. Otherwise, it will raise a PR for the tasks. Here also, we can vibe and make corrections to the plan if needed.

> 

After this, when we come back to the analyze screen in bob and update that PR has been approved, Bob will update the JIRA stories with the task details.

## Step 5: Implement

Now that the tasks are done, we need to run the implement command. This will create a new branch and start the implementation for each of the repos.

First, run the command

`/speckit.implement STORY_ID=DPDE-30 GENERATE_QUEUE=true`

> 

This will generate an implementation queue - a logical order to run the tasks segregrated by repositories and phases. The generated artifact will have the instruction to run the next set of commands

> 

So, the next set of commands will be

`/speckit.implement STORY_ID=DPDE-30 REPO=<> PHASE=<>`

> 

After this is completed, JIRA stories will be updated with the implementation details.

## Step 5: Raise PRs

Finally, after all the elements of implementation queue are completed, we need to run

`/speckit.implement STORY_ID=DPDE-30`

This will raise the PRs for each of the repositories and update the corresponding JIRA stories with the PR details.

> 

> 

