# memoQ CLI

A command-line tool for managing memoQ Server - handle projects, files, translation memories (TM), terminology bases (TB), project templates, and light resources from your terminal.

## Table of Contents

- [For AI Agents / Programmatic Use](#for-ai-agents--programmatic-use)
- [Runtime & Server Sizing](#runtime--server-sizing)
- [What You Need](#what-you-need)
- [Installation (Step by Step)](#installation-step-by-step)
- [Quick Start](#quick-start)
- [Commands Reference](#commands-reference)
- [Troubleshooting](#troubleshooting)

---

## For AI Agents / Programmatic Use

This CLI is a thin local client over memoQ Server's WSAPI (SOAP) and RSAPI
(REST). An agent should treat it as a shell-invoked JSON tool.

### Invocation contract

- **Entry point:** `python -m memoq_cli.cli <group> <command> [args]`
  (or the `memoq` console script if on `PATH`).
- **Config discovery order:** `-c <path>` → `./config.json` → `~/.memoq/config.json` → `~/.config/memoq/config.json`.
  Set `-c` explicitly in automation to avoid ambiguity.
- **Machine output:** pass `--json` on any read command to get a raw dict/list
  on stdout. Without `--json`, output is human-formatted tables/text.
- **Exit codes:** `0` on success, non-zero on error. Human-readable errors go
  to stderr; use `-v` for tracebacks, `-q` to suppress info logs,
  `--soap-debug` to dump raw SOAP XML (noisy, for debugging only).
- **Idempotency:** `list` / `info` / `search` / `lookup` / `export` /
  `download` / `stats` are safe to retry. `create` / `delete` /
  `import` / `assign` / `upload` / `entry-*` mutate server state.
- **Destructive commands** (`tm delete`, `tb delete`, `entry-delete`) prompt
  by default; pass `-y` to skip in automation.

### Minimal automation recipe

```bash
# 1. Point at an explicit config
export MEMOQ="python -m memoq_cli.cli -c ./config.json"

# 2. Discover GUIDs as JSON
$MEMOQ project list --json          # -> list of {Guid, Name, ...}
$MEMOQ tm list --json
$MEMOQ tb list --json
$MEMOQ template list --json

# 3. Drive per-object commands with those GUIDs
$MEMOQ project docs <PROJECT_GUID> -d --json
$MEMOQ project stats <PROJECT_GUID> -F CSV_MemoQ --json
$MEMOQ tm search <TM_GUID> "text" -t 80 --json
```

### Command surface (one line each)

| Group | Commands |
|-------|----------|
| top-level | `init`, `test`, `config`, `--version` |
| `project` | `list`, `info`, `update`, `stats`, `users`, `users assign`, `docs`, `docs detailed`, `docs stats`, `docs assign`, `docs userassign` |
| `file` | `upload`, `download`, `import-xliff` |
| `tm` | `list`, `info`, `create`, `delete`, `import`, `export`, `search`, `concordance`, `lookup`, `metascheme`, `entry`, `entry-add`, `entry-update`, `entry-delete` |
| `tb` | `list`, `info`, `create`, `delete`, `add`, `search`, `lookup`, `metadefs`, `import`, `export`, `entry`, `entry-update`, `entry-delete`, `entry-meta`, `language-meta`, `term-meta` |
| `template` | `list`, `info` |
| `resource` | `listall`, `importnewfilter` |

Run any command with `--help` to get flags; most read commands accept `--json`,
most list commands accept `-f <name-filter>` and `-n <limit>`.

### Agent guardrails

- Always call `memoq test` once before a batch run — it validates WSAPI/RSAPI
  reachability and credentials cheaply.
- Server calls are network-bound; expect seconds-to-minutes for `project stats`,
  `file upload -t dir/zip`, and `tm import`/`export`. Budget timeouts ≥ 5 min
  for those.
- Language codes are memoQ-style (`eng`, `zho-CN`, `kor`, `de-DE`) — not
  ISO-639-1. Pull them from `project info` / `tm list` output rather than
  guessing.
- Treat GUIDs as opaque; never construct them.

---

## Runtime & Server Sizing

**Short answer:** this CLI is a client, not a server. Any modern small VM or
container that can run Python 3.9+ is sufficient. The heavy lifting happens on
the memoQ Server you point it at.

### If an AI runs this CLI in a sandbox/VM

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 512 MB | 1–2 GB (WSDL parsing + large XLIFF/TMX transfers use transient memory) |
| Disk | 300 MB (venv + deps) | 2–10 GB (working space for uploads/downloads, TMX/XLIFF exports) |
| Network | outbound HTTPS to memoQ Server on WSAPI/RSAPI ports (commonly 8080/8081/8082) | low-latency link to the memoQ Server; throughput matters for bulk file/TM transfers |
| OS | Linux/macOS/Windows | Linux container (Debian/Ubuntu slim, Alpine works with glibc variant) |
| Python | 3.9 | 3.11 |

Typical AWS/GCP/Azure equivalents: **t3.micro / e2-small / B1s** is enough
for interactive agent use; step up to **t3.small–medium** if the agent does
concurrent bulk TM/TMX imports or multi-GB file transfers.

### What actually drives load

- **SOAP WSDL parse** on first WSAPI call (one-off ~50–100 MB peak).
- **File/TM/TB transfers** stream through local disk; size your `/tmp` or
  working dir to ≥ the largest bundle you expect (typical: 100 MB–2 GB).
- **`project stats`** is server-side work on memoQ; the client just waits.
- No persistent daemon, no background workers, no database locally.

### What the memoQ Server needs

Out of scope for this repo — follow Kilgray/memoQ's official sizing guidance.
This CLI adds negligible load (one authenticated SOAP/REST session per
command invocation).

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
- **Server host**: Your memoQ server URL (e.g., `https://your-memoq-server.example.com`)
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

WSAPI: https://your-memoq-server.example.com:8081/memoqservices
  OK: WSDL loaded, services: ['ServerProjectService']
RSAPI: https://your-memoq-server.example.com:8082/memoqserverhttpapi/v1
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
| `memoq resource` | Light Resource Service (import filters, list all resources) |

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

# Show detailed document info with assignments (uses ListProjectTranslationDocuments2)
memoq project docs <PROJECT_GUID> -d
memoq project docs detailed <PROJECT_GUID>

# Detailed view without assignment info (faster)
memoq project docs detailed <PROJECT_GUID> -n

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
memoq tm list -f "project" -s eng -t zho-CN

# Get TM details
memoq tm info <TM_GUID>

# Create new TM
memoq tm create -n "My TM" -s eng -t zho-CN

# Delete TM (asks for confirmation)
memoq tm delete <TM_GUID>
memoq tm delete <TM_GUID> -y    # skip confirmation

# Import TMX file
memoq tm import <TM_GUID> -p ./memory.tmx

# Export TM to TMX
memoq tm export <TM_GUID> -o ./exported.tmx

# Search TM (with custom threshold, default 75%)
memoq tm search <TM_GUID> "search text"
memoq tm search <TM_GUID> "search text" -t 80

# Concordance search
memoq tm concordance <TM_GUID> "search term"
memoq tm concordance <TM_GUID> term1 term2    # multiple terms

# Lookup segments (auto-wraps plain text in <seg> tags)
memoq tm lookup <TM_GUID> "Hello world"
memoq tm lookup <TM_GUID> "segment 1" "segment 2"

# Get custom metadata scheme
memoq tm metascheme <TM_GUID>

# Entry operations
memoq tm entry <TM_GUID> <ENTRY_ID>                         # get entry
memoq tm entry-add <TM_GUID> -s "Hello" -t "你好"            # add entry
memoq tm entry-add <TM_GUID> -s "Hello" -t "你好" -m "user"  # with modifier
memoq tm entry-update <TM_GUID> <ENTRY_ID> -s "Hi" -t "你好" # update entry
memoq tm entry-delete <TM_GUID> <ENTRY_ID>                   # delete entry
```

### TB (Terminology Base) Commands

```bash
# List all TBs
memoq tb list
memoq tb list -f "project"    # filter by name

# Get TB details
memoq tb info <TB_GUID>

# Create new TB (multi-language)
memoq tb create -n "My TB" -l zho-CN -l eng

# Delete TB (asks for confirmation)
memoq tb delete <TB_GUID>
memoq tb delete <TB_GUID> -y    # skip confirmation

# Add a term entry
memoq tb add <TB_GUID> -t "eng:computer" -t "zho-CN:电脑"
memoq tb add <TB_GUID> -t "eng:RAM" -t "zho-CN:内存" -d "Random Access Memory" --domain "IT"

# Search TB (requires target language)
memoq tb search <TB_GUID> "Attack" -t eng
memoq tb search <TB_GUID> "攻击" -t zho-CN
memoq tb search <TB_GUID> "Attack" -t eng -c exact    # exact match
memoq tb search <TB_GUID> "Att" -t eng -c begins      # begins with

# Lookup terms in segments (requires source language)
memoq tb lookup <TB_GUID> "攻击测试" -s zho-CN -t eng
memoq tb lookup <TB_GUID> "seg1" "seg2" -s zho-CN     # multiple segments

# Get metadata definitions
memoq tb metadefs <TB_GUID>

# Import / Export
memoq tb import <TB_GUID> -p ./terms.csv
memoq tb export <TB_GUID> -o ./terms.csv

# Entry operations
memoq tb entry <TB_GUID> <ENTRY_ID>                             # get entry
memoq tb entry-update <TB_GUID> <ENTRY_ID> -t "eng:Attack"      # update terms
memoq tb entry-delete <TB_GUID> <ENTRY_ID>                      # delete entry

# Metadata operations (for custom metadata fields)
memoq tb entry-meta <TB_GUID> <ENTRY_ID> <META_NAME>              # get
memoq tb entry-meta <TB_GUID> <ENTRY_ID> <META_NAME> --set "val"  # set
memoq tb language-meta <TB_GUID> <ENTRY_ID> <META_NAME> -l eng    # language-level
memoq tb term-meta <TB_GUID> <ENTRY_ID> <META_NAME> --term-id 1   # term-level
```

### Template Commands

```bash
# List all project templates
memoq template list

# Filter by name (server-side filtering)
memoq template list -f "standard"

# Filter by language code
memoq template list --lang en-US

# Combine filters
memoq template list -f "translation" --lang de-DE

# Get template details
memoq template info <TEMPLATE_GUID>

# Output as JSON
memoq template list --json
```

### Resource Commands

Manage memoQ light resources (filter configs, MT settings, QA settings, etc.) via the Light Resource Service API.

```bash
# List all resources across all supported types
memoq resource listall

# List resources of a specific type only
memoq resource listall --type FilterConfigs
memoq resource listall --type QASettings
memoq resource listall --type MTSettings

# Output as JSON
memoq resource listall --json

# Import a filter config file as a new resource
memoq resource importnewfilter ./myfilter.xml

# Import with a custom name
memoq resource importnewfilter ./myfilter.xml --name "My Custom Filter"
```

**Supported resource types for `listall`:**

| Type | Description |
|------|-------------|
| `FilterConfigs` | File filter configurations |
| `FontSubstitution` | Font substitution rules |
| `IgnoreLists` | Spellcheck ignore lists |
| `MTSettings` | Machine translation settings |
| `PathRules` | Import path rules |
| `ProjectTemplate` | Project templates |
| `QASettings` | QA check settings |
| `SegRules` | Segmentation rules |

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
        "host": "https://your-memoq-server.example.com",
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
2. Check port numbers (WSAPI usually 8080, RSAPI usually 8082)
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
