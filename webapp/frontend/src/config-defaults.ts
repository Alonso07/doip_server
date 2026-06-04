export const DOIP_DEFAULT_CONFIG = `gateway:
  name: "My DoIP Gateway"
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

logging:
  level: "INFO"
  console: true

security:
  enabled: false
`

// Empty = use built-in package config (copied to /config on first container start)
export const SOVD_DEFAULT_CONFIG = ``
