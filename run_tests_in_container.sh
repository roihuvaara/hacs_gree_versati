#!/bin/bash
# Bash script to run tests in the development container
# For Windows users: Run this script with Git Bash, WSL, or any Bash implementation

# Default test path if none provided
TEST_PATH=${@:-"tests/"}

# Get the container ID of the running devcontainer
CONTAINER_ID=$(docker ps --filter "name=hacs_gree_versati" --format "{{.ID}}")

if [ -z "$CONTAINER_ID" ]; then
    echo -e "\033[0;31mNo running container found for this project.\033[0m"
    echo -e "\033[0;33mPlease start the devcontainer first:\033[0m"
    echo -e "\033[0;33m1. Open VS Code\033[0m"
    echo -e "\033[0;33m2. Click the Remote Explorer button in the activity bar\033[0m"
    echo -e "\033[0;33m3. Right-click on the devcontainer and select 'Start Container'\033[0m"
    exit 1
fi

# Run tests in the container
echo -e "\033[0;36mRunning tests in container: $TEST_PATH\033[0m"
docker exec -it $CONTAINER_ID bash -c "cd /workspace && python -m pytest -xvs $TEST_PATH"

# Show the exit code
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\033[0;32mTests passed!\033[0m"
else
    echo -e "\033[0;31mTests failed with exit code $EXIT_CODE\033[0m"
fi

exit $EXIT_CODE 