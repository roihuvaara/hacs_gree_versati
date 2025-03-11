# PowerShell script to run tests in the development container

param (
    [Parameter(Position=0)]
    [string]$TestPath = "tests/"
)

# Get the container ID of the running devcontainer
$containerId = docker ps --filter "name=hacs_gree_versati" --format "{{.ID}}"

if ([string]::IsNullOrEmpty($containerId)) {
    Write-Host "No running container found for this project." -ForegroundColor Red
    Write-Host "Please start the devcontainer first:" -ForegroundColor Yellow
    Write-Host "1. Open VS Code" -ForegroundColor Yellow
    Write-Host "2. Click the Remote Explorer button in the activity bar" -ForegroundColor Yellow 
    Write-Host "3. Right-click on the devcontainer and select 'Start Container'" -ForegroundColor Yellow
    exit 1
}

# Format the test path appropriately
$testPathArg = $TestPath

# Run tests in the container
Write-Host "Running tests in container: $testPathArg" -ForegroundColor Cyan
docker exec -it $containerId bash -c "cd /workspace && python -m pytest -xvs $testPathArg"

# Show the exit code
$exitCode = $LASTEXITCODE
if ($exitCode -eq 0) {
    Write-Host "Tests passed!" -ForegroundColor Green
} else {
    Write-Host "Tests failed with exit code $exitCode" -ForegroundColor Red
}

exit $exitCode 