#!/bin/bash
# Kill process running on a specific port
#
# Usage: ./kill_port.sh 8000
#        ./kill_port.sh 5001

PORT=${1:-8000}

if [ -z "$1" ]; then
    echo "Usage: ./kill_port.sh <port>"
    echo "Example: ./kill_port.sh 8000"
    exit 1
fi

PID=$(lsof -ti:$PORT 2>/dev/null)

if [ -z "$PID" ]; then
    echo "No process running on port $PORT"
else
    echo "Killing process $PID on port $PORT..."
    kill -9 $PID
    echo "Done."
fi
