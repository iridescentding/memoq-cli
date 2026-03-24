# memoQ CLI

A command-line tool for managing memoQ Server - handle projects, files, translation memories (TM), terminology bases (TB), and project templates from your terminal.

## Table of Contents

- [What You Need](#what-you-need)
- [Installation (Step by Step)](#installation-step-by-step)
- [Quick Start](#quick-start)
- [Commands Reference](#commands-reference)
- [Troubleshooting](#troubleshooting)

---

## What You Need

Before installing, make sure you have:

1. **Python 3.9 or higher** - Check by running:
   ```bash
   python3 --version
   ```
   If not installed, download from [python.org](https://www.python.org/downloads/)

2. **uv** (recommended) or **pip** - Package installer
   - Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Or use pip (comes with Python)

3. **memoQ Server access** - You need:
   - Server URL (e.g., `https://memoq.yourcompany.com`)
   - API Key (get from your memoQ administrator)

---

## Installation (Step by Step)

### Step 1: Download the project

```bash
# Option A: Clone with git
git clone https://github.com/your-org/memoq-cli.git

# Option B: Or download and extract the ZIP file
```

### Step 2: Open terminal and go to project folder

```bash
cd memoq-cli
```

### Step 3: Create virtual environment and install

**Using uv (Recommended - faster):**
```bash
# Create virtual environment
uv venv

# Install the tool
uv pip install -e .
```

**Using pip:**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
# On Mac/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install the tool
pip install -e .
```

### Step 4: Verify installation

```bash
# Using the virtual environment
.venv/bin/memoq --version

# Or if activated:
memoq --version
```

You should see: `memoq-cli, version 1.0.0`

---

## Quick Start

### 1. Create configuration file

Run the setup wizard:

```bash
.venv/bin/python -m memoq_cli.cli init
```

It will ask you for:
- **Server host**: Your memoQ server URL (e.g., `https://memoq.datalsp.com`)
- **WSAPI port**: e.g., `8081`
- **RSAPI port**: e.g., `8082`
- **RSAPI path**: Usually `memoqserverhttpapi/v1`
- **API Key**: Your secret key (will be hidden when typing)

This creates a `config.json` file in your current folder.

> **Note**: Due to path issues, it's recommended to use `python -m memoq_cli.cli` instead of `.venv/bin/memoq` directly.

### 2. Test the connection

```bash
.venv/bin/python -m memoq_cli.cli test
```

If successful, you'll see:
```
Connection Test

WSAPI: https://memoq.datalsp.com:8081/memoqservices
  OK: WSDL loaded, services: ['ServerProjectService']
RSAPI: https://memoq.datalsp.com:8082/memoqserverhttpapi/v1
  OK: RSAPI reachable (HTTP 404)
```

### 3. List your projects

```bash
.venv/bin/python -m memoq_cli.cli project list
```

### 4. Common tasks

```bash
# Alias for convenience (add to your shell profile)
alias memoq='.venv/bin/python -m memoq_cli.cli'

# List translation memories
memoq tm list

# List terminology bases
memoq tb list

# List project templates
memoq template list

# Get help for any command
memoq --help
memoq project --help
memoq tm --help
```

---

## Commands Reference

### Overview

| Command | Description |
|---------|-------------|
| `memoq init` | Create configuration file |
| `memoq test` | Test server connection |
| `memoq config` | View/edit configuration |
| `memoq project` | Manage projects, users, and document assignments |
| `memoq file` | Upload/download files |
| `memoq tm` | Manage Translation Memories |
| `memoq tb` | Manage Terminology Bases |
| `memoq template` | Browse project templates |

### Project Commands

```bash
# List all projects
memoq project list

# Filter projects by name
memoq project list -f "client name"

# Include archived projects
memoq project list -a

# Limit results
memoq project list -n 10

# Output as JSON
memoq project list --json

# Get project details
memoq project info <PROJECT_GUID>

# List documents in a project
memoq project docs <PROJECT_GUID>

# Show document status
memoq project docs <PROJECT_GUID> -s

# Get project statistics
memoq project stats <PROJECT_GUID>
```

#### Project User Management

```bash
# List users assigned to a project
memoq project users <PROJECT_GUID>

# Interactively assign a user to a project
# (prompts for user selection and role: Project Manager, Member, Terminologist)
memoq project users assign <PROJECT_GUID>
```

#### Document User Assignment

```bash
# List document-user assignments in a table
memoq project docs userassign <PROJECT_GUID>

# Interactively assign a user to a document
# (prompts for document, user, role, and deadline)
memoq project docs assign <PROJECT_GUID>
```

### File Commands

```bash
# Upload a single file
memoq file upload <PROJECT_GUID> -p ./document.docx

# Upload a ZIP file (extracts and imports all files)
memoq file upload <PROJECT_GUID> -p ./files.zip -t zip

# Upload entire folder
memoq file upload <PROJECT_GUID> -p ./folder -t dir

# Specify target language(s)
memoq file upload <PROJECT_GUID> -p ./doc.docx -l zh-CN

# Download all files from project
memoq file download <PROJECT_GUID> -o ./downloads

# Download a specific document
memoq file download <PROJECT_GUID> -d <DOC_GUID> -o ./downloads

# Download as XLIFF format
memoq file download <PROJECT_GUID> -f xliff -o ./xliff

# Import translated XLIFF back
memoq file import-xliff <PROJECT_GUID> -p ./translated.xliff
```

### TM (Translation Memory) Commands

```bash
# List all TMs
memoq tm list

# Filter by name and language
memoq tm list -f "project" -s en-US -t zh-CN

# Get TM details
memoq tm info <TM_GUID>

# Create new TM
memoq tm create -n "My TM" -s en-US -t zh-CN

# Import TMX file
memoq tm import <TM_GUID> -p ./memory.tmx

# Export TM to TMX
memoq tm export <TM_GUID> -o ./exported.tmx

# Search TM (with custom threshold)
memoq tm search <TM_GUID> "search text" -t 80

# Delete TM (careful!)
memoq tm delete <TM_GUID>
```

### TB (Terminology Base) Commands

```bash
# List all TBs
memoq tb list

# Get TB details
memoq tb info <TB_GUID>

# Create new TB
memoq tb create -n "My TB" -l en-US -l zh-CN

# Add a term
memoq tb add <TB_GUID> -t "en-US:computer" -t "zh-CN:电脑"

# Add a term with definition and domain
memoq tb add <TB_GUID> -t "en-US:RAM" -t "zh-CN:内存" -d "Random Access Memory" --domain "IT"

# Search TB
memoq tb search <TB_GUID> "computer"

# Import CSV
memoq tb import <TB_GUID> -p ./terms.csv

# Export to CSV
memoq tb export <TB_GUID> -o ./terms.csv

# Delete TB (careful!)
memoq tb delete <TB_GUID>
```

### Template Commands

```bash
# List all project templates
memoq template list

# Filter by name
memoq template list -f "standard"

# Get template details
memoq template info <TEMPLATE_GUID>

# Output as JSON
memoq template list --json
```

### Global Options

```bash
# Use specific config file
memoq -c /path/to/config.json project list

# Verbose output (show debug info)
memoq -v project list

# Quiet mode (errors only)
memoq -q project list

# Enable SOAP debug logging (logs raw SOAP XML request/response)
memoq --soap-debug project list

# Show version
memoq --version

# Show help
memoq --help
```

---

## Configuration

### Config File Location

The tool looks for `config.json` in these locations (in order):
1. Current folder: `./config.json`
2. Home folder: `~/.memoq/config.json`
3. Config folder: `~/.config/memoq/config.json`

### View Current Config

```bash
memoq config --show
```

### Edit Config

```bash
# Change server host
memoq config --set server.host https://new-server.com

# Get a specific value
memoq config --get server.host
```

### Config File Format

```json
{
    "server": {
        "host": "https://memoq.datalsp.com",
        "wsapi_port": 8081,
        "rsapi_port": 8082,
        "rsapi_base": "memoqserverhttpapi/v1"
    },
    "auth": {
        "api_key": "your-api-key-here",
        "username": "",
        "password": ""
    },
    "export": {
        "default_path": "./exports",
        "xliff_version": "1.2"
    },
    "import": {
        "default_path": "./imports",
        "filter_system_files": true
    },
    "logging": {
        "level": "INFO",
        "log_file": "memoq_cli.log"
    }
}
```

---

## Troubleshooting

### "Config file not found"

**Problem:** You see "Warning: Config file not found"

**Solution:** Run `memoq init` to create a config file first.

### "Connection refused" or "Connection timeout"

**Problem:** Cannot connect to server

**Solutions:**
1. Check server URL is correct
2. Check port numbers (WSAPI usually 8080, RSAPI usually 443)
3. Make sure you can access the server from your network
4. Ask your IT admin if there's a firewall blocking access

### "401 Unauthorized" or "Authentication failed"

**Problem:** API Key is rejected

**Solutions:**
1. Check your API Key is correct in config.json
2. Ask your memoQ admin to verify the API Key is valid
3. Check the API Key has proper permissions

### "Module not found" errors

**Problem:** Python can't find required packages

**Solution:** Make sure you installed the dependencies:
```bash
cd memoq-cli
uv pip install -e .
# or
pip install -e .
```

### Command not found: memoq

**Problem:** The `memoq` command doesn't work

**Solutions:**
1. Use the full path: `.venv/bin/memoq`
2. Or activate the virtual environment first:
   ```bash
   source .venv/bin/activate
   memoq --help
   ```

---

## Tips for Beginners

### What is a GUID?

A GUID (Globally Unique Identifier) looks like this:
```
a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

You'll need GUIDs to identify projects, documents, TMs, and TBs. Get them by listing items first:
```bash
memoq project list
# Copy the GUID from the output
```

### What is WSAPI vs RSAPI?

- **WSAPI** (Web Service API): SOAP-based API used for projects, files, and templates
- **RSAPI** (REST API): REST-based API used for TMs and TBs

You don't need to worry about this - the tool handles it automatically. Use the `--soap-debug` flag if you need to inspect raw SOAP traffic for debugging.

### Quick Workflow Example

```bash
# 1. List projects to find GUID
memoq project list

# 2. Upload files to a project
memoq file upload a1b2c3d4-... -p ./my-documents -t dir

# 3. Assign users to documents
memoq project docs assign a1b2c3d4-...

# 4. Check assignment status
memoq project docs userassign a1b2c3d4-...

# 5. When translation is done, download files
memoq file download a1b2c3d4-... -o ./translated

# 6. Or export as XLIFF for review
memoq file download a1b2c3d4-... -f xliff -o ./for-review
```

---

## Getting Help

- Run `memoq --help` for general help
- Run `memoq <command> --help` for command-specific help
- Check the [Issues](https://github.com/your-org/memoq-cli/issues) page for known problems

---

## License

MIT License
