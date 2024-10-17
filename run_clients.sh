#!/bin/bash

SERVER_HOST="owl.cs.umanitoba.ca"
SERVER_PORT=8576

read -p "Enter the number of clients to run: " NUM_CLIENTS

# number of clients to run
for ((i = 1; i <= NUM_CLIENTS; i++))

  do
    python test_client.py "$SERVER_HOST" "$SERVER_PORT" "Client_$i" &
    echo "Started running Client_$i"

done

wait 
