#!/bin/bash

# Script to exercise the sample application endpoints
# This generates various metrics for Prometheus

BASE_URL="${BASE_URL:-http://localhost:8000}"
REGIONS=("us-east" "us-west" "eu-central" "ap-south")
USER_IDS=(1 2 3 4 5 10 20 30 40 50)

echo "Starting to exercise application endpoints..."
echo "Base URL: $BASE_URL"
echo "Press Ctrl+C to stop"
echo ""

# Function to make a request with optional headers
make_request() {
    local method=$1
    local endpoint=$2
    local region=${3:-}
    
    if [ -n "$region" ]; then
        curl -s -X "$method" \
            -H "X-Region: $region" \
            "$BASE_URL$endpoint" > /dev/null
    else
        curl -s -X "$method" "$BASE_URL$endpoint" > /dev/null
    fi
}

# Counter for iterations
iteration=0

while true; do
    iteration=$((iteration + 1))
    echo "[Iteration $iteration] Generating traffic..."
    
    # Health check
    make_request "GET" "/"
    
    # Products endpoint - generates products_viewed_total
    for i in {1..5}; do
        region=${REGIONS[$RANDOM % ${#REGIONS[@]}]}
        make_request "GET" "/products" "$region"
    done
    
    # Orders endpoint - generates orders_total, order_value_total, last_order_timestamp
    for i in {1..10}; do
        region=${REGIONS[$RANDOM % ${#REGIONS[@]}]}
        make_request "POST" "/orders" "$region"
    done
    
    # User logins - generates last_user_login_timestamp
    for user_id in "${USER_IDS[@]}"; do
        make_request "POST" "/users/$user_id/login"
    done
    
    # API v1 and v2 calls - for fill missing data examples
    for i in {1..3}; do
        make_request "GET" "/api/v1/data"
        make_request "GET" "/api/v2/data"
        # Occasionally call v3 (less frequent for fill examples)
        if [ $((RANDOM % 5)) -eq 0 ]; then
            make_request "GET" "/api/v3/data"
        fi
    done
    
    # Slow endpoint - for duration analysis
    make_request "GET" "/slow"
    
    # Error endpoint - for error rate analysis
    for i in {1..2}; do
        make_request "GET" "/error"
    done
    
    # Random delay between iterations (1-3 seconds)
    sleep $((1 + RANDOM % 3))
done

