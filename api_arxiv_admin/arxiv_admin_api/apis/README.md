# API Client Generation

This directory contains generated API clients for external services.

## ModAPI Client

The ModAPI client is generated from the OpenAPI specification at `https://services.dev.arxiv.org/openapi.json` using `openapi-generator-cli`.

### Regenerating the ModAPI Client

To regenerate the ModAPI client (for example, when the API specification is updated):

**Use the automated script:**
```bash
./modapi-gen.sh
```

**Or manually:**

1. **Activate the virtual environment:**
   ```bash
   cd /path/to/api_arxiv_admin
   source venv/bin/activate
   ```

2. **Generate the new client:**
   ```bash
   openapi-generator-cli generate \
       -i https://services.dev.arxiv.org/openapi.json \
       -g python \
       -o ./arxiv_admin_api/apis/modapi \
       --package-name modapi_client \
       --additional-properties=packageName=modapi_client,projectName=modapi-client,removeOperationIdPrefix=true,useOneOfDiscriminatorLookup=false,disallowAdditionalPropsIfNotPresent=false,packageUrl=,generateSourceCodeOnly=true \
       --skip-validate-spec
   ```

### Features

- **Automatic import fixing**: The generation script automatically updates imports to work within the project structure
- **Operation ID prefix removal**: Removes common prefixes like `change_status_` from function names
- **Source-only generation**: Only generates source code without standalone project files
- **Project integration**: Generated code uses correct import paths for integration

### Generated Structure

The generated client will have the following structure:
```
modapi/
├── modapi_client/
│   ├── api/           # API classes organized by tags (e.g., debugging_api.py)
│   ├── models/        # Pydantic data models
│   ├── api_client.py  # Main API client class
│   ├── configuration.py  # Client configuration
│   ├── rest.py        # REST utilities
│   └── __init__.py    # Package initialization
```

### Usage

The client can be used in business logic modules like `biz/modapi_clear_user_cache.py`:

```python
from ..apis.modapi.modapi_client.api_client import ApiClient
from ..apis.modapi.modapi_client.api.debugging_api import DebuggingApi
from ..apis.modapi.modapi_client.configuration import Configuration

# Create client
config = Configuration(host="https://services.dev.arxiv.org")
api_client = ApiClient(configuration=config)
debugging_api = DebuggingApi(api_client=api_client)

# Use API
result = debugging_api.debug_clear_stored_user_debug_clear_stored_user_get(
    clear_user_id=user_id,
    authorization="Bearer token",
    modkey="key"
)
```

### Configuration

The generation uses `modapi_config.yaml` (legacy, now replaced by command-line options) and includes:
- Package naming overrides
- Operation ID transformations
- Import path corrections

### Notes

- **Import fixing**: The script automatically converts `from modapi_client` imports to use the full project path
- **Validation skipping**: Uses `--skip-validate-spec` due to duplicate operation IDs in the source API
- **GitHub cleanup**: Automatically removes generated `.github` directory
- **Authentication**: Handled via function parameters rather than global configuration