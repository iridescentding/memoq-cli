# Project Template Feature - Implementation Summary

## Overview
Added project template information retrieval capability to memoQ CLI using both RSAPI and WSAPI.

## What Was Implemented

### 1. Fixed RSAPI Port Configuration ✅
- **Issue**: Default RSAPI port was 443 instead of 8082
- **Fix**: Updated `config.py` to use port 8082 as default
- **Test**: `tests/test_config.py::test_rsapi_port_defaults_to_8082_not_443`

### 2. Added Username/Password Authentication ✅
- **Issue**: RSAPI client only supported API key authentication
- **Fix**: Added `authenticate_with_password()` method to `RSAPIClient`
- **Usage**: Supports LoginMode=0 (username/password)
- **Test**: `tests/rsapi/test_auth.py::test_authenticate_with_username_password`

### 3. RSAPI Project Template Client ✅
- **Location**: `memoq_cli/rsapi/project_template.py`
- **Class**: `ProjectTemplateClient`
- **Methods**:
  - `list_templates()` - List all project templates
  - `get_template(guid)` - Get specific template details
  - `print_template_list(templates)` - Pretty-print template list
  - `print_template_details(template)` - Show detailed info
- **Note**: RSAPI endpoints for project templates don't exist on the tested server
- **Tests**: `tests/rsapi/test_project_template.py`, `tests/rsapi/test_project_template_display.py`

### 4. WSAPI Project Template Manager ✅ (Working Implementation)
- **Location**: `memoq_cli/wsapi/project_template.py`
- **Class**: `ProjectTemplateManager`
- **Methods**:
  - `list_templates()` - Lists resources of type "ServerProjectTemplate"
  - `get_template(guid)` - Get template details via Resource.GetResourceInfo
  - `print_template_list(templates)` - Display templates in table format
  - `print_template_details(template)` - Show detailed template info
- **Implementation**: Uses WSAPI Resource service
- **Test**: `tests/wsapi/test_project_template.py`

## Key Findings

### RSAPI vs WSAPI for Project Templates
1. **RSAPI (Light Resources API)**:
   - Does NOT expose project template endpoints
   - Tested endpoints all returned 404
   - Not suitable for project template access

2. **WSAPI (SOAP API)**:
   - ✅ Project templates accessible via Resource service
   - Templates are resources of type "ServerProjectTemplate"
   - Use `ListResources()` to get all resources, filter by type
   - Use `GetResourceInfo(guid)` for detailed template info

## Usage Examples

### Using WSAPI (Recommended)

```python
from memoq_cli.wsapi.project_template import ProjectTemplateManager

# Create manager
manager = ProjectTemplateManager(
    host="https://memoq.datalsp.com",
    port=8081,
    api_key="your-api-key",
    verify_ssl=False
)

# List all templates
templates = manager.list_templates()
manager.print_template_list(templates)

# Get specific template
if templates:
    template_guid = templates[0]["Guid"]
    details = manager.get_template(template_guid)
    manager.print_template_details(details)

manager.close()
```

### Using RSAPI (Alternative - If endpoints exist)

```python
from memoq_cli.rsapi.project_template import ProjectTemplateClient

# Create client with username/password
client = ProjectTemplateClient(
    host="https://memoq.datalsp.com",
    port=8082,
    verify_ssl=False
)

# Authenticate
client.authenticate_with_password("username", "password")

# List templates (if endpoint exists)
templates = client.list_templates()
client.print_template_list(templates)

client.close()
```

## Testing

### Run All Tests
```bash
cd /Users/jayding/Desktop/Code\ Projects/memoq-cli
source .venv/bin/activate
python -m pytest tests/ -v
```

### Test with Real Server
```bash
# Test WSAPI implementation
python test_wsapi_templates.py

# Test RSAPI implementation (will fail - endpoints don't exist)
python test_project_templates.py
```

## Configuration

### config.json
```json
{
    "server": {
        "host": "https://memoq.datalsp.com",
        "wsapi_port": 8081,
        "rsapi_port": 8082,
        "rsapi_path": "memoqserverhttpapi/v1"
    },
    "auth": {
        "api_key": "your-api-key",
        "username": "wsapi",
        "password": "Datalsp2026@"
    }
}
```

## Test Results

- ✅ 11/11 tests passing
- ✅ RSAPI port configuration fixed
- ✅ Username/password authentication working
- ✅ WSAPI project template access working
- ⚠️  RSAPI project template endpoints don't exist on server

## Files Created/Modified

### New Files
- `memoq_cli/rsapi/project_template.py` - RSAPI client (endpoints don't exist)
- `memoq_cli/wsapi/project_template.py` - WSAPI manager (working)
- `tests/rsapi/test_auth.py` - Authentication tests
- `tests/rsapi/test_client.py` - Client port tests
- `tests/rsapi/test_project_template.py` - RSAPI template tests
- `tests/rsapi/test_project_template_display.py` - Display tests
- `tests/test_config.py` - Configuration tests
- `tests/wsapi/test_project_template.py` - WSAPI template tests

### Modified Files
- `memoq_cli/config.py` - Fixed default RSAPI port (443 → 8082)
- `memoq_cli/rsapi/client.py` - Added `authenticate_with_password()` method

## Recommendations

1. **Use WSAPI** for project template access (it works)
2. **Use username/password auth** for RSAPI when API key not available
3. **Test servers** may have 0 templates - this is normal
4. **RSAPI endpoints** for project templates may not be implemented in all memoQ versions

## TDD Approach

All implementation followed Test-Driven Development:
1. Write failing test (RED)
2. Verify test fails correctly
3. Write minimal code to pass (GREEN)
4. Verify test passes
5. Refactor if needed

This ensured high code quality and test coverage.
