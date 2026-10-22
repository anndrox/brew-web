#!/bin/sh
# Run inside the image being assessed, not on a developer/runner host.
set -eu

for executable in php php-cgi php-fpm frankenphp; do
  if command -v "$executable" >/dev/null 2>&1; then
    printf 'Unexpected PHP executable: %s\n' "$executable" >&2
    exit 1
  fi
done

if command -v dpkg-query >/dev/null 2>&1; then
  packages="$(dpkg-query -W -f='${db:Status-Status}\t${binary:Package}\t${Version}\n')"
  php_packages="$(printf '%s\n' "$packages" | awk '$1 == "installed" && $2 ~ /^(php|libapache2-mod-php|frankenphp)/ {print}')"
elif command -v apk >/dev/null 2>&1; then
  packages="$(apk info -v)"
  php_packages="$(printf '%s\n' "$packages" | awk '/^(php[0-9]*-|frankenphp-|apache2-mod-php)/ {print}')"
else
  printf '%s\n' 'Unsupported package database; cannot verify PHP absence.' >&2
  exit 1
fi
if [ -n "$php_packages" ]; then
  printf 'Unexpected PHP packages:\n%s\n' "$php_packages" >&2
  exit 1
fi

for directory in /usr /opt /bin /sbin; do
  if [ -d "$directory" ]; then
    php_files="$(find "$directory" -type f \( -name php -o -name 'php[0-9]*' \
      -o -name 'php-cgi*' -o -name 'php-fpm*' -o -name 'libphp*.so*' \
      -o -name 'frankenphp*' \) -print)"
    if [ -n "$php_files" ]; then
      printf 'Unexpected PHP runtime files:\n%s\n' "$php_files" >&2
      exit 1
    fi
  fi
done

printf '%s\n' 'PASS: no PHP commands, installed PHP packages or matching runtime files detected.'
