# Release Workflow Setup Guide

## Overview
This GitHub Action workflow automatically creates semver tags and publishes your package to PyPI on successful merges to the `main` branch.

## Setup Instructions

### 1. PyPI Configuration
You need to configure PyPI publishing using the Trusted Publisher feature (recommended) or API tokens.

#### Option A: Trusted Publisher (Recommended)
1. Go to your project on PyPI: https://pypi.org/project/django-stagedoor/
2. Navigate to "Publishing" → "Add a publisher"
3. Add the following configuration:
   - Owner: `galaxybrainco` (your GitHub username)
   - Repository: `django-stagedoor`
   - Workflow name: `release.yml`
   - Environment: (leave blank)

#### Option B: API Token
1. Go to https://pypi.org/manage/account/token/
2. Create a new API token with scope for `django-stagedoor`
3. In your GitHub repository, go to Settings → Secrets and variables → Actions
4. Add a new secret named `PYPI_API_TOKEN` with your token value

If using Option B, update the publish step in the workflow to :
```yaml
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.PYPI_API_TOKEN }}
    print-hash: true
```

### 2. GitHub Permissions
The workflow requires write permissions for:
- Contents (to push version bumps and create tags)
- ID Token (for PyPI trusted publishing)

These are already configured in the workflow.

## How It Works

### Automatic Version Bumping
The workflow analyzes commit messages to determine the version bump type:
- **Major** (1.0.0 → 2.0.0): Include "Major Version Bump" anywhere in commit message
- **Minor** (1.0.0 → 1.1.0): Include "Minor Version Bump" anywhere in commit message
- **Patch** (1.0.0 → 1.0.1): Default for all other commits

The search is case-insensitive, so "minor version bump", "Minor Version Bump", or "MINOR VERSION BUMP" all work.

### Manual Triggering
You can also manually trigger the workflow from the Actions tab with a specific version bump type.

### Workflow Steps
1. Analyzes commits since the last tag
2. Determines appropriate version bump
3. Updates version in `pyproject.toml`
4. Commits the version change
5. Creates and pushes a git tag
6. Builds the Python package
7. Publishes to PyPI
8. Creates a GitHub Release

## Commit Message Examples
- Patch version (default):
  ```
  fix: resolve issue with user authentication
  ```
- Minor version:
  ```
  feat: add new user dashboard
  
  Minor Version Bump
  ```
- Major version:
  ```
  refactor: complete API redesign
  
  Major Version Bump
  ```

## Testing
Before the first production release:
1. Test with a manual workflow dispatch to a test branch
2. Verify the version bump logic works correctly
3. Ensure PyPI authentication is properly configured

## Troubleshooting
- If the workflow fails at the PyPI publish step, check your authentication configuration
- If version bumping fails, ensure your commit messages follow the convention
- Check that the workflow has necessary permissions in repository settings