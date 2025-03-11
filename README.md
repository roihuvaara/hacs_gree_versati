# Notice

The component and platforms in this repository are not meant to be used by a
user, but as a "blueprint" that custom component developers can build
upon, to make more awesome stuff.

HAVE FUN! 😎

## Why?

This is simple, by having custom_components look (README + structure) the same
it is easier for developers to help each other and for users to start using them.

If you are a developer and you want to add things to this "blueprint" that you think more
developers will have use for, please open a PR to add it :)

## What?

This repository contains multiple files, here is a overview:

File | Purpose | Documentation
-- | -- | --
`.devcontainer.json` | Used for development/testing with Visual Studio Code. | [Documentation](https://code.visualstudio.com/docs/remote/containers)
`.github/ISSUE_TEMPLATE/*.yml` | Templates for the issue tracker | [Documentation](https://help.github.com/en/github/building-a-strong-community/configuring-issue-templates-for-your-repository)
`custom_components/integration_blueprint/*` | Integration files, this is where everything happens. | [Documentation](https://developers.home-assistant.io/docs/creating_component_index)
`CONTRIBUTING.md` | Guidelines on how to contribute. | [Documentation](https://help.github.com/en/github/building-a-strong-community/setting-guidelines-for-repository-contributors)
`LICENSE` | The license file for the project. | [Documentation](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/licensing-a-repository)
`README.md` | The file you are reading now, should contain info about the integration, installation and configuration instructions. | [Documentation](https://help.github.com/en/github/writing-on-github/basic-writing-and-formatting-syntax)
`requirements.txt` | Python packages used for development/lint/testing this integration. | [Documentation](https://pip.pypa.io/en/stable/user_guide/#requirements-files)

## How?

1. Create a new repository in GitHub, using this repository as a template by clicking the "Use this template" button in the GitHub UI.
1. Open your new repository in Visual Studio Code devcontainer (Preferably with the "`Dev Containers: Clone Repository in Named Container Volume...`" option).
1. Rename all instances of the `integration_blueprint` to `custom_components/<your_integration_domain>` (e.g. `custom_components/awesome_integration`).
1. Rename all instances of the `Integration Blueprint` to `<Your Integration Name>` (e.g. `Awesome Integration`).
1. Run the `scripts/develop` to start HA and test out your new integration.

## Next steps

These are some next steps you may want to look into:
- Add tests to your integration, [`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) can help you get started.
- Add brand images (logo/icon) to https://github.com/home-assistant/brands.
- Create your first release.
- Share your integration on the [Home Assistant Forum](https://community.home-assistant.io/).
- Submit your integration to [HACS](https://hacs.xyz/docs/publish/start).

# Testing with DevContainer

This project includes a DevContainer configuration to simplify testing in a Linux environment.

## Prerequisites

1. [Visual Studio Code](https://code.visualstudio.com/)
2. [Docker Desktop](https://www.docker.com/products/docker-desktop/)
3. [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension for VS Code
4. A Bash shell (Git Bash, WSL, or any other Bash implementation on Windows)

## Running Tests in DevContainer

### Option 1: Use the Bash Script

The repository includes a Bash script to run tests in the container without having to enter the container yourself:

1. Make sure Docker Desktop is running
2. Make sure the devcontainer is running in VS Code
3. Open a Bash shell (Git Bash, WSL, or similar on Windows)
4. Run the script:

```bash
# Make script executable (only needed once)
chmod +x run_tests_in_container.sh

# Run all tests
./run_tests_in_container.sh

# Run specific tests
./run_tests_in_container.sh tests/test_climate.py
```

### Option 2: Enter the Container

1. Open the project in VS Code
2. Click on the green button in the bottom-left corner of the window
3. Select "Reopen in Container" from the menu
4. Wait for the container to build and start (this may take a few minutes the first time)
5. Once the container is running, you can:
   - Run tests directly from VS Code's Test Explorer
   - Use the terminal and run `python -m pytest tests/`
   - Use the included script `.devcontainer/test_runner.sh`

## Benefits of Using DevContainer

- Avoids Windows-specific asyncio loop issues
- Provides a consistent testing environment
- Matches the environment used by Home Assistant more closely
- Eliminates compatibility problems with pytest-socket

## Manual Testing

From the terminal in the devcontainer:

```bash
# Run all tests
python -m pytest tests/

# Run a specific test file
python -m pytest tests/test_minimal.py

# Run with coverage report
python -m pytest --cov=custom_components.gree_versati tests/
```
