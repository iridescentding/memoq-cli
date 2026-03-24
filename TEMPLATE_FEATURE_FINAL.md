# Project Template Feature - Final Implementation

## ✅ **WORKING SOLUTION**

Successfully implemented project template listing using **Light Resource Service API** based on official memoQ documentation.

## Results

```bash
$ memoq template list
Found 63 project template(s):

Name                                     GUID                                   Source
==================================================================================================
jerrytang-中译英 - 小牛机翻                  090d412f-4e12-46e4-b9b5-7bf3026cab4f   zho-CN
中译英项目模板示例 - 小牛机翻测试                1052c47b-39c7-4925-8e8c-6f3ca2123d32   zho-CN
One TM per client template               16000000-0000-0000-0000-00000973948b   N/A
...and 60 more templates
```

## Implementation Details

### API Used
**Light Resource Service** (WSAPI/SOAP)
- Documentation: https://docs.memoq.com/current/api-docs/wsapi/api/lightresourceservice/
- WSDL: `https://memoq.datalsp.com:8081/memoqservices/resource?wsdl`

### Key Methods

#### 1. ListResources
```python
ListResources(ResourceType resourceType, LightResourceListFilter filter)
```

**Usage:**
```python
client.service.ListResources('ProjectTemplate', None)
```

**Important:** Pass `'ProjectTemplate'` as a **string**, not an integer enum value.

#### 2. GetResourceInfo
```python
GetResourceInfo(ResourceType resourceType, Guid resourceGuid)
```

**Usage:**
```python
client.service.GetResourceInfo('ProjectTemplate', guid)
```

### Data Structure

Project templates returned have this structure:
```json
{
  "Description": null,
  "Guid": "090d412f-4e12-46e4-b9b5-7bf3026cab4f",
  "Name": "jerrytang-中译英 - 小牛机翻",  // ← "Name", not "FriendlyName"!
  "Readonly": false,
  "IsDefault": false,
  "SourceLangCode": "zho-CN",
  "TargetLangCodes": {
    "string": ["eng", "por-BR", "por"]  // ← Wrapped in "string" object
  }
}
```

**Key differences from other resources:**
- Uses `"Name"` instead of `"FriendlyName"`
- `TargetLangCodes` is `{"string": []}` not a direct array

## CLI Commands

### List All Templates
```bash
memoq template list
```

### Filter by Name
```bash
memoq template list --filter "Game"
```

### Limit Results
```bash
memoq template list --limit 10
```

### JSON Output
```bash
memoq template list --json
```

### Get Template Details
```bash
memoq template info <guid>
```

### Examples
```bash
# Find game-related templates
$ memoq template list --filter "Game"
Found 2 project template(s):
Name                                     GUID
====================================================================================================
01_售前演示_Game_zh_multilingual             4826c18f-3dba-4071-b1cf-a0c6287e6730
01_售前演示_Game_eng_multilingual            669166fd-8a1c-4763-ad3b-d21e5ab0412e

# Get detailed info
$ memoq template info 4826c18f-3dba-4071-b1cf-a0c6287e6730

Project Template Info:

  Name:        01_售前演示_Game_zh_multilingual
  GUID:        4826c18f-3dba-4071-b1cf-a0c6287e6730
  Source:      zho-CN
  Description: None
  Read-only:   False
  Is Default:  False
  Targets:     jpn, eng
```

## Implementation Files

### Core Implementation
- `memoq_cli/wsapi/project_template.py` - Template manager class
  - `list_templates()` - Lists all project templates
  - `get_template(guid)` - Gets specific template details
  - `print_template_list()` - Pretty-print template list
  - `print_template_details()` - Show detailed info

### CLI Commands
- `memoq_cli/commands/template.py` - CLI command implementation
  - `memoq template list` - List templates
  - `memoq template info <guid>` - Template details

### Tests
- `tests/wsapi/test_project_template.py` - Unit tests
- All 11 tests passing ✅

## Key Discoveries

### 1. Resource Type Parameter
Initially tried passing integer value `16` for `ProjectTemplate` enum:
```python
client.service.ListResources(16, None)  # ❌ Failed!
```

**Error:**
```
无法将无效的枚举值"16"反序列化为类型"MemoQServices.ResourceType"
```

