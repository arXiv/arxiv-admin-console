#!/bin/bash

# ModAPI Client Generation Script
# Generates a Python client from the ModAPI OpenAPI specification
# Configured for integration into existing project (not standalone)

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/modapi"
API_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔧 Activating virtual environment..."
source "$API_ROOT/venv/bin/activate"

echo "🧹 Cleaning up existing generated code..."
rm -rf "$OUTPUT_DIR"/*

echo "🚀 Generating ModAPI client..."
openapi-generator-cli generate \
  -i https://services.dev.arxiv.org/openapi.json \
  -g python \
  -o "$OUTPUT_DIR" \
  --package-name modapi_client \
  --additional-properties=packageName=modapi_client,projectName=modapi-client,removeOperationIdPrefix=true,useOneOfDiscriminatorLookup=false,disallowAdditionalPropsIfNotPresent=false,packageUrl=,generateSourceCodeOnly=true \
  --skip-validate-spec

echo "🔧 Fixing imports for project integration..."

# Fix imports in all Python files
find "$OUTPUT_DIR" -name "*.py" -type f -exec sed -i 's/from modapi_client\./from arxiv_admin_api.apis.modapi.modapi_client./g' {} \;
find "$OUTPUT_DIR" -name "*.py" -type f -exec sed -i 's/import modapi_client\./import arxiv_admin_api.apis.modapi.modapi_client./g' {} \;
find "$OUTPUT_DIR" -name "*.py" -type f -exec sed -i 's/from modapi_client import/from arxiv_admin_api.apis.modapi.modapi_client import/g' {} \;
find "$OUTPUT_DIR" -name "*.py" -type f -exec sed -i 's/import modapi_client$/import arxiv_admin_api.apis.modapi.modapi_client/g' {} \;

rm -fr modapi/.github

echo "✅ ModAPI client generated successfully in $OUTPUT_DIR"
echo "💡 The generated code is configured for integration into your existing project."
