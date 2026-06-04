DOIP_DEFAULT_CONFIG = """\
gateway:
  name: "{name}"
  description: "DoIP Gateway"
  logical_address: 0x1000

  vehicle:
    vin: "1HGBH41JXMN109186"
    eid: "123456789ABC"
    gid: "DEF012345678"

  network:
    host: "0.0.0.0"
    dual_stack: false
    port: 13400
    max_connections: 10
    timeout: 60
    keep_alive: true
    tcp_nodelay: true

  protocol:
    version: 0x02
    inverse_version: 0xFD

  settings:
    enable_logging: true
    log_level: "INFO"
    enable_security: false
    allow_multiple_sessions: true

  ecus: []

  power_mode_status:
    current_status: 0x01
    response_cycling:
      enabled: false

  entity_status:
    node_type: 0x01
    max_open_sockets: 10
    current_open_sockets: 0

logging:
  level: "INFO"
  console: true
  file: "doip_server.log"

security:
  enabled: false
"""
