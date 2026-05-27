#!/usr/bin/env bash
# =============================================================================
# setup-drive-link.sh — DEPRECATED SHIM
# =============================================================================
# This script is now a thin wrapper around scripts/setup-cloud-link.sh which
# replaces it with a multi-provider (Google Drive / iCloud / Dropbox / OneDrive)
# version and also handles raw/ linkage.
#
# All existing flags (--status, --unlink, --path) are passed through.
#
# New canonical command:
#   bash scripts/setup-cloud-link.sh
#
# This shim will remain for backward compatibility.
# =============================================================================

echo "note: setup-drive-link.sh is now a shim → setup-cloud-link.sh --drive-only" >&2
exec bash "$(dirname "$0")/setup-cloud-link.sh" --drive-only "$@"
