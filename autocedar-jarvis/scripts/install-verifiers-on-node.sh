#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

load_config "${1:-}"
require_slurm_job
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

for command_name in curl sha256sum unzip; do
  command -v "$command_name" >/dev/null 2>&1 || fail \
    "$command_name is required. Ask the lab administrator how to load/install it on Jarvis."
done

if ! command -v cargo >/dev/null 2>&1; then
  printf 'Installing Rust in %s/.cargo...\n' "$HOME"
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi
if [[ -f "$HOME/.cargo/env" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/.cargo/env"
fi

CEDAR="$HOME/.cargo/bin/cedar"
if [[ ! -x "$CEDAR" ]] || ! "$CEDAR" symcc --help 2>&1 | grep -q -- '--principal-type'; then
  printf 'Installing Cedar CLI 4.10.0 with symbolic analysis...\n'
  cargo install cedar-policy-cli \
    --locked \
    --version 4.10.0 \
    --features analyze \
    --force
else
  printf 'Cedar with symbolic analysis is already installed.\n'
fi

CVC5_VERSION="1.3.4"
CVC5_SHA256="dcdbfada0ce493ee98259c0816e0daafc561c223aadb3af298c2968e73ea39c6"
CVC5="$HOME/.local/bin/cvc5"
if [[ ! -x "$CVC5" ]]; then
  [[ "$(uname -s)" == "Linux" && "$(uname -m)" == "x86_64" ]] || fail \
    "The bundled CVC5 installer expects Linux x86_64. Ask the administrator for the correct binary."
  mkdir -p "$HOME/.local/bin" "$HOME/.local/opt"
  archive="$HOME/.local/opt/cvc5-$CVC5_VERSION.zip"
  printf 'Downloading CVC5 %s...\n' "$CVC5_VERSION"
  curl -fL \
    -o "$archive" \
    "https://github.com/cvc5/cvc5/releases/download/cvc5-$CVC5_VERSION/cvc5-Linux-x86_64-static.zip"
  printf '%s  %s\n' "$CVC5_SHA256" "$archive" | sha256sum --check --status || fail \
    "CVC5 archive checksum did not match; remove $archive and retry."
  unzip -q -o "$archive" -d "$HOME/.local/opt"
  ln -sfn \
    "$HOME/.local/opt/cvc5-Linux-x86_64-static/bin/cvc5" \
    "$CVC5"
else
  printf 'CVC5 is already installed.\n'
fi

"$CEDAR" --version
"$CEDAR" symcc --help | grep -- '--principal-type'
"$CVC5" --version
printf 'Verifier installation finished.\n'
