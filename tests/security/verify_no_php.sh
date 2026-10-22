#!/bin/sh
# GitHub-hosted runner only. Never start Docker Desktop for this check.
set -eu
script_directory="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

if [ "${1:-}" = '--self-test' ]; then
  image="${2:?Provide the image for the bounded detector self-test}"
  if output="$(docker run --rm --interactive --network none --read-only \
    --cap-drop ALL --security-opt no-new-privileges:true --user 65534:65534 \
    --tmpfs /tmp:rw,exec,nosuid,size=1m --entrypoint /bin/sh "$image" \
    -ec 'printf "#!/bin/sh\nexit 0\n" > /tmp/php; chmod 755 /tmp/php; export PATH="/tmp:$PATH"; exec /bin/sh -s' \
    < "$script_directory/check_no_php.sh" 2>&1)"; then
    printf '%s\n' 'ERROR: detector accepted the intentional PHP command marker.' >&2
    exit 1
  fi
  printf '%s\n' "$output"
  printf '%s\n' "$output" | grep -F 'Unexpected PHP executable: php' >/dev/null
  printf '%s\n' 'PASS: intentional PHP command marker was refused; disposable container removed.'
  exit 0
fi

if [ "$#" -eq 0 ]; then
  printf '%s\n' 'Provide at least one locally available image to assess.' >&2
  exit 1
fi
for image in "$@"; do
  printf 'Assessing image: %s\n' "$image"
  docker image inspect --format 'Image ID: {{.Id}}; repository digests: {{json .RepoDigests}}' "$image"
  docker run --rm --interactive --network none --read-only --cap-drop ALL \
    --security-opt no-new-privileges:true --user 65534:65534 \
    --entrypoint /bin/sh "$image" -s < "$script_directory/check_no_php.sh"
done
