#!/usr/bin/env python3
"""
DoIP Request/Response Handlers module.

This module provides handlers for different types of DoIP requests and responses,
including routing activation, diagnostic messages, and UDS processing.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from .messages import (
    DoIPMessage,
    ROUTING_ACTIVATION_RESPONSE_CODE_SUCCESS,
    ROUTING_ACTIVATION_RESPONSE_CODE_UNKNOWN_SOURCE_ADDRESS,
    ROUTING_ACTIVATION_RESPONSE_CODE_ALREADY_ACTIVATED,
)
from .hierarchical_config_manager import HierarchicalConfigManager


class DoIPHandlers:
    """Handles DoIP request/response processing."""

    def __init__(
        self,
        config_manager: HierarchicalConfigManager,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize DoIP handlers.

        Args:
            config_manager: Configuration manager instance
            logger: Logger instance for this handler
        """
        self.config_manager = config_manager
        self.logger = logger or logging.getLogger(__name__)
        self.message_handler = DoIPMessage(logger)
        self.response_cycle_state = {}

    def handle_routing_activation(self, payload: bytes) -> bytes:
        """Handle routing activation request.

        Args:
            payload: Raw routing activation request payload

        Returns:
            DoIP routing activation response message
        """
        self.logger.info("Processing routing activation request")

        try:
            source_address, activation_type = (
                self.message_handler.parse_routing_activation_request(payload)
            )
            self.logger.info(
                f"Source address: 0x{source_address:04X}, Activation type: {activation_type}"
            )

            # Get gateway logical address
            gateway_logical_address = self._get_gateway_logical_address()

            # Check if source address is authorized
            if not self._is_source_address_authorized(source_address):
                self.logger.warning(
                    f"Unauthorized source address: 0x{source_address:04X}"
                )
                return self.message_handler.create_routing_activation_response(
                    ROUTING_ACTIVATION_RESPONSE_CODE_UNKNOWN_SOURCE_ADDRESS,
                    source_address,
                    gateway_logical_address,
                )

            # Check if already activated
            if self._is_source_already_activated(source_address):
                self.logger.warning(
                    f"Source address already activated: 0x{source_address:04X}"
                )
                return self.message_handler.create_routing_activation_response(
                    ROUTING_ACTIVATION_RESPONSE_CODE_ALREADY_ACTIVATED,
                    source_address,
                    gateway_logical_address,
                )

            # Success
            self.logger.info(
                f"Routing activation successful for source: 0x{source_address:04X}"
            )
            return self.message_handler.create_routing_activation_response(
                ROUTING_ACTIVATION_RESPONSE_CODE_SUCCESS,
                source_address,
                gateway_logical_address,
            )

        except Exception as e:
            self.logger.error(f"Error processing routing activation: {e}")
            return self.message_handler.create_routing_activation_response(
                ROUTING_ACTIVATION_RESPONSE_CODE_UNKNOWN_SOURCE_ADDRESS,
                0x0000,
                self._get_gateway_logical_address(),
            )

    def handle_diagnostic_message(self, payload: bytes) -> List[bytes]:
        """Handle diagnostic message (UDS) and return list of responses.

        Args:
            payload: Raw diagnostic message payload

        Returns:
            List of DoIP diagnostic message responses
        """
        try:
            source_address, target_address, uds_payload = (
                self.message_handler.parse_diagnostic_message(payload)
            )
            self.logger.info(
                f"Diagnostic message: source=0x{source_address:04X}, target=0x{target_address:04X}"
            )

            # Check if source address is authorized
            if not self._is_source_address_authorized(source_address):
                self.logger.warning(
                    f"Unauthorized source address: 0x{source_address:04X}"
                )
                return [
                    self.message_handler.create_doip_nack(0x02)
                ]  # Invalid source address

            # Check if target address is valid
            if not self.config_manager.is_target_address_valid(target_address):
                self.logger.warning(f"Invalid target address: 0x{target_address:04X}")
                return [
                    self.message_handler.create_doip_nack(0x03)
                ]  # Invalid target address

            # Check if target is functional address
            if self._is_functional_address(target_address):
                return self._handle_functional_diagnostic_message(
                    source_address, target_address, uds_payload
                )
            else:
                return self._handle_physical_diagnostic_message(
                    source_address, target_address, uds_payload
                )

        except Exception as e:
            self.logger.error(f"Error processing diagnostic message: {e}")
            return [
                self.message_handler.create_doip_nack(0x02)
            ]  # Invalid payload length

    def handle_alive_check(self) -> bytes:
        """Handle alive check request.

        Returns:
            DoIP alive check response message
        """
        self.logger.info("Processing alive check request")
        return self.message_handler.create_alive_check_response()

    def handle_power_mode_request(self, payload: bytes) -> bytes:
        """Handle power mode information request.

        Args:
            payload: Raw power mode request payload

        Returns:
            DoIP power mode response message
        """
        self.logger.info("Processing power mode information request")

        try:
            power_mode_config = self.config_manager.get_power_mode_config()
            current_status = power_mode_config.get("current_status", 0x0001)

            # Check if response cycling is enabled
            response_cycling = power_mode_config.get("response_cycling", {})
            if response_cycling.get("enabled", False):
                # Get cycling statuses
                cycle_through = response_cycling.get("cycle_through", [0x0001])
                if cycle_through:
                    # Use response cycling logic with string key format
                    cycle_key = "power_mode_power_mode_status"
                    if cycle_key not in self.response_cycle_state:
                        self.response_cycle_state[cycle_key] = 0

                    current_index = self.response_cycle_state[cycle_key]
                    current_status = cycle_through[current_index % len(cycle_through)]

                    # Update index for next time
                    self.response_cycle_state[cycle_key] = (current_index + 1) % len(
                        cycle_through
                    )

                    self.logger.info(
                        f"Power mode response cycling: index {current_index}, status 0x{current_status:04X}"
                    )

            return self.message_handler.create_power_mode_response(current_status)
        except Exception as e:
            self.logger.error(f"Error processing power mode request: {e}")
            return self.message_handler.create_power_mode_response(0x0001)

    def handle_entity_status_request(self, payload: bytes) -> bytes:
        """Handle DoIP entity status request.

        Args:
            payload: Raw entity status request payload

        Returns:
            DoIP entity status response message
        """
        self.logger.info("Processing DoIP entity status request")

        try:
            entity_status_config = self.config_manager.get_gateway_config().get(
                "entity_status", {}
            )
            entity_status = entity_status_config.get("status", 0x01)  # Default to ready
            return self.message_handler.create_entity_status_response(entity_status)
        except Exception as e:
            self.logger.error(f"Error processing entity status request: {e}")
            return self.message_handler.create_entity_status_response(0x01)

    def process_uds_message(
        self, uds_payload: bytes, target_address: int
    ) -> Optional[bytes]:
        """Process UDS message and return response for specific ECU.

        Args:
            uds_payload: Raw UDS payload
            target_address: Target ECU address

        Returns:
            UDS response payload or None if no response
        """
        try:
            if len(uds_payload) == 0:
                return None

            # Convert payload to hex string for matching
            request_hex = uds_payload.hex().upper()
            service_id = uds_payload[0]
            self.logger.info(
                f"Processing UDS request {request_hex} for ECU 0x{target_address:04X}"
            )

            # Get ECU configuration
            ecu_config = self.config_manager.get_ecu_config(target_address)
            if not ecu_config:
                self.logger.warning(
                    f"No configuration found for ECU 0x{target_address:04X}"
                )
                return self.message_handler.create_uds_negative_response(
                    service_id, 0x11
                )  # Service not supported

            # Get UDS services configuration for this ECU
            ecu_services = self.config_manager.get_ecu_uds_services(target_address)

            # Find matching service by request
            service_config = self.config_manager.get_uds_service_by_request(
                request_hex, target_address
            )
            if not service_config:
                self.logger.warning(f"No service found for request {request_hex}")
                return self.message_handler.create_uds_negative_response(
                    service_id, 0x11
                )

            service_name = service_config["name"]
            responses = service_config.get("responses", [])

            if not responses:
                self.logger.warning(
                    f"No responses configured for service {service_name}"
                )
                return self.message_handler.create_uds_negative_response(
                    service_id, 0x11
                )

            # Handle response cycling
            cycling_key = f"ECU_0x{target_address:04X}_{service_name}"

            # Initialize cycling state if not exists
            if cycling_key not in self.response_cycle_state:
                self.response_cycle_state[cycling_key] = 0

            # Get current cycle index
            cycle_index = self.response_cycle_state[cycling_key]

            # Get response at current index
            if cycle_index < len(responses):
                response_hex = responses[cycle_index]
                # Process response with mirroring if needed
                response_hex = self.config_manager.process_response_with_mirroring(
                    response_hex, request_hex
                )

                # Convert to bytes
                response = bytes.fromhex(
                    response_hex.replace("0x", "").replace(" ", "")
                )

                # Advance cycle index
                self.response_cycle_state[cycling_key] = (cycle_index + 1) % len(
                    responses
                )

                self.logger.info(
                    f"Generated UDS response for service {service_name}: {response.hex()}"
                )
                return response
            else:
                # Fallback to first response
                response_hex = responses[0]
                response_hex = self.config_manager.process_response_with_mirroring(
                    response_hex, request_hex
                )
                response = bytes.fromhex(
                    response_hex.replace("0x", "").replace(" ", "")
                )

                # Reset cycle
                self.response_cycle_state[cycling_key] = 1

                self.logger.info(
                    f"Generated UDS response for service {service_name} (fallback): {response.hex()}"
                )
                return response

        except Exception as e:
            self.logger.error(f"Error processing UDS message: {e}")
            return self.message_handler.create_uds_negative_response(
                service_id, 0x72
            )  # Request sequence error

    def reset_response_cycling(
        self, ecu_address: Optional[int] = None, service_name: Optional[str] = None
    ):
        """Reset response cycling state for a specific ECU-service combination or all states.

        Args:
            ecu_address: ECU address to reset (None for all ECUs)
            service_name: Service name to reset (None for all services)
        """
        if ecu_address is None and service_name is None:
            # Reset all
            self.response_cycle_state.clear()
            self.logger.info("Reset all response cycling states")
        elif ecu_address is not None and service_name is not None:
            # Reset specific ECU-service combination
            key = f"ECU_0x{ecu_address:04X}_{service_name}"
            if key in self.response_cycle_state:
                del self.response_cycle_state[key]
                self.logger.info(
                    f"Reset response cycling for ECU 0x{ecu_address:04X}, service {service_name}"
                )
        else:
            # Reset all for specific ECU or service
            keys_to_remove = []
            for key in self.response_cycle_state:
                if ecu_address is not None and key.startswith(
                    f"ECU_0x{ecu_address:04X}_"
                ):
                    keys_to_remove.append(key)
                elif service_name is not None and key.endswith(f"_{service_name}"):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.response_cycle_state[key]

            self.logger.info(
                f"Reset response cycling for {len(keys_to_remove)} combinations"
            )

    def get_response_cycling_state(self) -> Dict[str, Any]:
        """Get current response cycling state for debugging.

        Returns:
            Dictionary containing response cycling state
        """
        return self.response_cycle_state.copy()

    def process_doip_message(self, message: bytes) -> Optional[bytes]:
        """Process DoIP message and return response.

        Args:
            message: Raw DoIP message

        Returns:
            DoIP response message or None
        """
        try:
            if len(message) < 8:
                self.logger.error("DoIP message too short")
                return None

            # Parse DoIP header
            protocol_version = message[0]
            inverse_version = message[1]
            payload_type = int.from_bytes(message[2:4], byteorder="big")
            payload_length = int.from_bytes(message[4:8], byteorder="big")

            # Validate protocol version
            if protocol_version != 0x02 or inverse_version != 0xFD:
                self.logger.error(
                    f"Invalid DoIP protocol version: {protocol_version:02X}, {inverse_version:02X}"
                )
                return None

            # Extract payload
            if len(message) < 8 + payload_length:
                self.logger.error("DoIP message payload too short")
                return None

            payload = message[8 : 8 + payload_length] if payload_length > 0 else b""

            # Route based on payload type
            if payload_type == 0x0001:  # Vehicle Identification Request
                return self.message_handler.create_vehicle_identification_response()
            elif payload_type == 0x0002:  # Vehicle Identification Request with EID
                return self.message_handler.create_vehicle_identification_response()
            elif payload_type == 0x0003:  # Vehicle Announcement
                return None  # No response needed
            elif payload_type == 0x0004:  # Routing Activation Request
                return self.handle_routing_activation(payload)
            elif payload_type == 0x0005:  # Alive Check Request
                return self.handle_alive_check()
            elif payload_type == 0x4001:  # DoIP Entity Status Request
                return self.handle_entity_status_request(payload)
            elif payload_type == 0x4003:  # Power Mode Information Request
                return self.handle_power_mode_request(payload)
            elif payload_type == 0x8001:  # Diagnostic Message
                responses = self.handle_diagnostic_message(payload)
                return responses[0] if responses else None
            else:
                self.logger.warning(f"Unknown DoIP payload type: 0x{payload_type:04X}")
                return None

        except Exception as e:
            self.logger.error(f"Error processing DoIP message: {e}")
            return None

    def _handle_functional_diagnostic_message(
        self, source_address: int, functional_address: int, uds_payload: bytes
    ) -> List[bytes]:
        """Handle functional diagnostic message (broadcast to multiple ECUs).

        Args:
            source_address: Source logical address
            functional_address: Functional address
            uds_payload: UDS payload

        Returns:
            List of DoIP diagnostic message responses
        """
        self.logger.info(
            f"Handling functional diagnostic message to 0x{functional_address:04X}"
        )

        # Get ECUs that respond to this functional address
        responding_ecus = self._get_responding_ecus_for_functional_address(
            functional_address
        )

        if not responding_ecus:
            self.logger.warning(
                f"No ECUs configured for functional address 0x{functional_address:04X}"
            )
            return []

        # Create ACK first
        ack_response = self.message_handler.create_diagnostic_message_ack(
            source_address, functional_address
        )

        # Process UDS message for each responding ECU
        responses = [ack_response]
        for ecu_address in responding_ecus:
            uds_response = self.process_uds_message(uds_payload, ecu_address)
            if uds_response:
                response = self.message_handler.create_diagnostic_message_response(
                    ecu_address, source_address, uds_response
                )
                responses.append(response)
                self.logger.info(f"Generated response from ECU 0x{ecu_address:04X}")

        return responses

    def _handle_physical_diagnostic_message(
        self, source_address: int, target_address: int, uds_payload: bytes
    ) -> List[bytes]:
        """Handle physical diagnostic message (single ECU).

        Args:
            source_address: Source logical address
            target_address: Target ECU address
            uds_payload: UDS payload

        Returns:
            List of DoIP diagnostic message responses
        """
        self.logger.info(
            f"Handling physical diagnostic message to 0x{target_address:04X}"
        )

        # Create ACK first
        ack_response = self.message_handler.create_diagnostic_message_ack(
            source_address, target_address
        )

        # Process UDS message
        uds_response = self.process_uds_message(uds_payload, target_address)

        responses = [ack_response]
        if uds_response:
            response = self.message_handler.create_diagnostic_message_response(
                target_address, source_address, uds_response
            )
            responses.append(response)
            self.logger.info(f"Generated response from ECU 0x{target_address:04X}")

        return responses

    def _is_functional_address(self, address: int) -> bool:
        """Check if address is a functional address.

        Args:
            address: Address to check

        Returns:
            True if address is functional
        """
        # Functional addresses are typically in the range 0x1FFF-0x1FFE
        return 0x1FFE <= address <= 0x1FFF

    def _is_source_address_authorized(self, source_address: int) -> bool:
        """Check if source address is authorized.

        Args:
            source_address: Source address to check

        Returns:
            True if address is authorized
        """
        # Check if source address is in the allowed range (0x0E00-0x0EFF for testers)
        # This is a basic validation - could be enhanced with configuration
        return 0x0E00 <= source_address <= 0x0EFF

    def _is_source_already_activated(self, source_address: int) -> bool:
        """Check if source address is already activated.

        Args:
            source_address: Source address to check

        Returns:
            True if address is already activated
        """
        # For now, always allow activation
        # This could be enhanced with session tracking
        return False

    def _get_responding_ecus_for_functional_address(
        self, functional_address: int
    ) -> List[int]:
        """Get list of ECUs that respond to a functional address.

        Args:
            functional_address: Functional address

        Returns:
            List of ECU addresses
        """
        # Get all ECU configurations
        all_ecus = self.config_manager.get_all_ecu_addresses()
        responding_ecus = []

        for ecu_address in all_ecus:
            ecu_config = self.config_manager.get_ecu_config(ecu_address)
            if ecu_config:
                functional_addresses = ecu_config.get("functional_addresses", [])
                if functional_address in functional_addresses:
                    responding_ecus.append(ecu_address)

        return responding_ecus

    def _get_gateway_logical_address(self) -> int:
        """Get gateway logical address from configuration.

        Returns:
            Gateway logical address
        """
        try:
            gateway_config = self.config_manager.get_gateway_config()
            return gateway_config.get("logical_address", 0x0E80)
        except Exception:
            return 0x0E80  # Default gateway address
