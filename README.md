# Match List Change Detector

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
   ```
   git clone https://github.com/yourusername/match_list_change_detector.git
   cd match_list_change_detector
   ```

2. Create a `.env` file with your FOGIS credentials:
   ```
   FOGIS_USERNAME=your_username
   FOGIS_PASSWORD=your_password
   DAYS_BACK=7
   DAYS_AHEAD=365
   ```

3. Customize the `orchestrator-docker-compose.yml` file to include your actual services for:
   - Syncing matches to your calendar
   - Adding referee contact information to Google contacts
   - Creating assets for WhatsApp groups

## Usage

### Running Manually

To run the change detector manually:

```bash
docker-compose up match-list-change-detector
```

### Running on a Schedule

To run the change detector on an hourly schedule:

```bash
docker-compose -f scheduled-docker-compose.yml up -d
```

This will create a scheduler container that runs the change detector every hour.

## How It Works

1. The application fetches your match list from the FOGIS API using the `fogis-api-client-timmyBird` package.
2. It compares the current match list with the previously saved list.
3. If changes are detected, it saves the changes to a JSON file and triggers the orchestrator docker-compose file.
4. The orchestrator services can then read the changes from the JSON file and perform their respective actions.

## Files

- `match_list_change_detector.py`: The main Python script that detects changes
- `Dockerfile`: Containerizes the Python script
- `docker-compose.yml`: Defines the change detector service
- `scheduled-docker-compose.yml`: Sets up a scheduler to run the change detector on a schedule
- `orchestrator-docker-compose.yml`: Defines the services to be triggered when changes are detected
- `requirements.txt`: Lists the Python dependencies

## Logs

Logs are written to `match_list_change_detector.log` and are also available in the container logs:

```bash
docker logs match-list-change-detector
```

## Customization

You can customize the behavior of the change detector by modifying the following environment variables:

- `DAYS_BACK`: Number of days in the past to include in the match list (default: 7)
- `DAYS_AHEAD`: Number of days in the future to include in the match list (default: 365)
- `DOCKER_COMPOSE_FILE`: Path to the orchestrator docker-compose file (default: orchestrator-docker-compose.yml)
