#!/bin/sh
mkdir -p /usr/share/nginx/html/admin-console
cat > /usr/share/nginx/html/admin-console/env-config.json <<EOF
{
  "AAA_URL": "${AAA_URL}",
  "ADMIN_API_BACKEND_URL": "${ADMIN_API_BACKEND_URL}",
  "ADMIN_APP_ROOT": "${ADMIN_APP_ROOT}"
}
EOF

nginx -g 'daemon off;'
