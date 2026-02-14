#!/bin/bash
# Save CA certificate from environment variable if it exists
if [ ! -z "$CA_PEM" ]; then
    echo "$CA_PEM" > /etc/secrets/ca.pem
    export SSL_CA_PATH=/etc/secrets/ca.pem
fi

# Start the application
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
