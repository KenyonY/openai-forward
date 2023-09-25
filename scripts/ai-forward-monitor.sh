#!/bin/bash

# Configuration variables
port=27001
workers=$(nproc)
#workers=2

max_retries=2  # Maximum number of retries for health checks
failure_count=0  # Counter for failed health checks

# Function to start the service
start_service() {
  aifd run --port $1 --workers=$2 &
  echo "ai-forword monitor started"
}

# Function to restart the service
restart_service() {
  echo "Service is not healthy. Restarting..."
  pkill aifd
  start_service $1 $2
}

# Function to check the service health
check_health() {
  curl --max-time 2 --silent --write-out "%{http_code}" --output /dev/null http://localhost:$1/healthz
}

# Start the service
start_service $port $workers

# Wait for service to start
sleep 5

# Main loop for health checks
while true; do
  response=$(check_health $port)

  if [[ "$response" -ne 200 ]]; then
    echo "Initial health check failed. Entering rapid retry mode."

    # Rapid retry loop
    while [[ "$failure_count" -lt $max_retries ]]; do
      response=$(check_health $port)

      if [[ "$response" -eq 200 ]]; then
        echo "Service is healthy again."
        failure_count=0  # Reset the failure_count after rapid retry loop
        break
      else
        ((failure_count++))
        echo "Failed health check $failure_count times."
        sleep 1
      fi
    done

    if [[ "$failure_count" -ge $max_retries ]]; then
      restart_service $port $workers
    fi
  fi

  sleep 30
done
