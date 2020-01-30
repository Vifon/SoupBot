#!/bin/bash

set -o errexit -o nounset -o pipefail

VERBOSE=0
COVERAGE=0
TIMEOUT=0

while getopts "vct" ARG; do
    case "$ARG" in
        v)
            VERBOSE=1
            ;;
        c)
            COVERAGE=1
            ;;
        t)
            TIMEOUT=1
            ;;
        ?)
            exit 1
            ;;
    esac
done
shift $((OPTIND-1))



start_test_server() {
    ./test_server.py &
    SERVER_PID="$!"
    sleep 0.2
}

start_test_client() {
    local COMMAND
    COMMAND=(./bot.py test_config.yml)

    if (( "$COVERAGE" )); then
        COMMAND=(
            coverage run --branch --source=bot,irc "${COMMAND[@]}"
        )
    fi

    if (( "$TIMEOUT" )); then
        COMMAND=(timeout 20s "${COMMAND[@]}")
    fi

    if (( "$VERBOSE" )); then
        "${COMMAND[@]}"
    else
        "${COMMAND[@]}" &> /dev/null
    fi
}

stop_test_server() {
    kill "$SERVER_PID" 2> /dev/null && echo "Killed the test server." || true
    exit
}

trap stop_test_server EXIT INT TERM
start_test_server
start_test_client "$@"
