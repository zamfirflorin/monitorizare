#!/bin/bash
# Script to get your Mac's IP address for Podman configuration
# Run this if your IP changes (e.g., after connecting to a different network)

HOST_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || ifconfig | grep -E "inet.*broadcast" | awk '{print $2}' | head -1)

if [ -z "$HOST_IP" ]; then
    echo "Could not determine host IP. Please set it manually in prometheus.yml"
    exit 1
fi

echo "Your host IP is: $HOST_IP"
echo ""
echo "Update prometheus.yml with this IP:"
echo "  - targets: [ '$HOST_IP:8000' ]"

