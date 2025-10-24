#!/bin/bash
# Start DoIP Server for testing with doip_tester_yaml

echo "Starting DoIP Server for testing..."
echo "Configuration: config/test_gateway.yaml"
echo "Port: 13400"
echo "ECUs configured: Engine_ECM, Transmission_TCU, ABS, ESP, Steering_EPS, BCM, Gateway, HVAC"
echo ""
echo "To test with doip_tester_yaml, run your tests against localhost:13400"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server using poetry
poetry run python -m doip_server.main --gateway-config config/test_gateway.yaml