**Solution:** Pass as string:
```python
client.service.ListResources('ProjectTemplate', None)  # ✅ Works!
```

### 2. Field Name Differences
Other resources use `"FriendlyName"`, but project templates use `"Name"`:
```python
# For TMs, TBs, etc.
tm.get("FriendlyName")  # ✅

# For Project Templates
template.get("Name")  # ✅
template.get("FriendlyName")  # ❌ Returns None
```

### 3. Target Languages Structure
```python
# Returned structure
{
  "TargetLangCodes": {
    "string": ["eng", "deu", "fra"]  # Array wrapped in "string" object
  }
}

# Access correctly
targets = template.get("TargetLangCodes", {})
if isinstance(targets, dict):
    target_list = targets.get("string", [])
```

## Testing

### Unit Tests
```bash
$ pytest tests/ -v
11 passed in 0.12s ✅
```

### Real Server Test
```bash
$ memoq template list
Found 63 project templates ✅
```

### Test Server
- Server: https://memoq.datalsp.com:8081
- API Key Authentication
- 63 templates available

## Configuration

### Default Settings (Updated)
```json
{
  "server": {
    "host": "https://memoq.datalsp.com",  // ✅ Default set
    "wsapi_port": 8081,                     // ✅ Corrected from 8080
    "rsapi_port": 8082                      // ✅ Corrected from 443
  },
  "auth": {
    "api_key": "your-api-key"
  }
}
```

### Initialize Config
```bash
$ memoq init
# Just press Enter to accept defaults
memoQ Server host [https://memoq.datalsp.com]:
WSAPI port [8081]:
RSAPI port [8082]:
```

## Why Other Approaches Failed

### 1. WSAPI Resource Service (Old Approach)
```python
# Old code
resources = client.service.ListResources()  # No parameters
templates = [r for r in resources if r.Type == "ServerProjectTemplate"]
```

**Problem:** Returns 0 resources on most servers

### 2. RSAPI (HTTP/REST API)
Tried endpoints:
- `/projecttemplates` ❌ 404
- `/resources` ❌ 404
- `/templates` ❌ 404

**Problem:** Project templates not available via RSAPI

### 3. Enum Integer Values
```python
client.service.ListResources(16, None)  # ProjectTemplate = 16
```

**Problem:** Server doesn't accept integer enum values, requires string

## Solution Architecture

```
User Command: memoq template list
           ↓
CLI (template.py)
           ↓
ProjectTemplateManager.list_templates()
           ↓
WSAPIClient.get_client("Resource")
           ↓
SOAP Call: ListResources('ProjectTemplate', None)
           ↓
memoQ Server Light Resource Service
           ↓
Returns 63 ProjectTemplate resources
           ↓
Display to user
```

## Documentation References

1. **Official memoQ API Docs:**
   - https://docs.memoq.com/current/api-docs/wsapi/
   - https://docs.memoq.com/current/api-docs/wsapi/api/lightresourceservice/

2. **IResourceService Interface:**
   - `ListResources(ResourceType, LightResourceListFilter)`
   - `GetResourceInfo(ResourceType, Guid)`

3. **ResourceType Enum:**
   - Value: `ProjectTemplate` (string)
   - Description: "Project template settings resource"

## Quick Start

### 1. Initialize
```bash
memoq init
# Press Enter to accept defaults
```

### 2. List Templates
```bash
memoq template list
```

### 3. Filter & Get Details
```bash
# Find specific templates
memoq template list --filter "Translation"

# Get GUID from list, then:
memoq template info <guid>
```

### 4. Use in Scripts
```bash
# Export as JSON for processing
memoq template list --json > templates.json

# Filter and extract GUIDs
memoq template list --filter "Game" --json | jq '.[].Guid'
```

## Summary

✅ **Working Implementation**
- 63 project templates successfully retrieved
- CLI commands fully functional
- All tests passing (11/11)
- Filtering, JSON output, detailed info all working

✅ **Correct API Usage**
- Light Resource Service API
- `ListResources('ProjectTemplate', None)`
- `GetResourceInfo('ProjectTemplate', guid)`

✅ **Production Ready**
- Error handling
- Unit tests
- Documentation
- Real server tested

**Command to use:**
```bash
memoq template list
```

This will display all project template names and GUIDs from your memoQ server! 🎉
