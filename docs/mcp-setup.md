# Antigravity ↔ n8n MCP Integration Setup

## Executive Summary
This document records the setup, verification, security, and tool capabilities of the Model Context Protocol (MCP) connection between the **Antigravity AI Agent** workspace and the **n8n Automation Instance** (`https://bharathkumar733.app.n8n.cloud`).

---

## 1. Connection Details & Status

| Attribute | Value |
| :--- | :--- |
| **Status** | **CONNECTED (SUCCESS)** |
| **Endpoint** | `https://bharathkumar733.app.n8n.cloud/mcp-server/http` |
| **Transport** | Server-Sent Events (SSE) / HTTP JSON-RPC |
| **Server Name** | `n8n MCP Server` |
| **Server Version** | `v1.1.0` |
| **Authentication** | Bearer JWT Token |
| **Configuration Path** | `.agents/mcp_config.json` |

---

## 2. Available MCP Tools (34 Discovered)

The connected n8n MCP server provides the following 34 tools for workflow discovery, inspection, validation, creation, and execution management:

### Workflow Discovery & Inspection (Read-Only)
* `search_workflows` - Search for workflows with optional filters; returns previews.
* `get_workflow_details` - Retrieve detailed information about a workflow including trigger details.
* `get_workflow_history` - List saved version history of a workflow (newest first).
* `get_workflow_version` - Retrieve full content (nodes, connections, node groups) of a specific version.

### Executions & Monitoring
* `search_executions` - Search workflow execution history with filters.
* `get_execution` - Retrieve execution logs and metadata by execution ID and workflow ID.

### Workflow SDK & Validation
* `get_sdk_reference` - Documentation reference for n8n Workflow SDK syntax and patterns.
* `get_workflow_best_practices` - Design guidance, recommended nodes, and common pitfalls by technique.
* `search_nodes` - Search available n8n nodes by service name, trigger type, or utility function.
* `get_node_types` - Fetch TypeScript type definitions and parameter schemas for n8n nodes.
* `explore_node_resources` - Resolve real values for dropdown resource locators or load options.
* `validate_node_config` - Validate individual node configurations before wiring into a graph.
* `validate_workflow` - Validate complete n8n Workflow SDK code before creation/updating.

### Workflow Management & Execution
* `create_workflow_from_code` - Create a new n8n workflow from validated SDK code.
* `update_workflow` - Atomically update nodes, parameters, connections, or settings of an existing workflow.
* `archive_workflow` - Archive a workflow by ID.
* `publish_workflow` - Publish/activate a workflow for production execution.
* `unpublish_workflow` - Unpublish/deactivate a workflow.
* `restore_workflow_version` - Restore a workflow to a previous historical version.
* `execute_workflow` - Trigger workflow execution by ID.
* `test_workflow` - Test a workflow using pin data.
* `prepare_test_pin_data` - Prepare test pin data for trigger and credential nodes.

### Instance & Project Management
* `list_credentials` - List accessible credential IDs.
* `list_n8n_connect_services` - List supported service nodes and credentials.
* `list_tags` - List workflow tags.
* `search_projects` - Search accessible project folders.
* `search_folders` - Search folders within a project.
* `search_data_tables` - Search n8n Data Tables.
* `create_data_table` - Create a new data table.
* `rename_data_table` - Rename a data table.
* `add_data_table_column` - Add a column to a data table.
* `delete_data_table_column` - Delete a column from a data table.
* `rename_data_table_column` - Rename a column in a data table.
* `add_data_table_rows` - Insert rows into a data table.

---

## 3. Verified Read Capabilities & Active Workflows

* **Read Verification Test**: `search_workflows` tool was executed against the instance.
* **Result**: Returned `count: 0` (0 active/exposed workflows on the connected n8n instance).
* **Existing Workflows Protection**: No existing workflows were modified, deleted, activated, or deactivated.

---

## 4. Capabilities Matrix

| Capability | Status | Tool(s) Used |
| :--- | :--- | :--- |
| **Workflow Read / Search** | **AVAILABLE** | `search_workflows`, `get_workflow_details` |
| **Execution Read / Logs** | **AVAILABLE** | `search_executions`, `get_execution` |
| **Workflow Creation** | **AVAILABLE** | `create_workflow_from_code` |
| **Workflow Update** | **AVAILABLE** | `update_workflow` |
| **Workflow Execution** | **AVAILABLE** | `execute_workflow`, `test_workflow` |
| **Workflow Deletion / Archiving** | **AVAILABLE** | `archive_workflow` |

---

## 5. Security & Isolation Considerations

1. **Credential Storage**: JWT Bearer token stored locally in `.agents/mcp_config.json`.
2. **Git Exclusion**: `.gitignore` configured to exclude `.agents/mcp_config.json` and `.env` files to prevent secret leakage into version control.
3. **Transport Security**: TLS encrypted HTTPS connection (`https://bharathkumar733.app.n8n.cloud`).
4. **Execution Policy**: No production modifications or executions performed during initial Phase 0 inspection.

---

## 6. Current Limitations

* **Exposed Workflows**: Currently 0 workflows are exposed on the n8n instance. If specific workflows need to be managed by Antigravity, ensure they are enabled under n8n **Settings > Instance-level MCP > Workflows exposed**.
