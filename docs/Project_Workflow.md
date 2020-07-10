# Project Workflow

## ✨ Start an Iteration
Each iteration on this repository will be tracked by a GitHub **[Milestone](https://help.github.com/en/github/managing-your-work-on-github/about-milestones)**. The completion of the milestone will queue a GitHub **[Release](https://help.github.com/en/github/administering-a-repository/managing-releases-in-a-repository)**. Issues will be added to the milestones to indicate work needed. After completion, this milestone can then act as a list of work contained within a release. 

## 🔀 Pull Request

### Attach Issue
Each pull request **MUST** be attached to an issue. On the surface, this ensures that closing a pull request will close an issue. This also ensures the issue can be included in the milestone. For this repository, the use of issues assists the team to use the [project board]() to track the progress towards a milestone.  

### Validation
Each pull request is validated by the [Pull Request Validation](https://github.com/microsoft/electionguard-python/blob/main/.github/workflows/pull_request.yml) GitHub [Action](https://help.github.com/en/actions). This action can be viewed from the PR or from the actions to inspect the details. 

### Review
All pull requests require a review from a **Contributor** but any reviewers are welcome.

## 🏁 Create a Release
At the end of an iteration aka when a milestone is complete, a release can be created. 

### Steps
1. Raise version number in `setup.py`
2. Close Milestone 
3. Edit Release details _(optional)_

### Release Workflow

Closing the milestone queues the [Release Build](https://github.com/microsoft/electionguard-python/blob/main/.github/workflows/release.yml) GitHub [Action](https://help.github.com/en/actions). This action is designed to reduce the effort by maintainers and give the community an open view of the package flow.

- Build package
- Create dependency graph
- Upload package to PyPi
- Validate PyPi package
- Upload package and graph to GitHub Workflow
- Create Release
- Upload zipped package and graph to Release
- Update GitHub Pages Documentation