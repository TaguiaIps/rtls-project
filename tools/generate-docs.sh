#!/usr/bin/env bash
set -euo pipefail

# generate-docs.sh — Build flat documentation from project markdown files.
# Produces both a single Markdown file and a PDF under docs/output/.
#
# Usage:
#   ./tools/generate-docs.sh          # generate both formats
#   ./tools/generate-docs.sh --md    # markdown only
#   ./tools/generate-docs.sh --pdf   # pdf only
#   ./tools/generate-docs.sh --clean # remove output directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"
OUTPUT_DIR="$DOCS_DIR/output"

# Markdown files to include in the flat documentation, in order.
# Excluded: ux-design.md (too large/specialized), runbook-mobile.md (operational),
# deployment-and-testing-plan.md (CI/CD process), tuya-gateway-analysis (hardware survey),
# rtls-guide.md (external reference material).
CHAPTERS=(
  "requirements-document.md"
  "technical-specification-document.md"
  "system-design.md"
  "auth-foundation.md"
  "spatial-admin-workflow.md"
  "deployment-strategy.md"
  "implementation-plan.md"
  "bootstrap-follow-on-decisions.md"
  "workspace-bootstrap.md"
)

generate_markdown() {
  echo "Generating flat markdown..."
  local output="$OUTPUT_DIR/rtls-platform-documentation.md"

  {
    echo "% RTLS Analytics Platform — Flat Documentation"
    echo "% Generated on $(date -u +%Y-%m-%d)"
    echo ""
    echo "# RTLS Analytics Platform — Flat Documentation"
    echo ""
    echo "> Generated from project documentation on $(date -u +%Y-%m-%d)."
    echo "> This document consolidates the core specifications, design, and operational"
    echo "> documentation for the RTLS Analytics Platform."
    echo ""
    echo "---"
    echo ""

    # Table of Contents
    echo "## Table of Contents"
    echo ""
    local idx=1
    for chapter in "${CHAPTERS[@]}"; do
      local title
      title=$(head -1 "$DOCS_DIR/$chapter" | sed 's/^#* //' | sed 's/\*//g' | sed 's/`//g')
      local slug
      slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
      echo "$idx. [$title](#$idx-$slug)"
      ((idx++))
    done
    echo ""

    # Append each chapter with a heading reset
    idx=1
    for chapter in "${CHAPTERS[@]}"; do
      local src="$DOCS_DIR/$chapter"
      local title
      title=$(head -1 "$src" | sed 's/^#* //' | sed 's/\*//g' | sed 's/`//g')
      local slug
      slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')

      echo "---"
      echo ""
      echo "<a id=\"$idx-$slug\"></a>"
      echo ""
      # Re-write chapter heading to avoid TOC collision
      echo "# $idx. $title"
      echo ""

      # Skip the first heading line of the source (already rendered above)
      tail -n +2 "$src"
      echo ""
      echo ""
      ((idx++))
    done
  } > "$output"

  echo "  -> $output"
}

generate_pdf() {
  echo "Generating PDF..."
  local md_src="$OUTPUT_DIR/rtls-platform-documentation.md"
  local pdf_out="$OUTPUT_DIR/rtls-platform-documentation.pdf"

  if [ ! -f "$md_src" ]; then
    echo "  Markdown source not found. Generate markdown first."
    exit 1
  fi

  pandoc "$md_src" \
    --pdf-engine=xelatex \
    --variable=geometry:margin=1in \
    --variable=fontsize=11pt \
    --variable=documentclass=article \
    --variable=colorlinks=true \
    --variable=linkcolor=blue \
    --variable=urlcolor=blue \
    --variable=toc=true \
    --variable=toc-depth=3 \
    --highlight-style=tango \
    -f markdown+tex_math_dollars+yaml_metadata_block \
    -o "$pdf_out"

  echo "  -> $pdf_out"
}

clean() {
  if [ -d "$OUTPUT_DIR" ]; then
    rm -rf "$OUTPUT_DIR"
    echo "Removed $OUTPUT_DIR"
  fi
}

main() {
  local mode="${1:-all}"

  case "$mode" in
    --md)
      mkdir -p "$OUTPUT_DIR"
      generate_markdown
      ;;
    --pdf)
      mkdir -p "$OUTPUT_DIR"
      generate_pdf
      ;;
    --clean)
      clean
      ;;
    all)
      mkdir -p "$OUTPUT_DIR"
      generate_markdown
      generate_pdf
      ;;
    *)
      echo "Usage: $0 [--md|--pdf|--clean]"
      exit 1
      ;;
  esac

  echo "Done."
}

main "$@"
