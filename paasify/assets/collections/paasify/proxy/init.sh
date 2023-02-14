#!/bin/bash

install_mkcert ()
{
  local url=https://github.com/FiloSottile/mkcert/releases/download/v1.4.3/mkcert-v1.4.3-linux-amd64
  local file=${url##*/}

  if [[ -f mkcert ]]; then
    MKCERT=$PWD/mkcert
    return
  fi
  if command -v mkcert >&/dev/null; then
    MKCERT=$(command -v mkcert)
    return
  fi

  # Install mkcert in PWD
  wget "$url"
  mv "$file" mkcert
  chmod +x mkcert
}

gen_certs ()
{
  install_mkcert
  DOMAIN1="domain1.org"
  DOMAIN2="domain2.org"
  SUBDOMAINS=$( echo {infra,paas,apps,iaas,dev,cloud,lab,adm,sv,mgmt}.$DOMAIN1 {infra,paas,apps,iaas,dev,cloud,lab,adm,sv,mgmt}.$DOMAIN2 )
  DOMAIN=$DOMAIN1

  echo $MKCERT "$DOMAIN" "*.$DOMAIN" $SUBDOMAINS
  (
    cd config/
    $MKCERT "$DOMAIN" "*.$DOMAIN" $SUBDOMAINS
  )
  echo "INFO: Certificates has bee generated."
  tree config

}

gen_htpassword ()
{
  CONFIG="admin:admin"
  local dst="./config/htpasswd"
  set -x

  while IFS=: read -r user pass; do
    ! grep -sq "^$user:" $dst  >&/dev/null || continue
    echo "Add: $user to $dst"
    printf "$user:$(openssl passwd -apr1 $pass)\n" >> "$dst"
  done <<< "$CONFIG"
}

main ()
{
  gen_certs
  gen_htpassword
}

main
