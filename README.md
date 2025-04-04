# Match List Change Detector

[![CI](https://github.com/timmybird/match-list-change-detector/actions/workflows/ci.yml/badge.svg)](https://github.com/timmybird/match-list-change-detector/actions/workflows/ci.yml)
[![Docker](https://github.com/timmybird/match-list-change-detector/actions/workflows/docker.yml/badge.svg)](https://github.com/timmybird/match-list-change-detector/actions/workflows/docker.yml)
[![Security](https://github.com/timmybird/match-list-change-detector/actions/workflows/security.yml/badge.svg)](https://github.com/timmybird/match-list-change-detector/actions/workflows/security.yml)

A Python application that detects changes in your football referee match list and triggers actions when changes are found.

## Overview

This application:
1. Fetches your upcoming matches from the FOGIS API
2. Compares them with previously saved matches
3. Detects any changes (new matches, cancelled matches, time changes, etc.)
4. If changes are detected, triggers a docker-compose file to handle the changes
5. Saves the current matches for future comparisons

## Requirements

- Docker and Docker Compose
- FOGIS API credentials (username and password)

## Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/timmybird/match-list-change-detector.git
   cd match_list_change_detector
   ```

2. Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with your FOGIS credentials and other settings:
   ```bash
   # Open with your favorite editor
   nano .env
   ```

4. Create required directories:
   ```bash
   mkdir -p data logs
   ```

5. Create a docker-compose.override.yml file (optional):
   ```bash
   cp docker-compose.override.yml.example docker-compose.override.yml
   ```

6. Customize the orchestrator docker-compose file to include your actual services for:
   - Syncing matches to your calendar
   - Adding referee contact information to Google contacts
   - Creating assets for WhatsApp groups

## Usage

### Running Manually

To run the change detector manually:

```bash
# Using the run script
./run_detector.sh

# Or using Docker Compose
docker-compose up match-list-change-detector
```

### Running on a Schedule

To run the change detector on an hourly schedule:

```bash
docker-compose -f scheduled-docker-compose.yml up -d
```

This will create a scheduler container that runs the change detector every hour.

### Running Tests

To run the tests:

```bash
# Using the run script
./run_tests.sh

# Or manually
source .venv/bin/activate
python -m unittest discover -s tests
```

## How It Works

1. The application fetches your match list from the FOGIS API using the `fogis-api-client-timmyBird` package.
2. It compares the current match list with the previously saved list.
3. If changes are detected, it saves the changes to a JSON file and triggers the orchestrator docker-compose file.
4. The orchestrator services can then read the changes from the JSON file and perform their respective actions.

## Project Structure

### Core Files
- `match_list_change_detector.py`: The main Python script that detects changes
- `config.py`: Configuration management
- `logging_config.py`: Centralized logging configuration

### Docker Files
- `Dockerfile`: Containerizes the Python script
- `docker-compose.yml`: Defines the change detector service
- `docker-compose.override.yml.example`: Example override file for local customization
- `scheduled-docker-compose.yml`: Sets up a scheduler to run the change detector on a schedule

### Scripts
- `run_detector.sh`: Script to run the detector
- `run_test.sh`: Script to run the API client test with interactive credentials
- `run_test_with_env.sh`: Script to run the API client test with .env credentials
- `run_tests.sh`: Script to run all unit tests

### Configuration
- `.env.example`: Example environment variables file
- `requirements.txt`: Lists the Python dependencies
- `setup.cfg`: Configuration for development tools (flake8, etc.)

### Tests
- `tests/`: Directory containing unit tests

## Logs

Logs are written to the `logs` directory and are also available in the container logs:

```bash
# View logs in the logs directory
cat logs/match_list_change_detector.log

# Or view container logs
docker logs match-list-change-detector
```

## Configuration

You can customize the behavior of the change detector by modifying the following environment variables in your `.env` file:

### API Credentials
- `FOGIS_USERNAME`: Your FOGIS username
- `FOGIS_PASSWORD`: Your FOGIS password

### Match List Configuration
- `DAYS_BACK`: Number of days in the past to include in the match list (default: 7)
- `DAYS_AHEAD`: Number of days in the future to include in the match list (default: 365)
- `PREVIOUS_MATCHES_FILE`: File to store previous matches (default: previous_matches.json)

### Orchestrator Configuration
- `DOCKER_COMPOSE_FILE`: Path to the orchestrator docker-compose file (default: ../MatchListProcessor/docker-compose.yml)

### Logging Configuration
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: INFO)
- `LOG_DIR`: Directory to store log files (default: logs)
- `LOG_FILE`: Log file name (default: match_list_change_detector.log)

### Docker Configuration
- `CONTAINER_NETWORK`: Docker network to use (default: fogis-network)

### Timezone
- `TZ`: Timezone (default: Europe/Stockholm)

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

### Workflows

- **CI**: Runs tests and linting on Python 3.9, 3.10, and 3.11
- **Docker**: Builds and publishes Docker images to GitHub Container Registry
- **Security**: Runs security scans including CodeQL and Bandit
- **Dependencies**: Automatically updates dependencies weekly
- **Release**: Creates GitHub releases when tags are pushed
- **Stale**: Marks and closes stale issues and pull requests
- **Labeler**: Automatically labels pull requests based on changed files
- **Greetings**: Welcomes new contributors

### Docker Images

Docker images are automatically built and published to GitHub Container Registry:

```bash
# Pull the latest image
docker pull ghcr.io/timmybird/match-list-change-detector:main

# Or pull a specific version
docker pull ghcr.io/timmybird/match-list-change-detector:v1.0.0
```

## Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-new-feature`
3. Make your changes
4. Run the tests: `./run_tests.sh`
5. Commit your changes: `git commit -am 'Add some feature'`
6. Push to the branch: `git push origin feature/my-new-feature`
7. Submit a pull request

### Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the tests:
   ```bash
   ./run_tests.sh
   ```
