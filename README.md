Redis as a session storage for Odoo
=================

## Configuration

1. Install this module to your addons folder.
2. add these parameters to configuration file (openerp_server.conf).
    + use_redis (required) : to enable this module
    + redis_host (optional) : default to 'localhost'
    + redis_port (optional) : default to 6379
    + redis_salt (optional) : salt using with generate_key 
3. Restart Odoo process and install 'Redis as Session Storage' in Odoo Apps.