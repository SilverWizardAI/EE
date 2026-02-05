# Parent CC Protocol Specification

**Version:** 1.0.0
**Date:** 2026-02-05
**Status:** Active

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Protocol Direction](#protocol-direction)
4. [App → Parent CC (Assistance Requests)](#app--parent-cc-assistance-requests)
5. [Parent CC → App (Control Commands)](#parent-cc--app-control-commands)
6. [Data Formats](#data-formats)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)
9. [Examples](#examples)
10. [Implementation Guide](#implementation-guide)

---

## Overview

### What is the Parent CC Protocol?

The **Parent CC Protocol** is a bidirectional communication standard between Silver Wizard applications and their Parent CC (Claude Code instance). It enables:

- **Apps** to request intelligent assistance for complex decisions
- **Parent CC** to monitor and control application behavior
- **Reduced app complexity** by delegating edge cases to AI
- **Standardized communication** across all Silver Wizard products

### Key Innovation

**Traditional Architecture:**
```
App encounters edge case → Bloated app handles it → 2000+ line modules
```

**Parent CC Architecture:**
```
App encounters edge case → Ask Parent CC → Parent CC analyzes with full context → App follows guidance → Modules stay <400 lines
```

### Why This Matters

- **Reduces code bloat:** Apps delegate complexity instead of implementing it
- **Leverages AI intelligence:** Parent CC has full project context
- **Consistent decisions:** Same AI handles edge cases across all apps
- **Easier maintenance:** Fix logic once in Parent CC, all apps benefit

---

## Architecture

### Communication Flow

```
┌─────────────────────────────────────────────────────┐
│              Parent CC (Claude Code)                 │
│  - Full project context                             │
│  - Intelligent decision making                      │
│  - Error analysis & recovery                        │
│  - App lifecycle management                         │
└──────────────────┬──────────────────────────────────┘
                   │ (bidirectional via MM mesh)
                   ↓
         ┌─────────────────────┐
         │ Central Mesh Proxy  │
         │    (port 6001)      │
         └─────────────────────┘
                   ↕
         ┌─────────┴─────────┐
         ↓                   ↓
    ┌────────┐          ┌────────┐
    │ App 1  │ ←──────→ │ App 2  │
    │(simple)│   peer   │(simple)│
    └────────┘   comms  └────────┘
```

### Transport Layer

**Current:** MM (MCP Mesh) on port 6001
**Future:** Could support WebSocket, HTTP, or other transports

### Protocol Versions

- **v1.0.0:** Initial specification (this document)
- **Future:** Backward-compatible extensions

---

## Protocol Direction

### Two Communication Patterns

1. **App → Parent CC (Assistance Requests)**
   - Initiated by app when it needs help
   - Async request/response pattern
   - Optional timeouts and priorities

2. **Parent CC → App (Control Commands)**
   - Initiated by Parent CC for monitoring/control
   - Synchronous command/response pattern
   - Apps must respond within reasonable time

---

## App → Parent CC (Assistance Requests)

### Request Types

| Type | Purpose | When to Use |
|------|---------|-------------|
| `HELP` | General guidance | App doesn't know what to do |
| `PERMISSION` | Request approval | Before risky/destructive action |
| `ERROR_RECOVERY` | Recovery guidance | After unexpected error |
| `DATA_PROCESSING` | Process complex data | Data transformation too complex |
| `ANALYSIS` | Get insights | Need to understand data |
| `DECISION` | Choose between options | Multiple valid approaches |
| `VALIDATION` | Validate data/action | Need expert validation |

### 1. Request Help

**Use when:** App encounters situation it doesn't know how to handle.

**Request:**
```python
{
    "type": "HELP",
    "context": {
        "count": 150,
        "max_expected": 100,
        "operation": "data_import"
    },
    "question": "Count exceeded expected maximum. Should I continue?",
    "priority": "NORMAL"
}
```

**Response:**
```python
{
    "approved": true,
    "guidance": "Yes, continue. Counts above 100 are normal for large imports.
                 Monitor memory usage and add progress reporting.",
    "suggested_action": "continue_with_monitoring",
    "data": {
        "add_memory_check": true,
        "progress_interval": 50
    }
}
```

**Code Example:**
```python
response = protocol.request_help(
    context={"count": 150, "max_expected": 100},
    question="Count exceeded expected maximum. Should I continue?",
    priority=RequestPriority.NORMAL
)

if response.approved:
    logger.info(response.guidance)
    if response.data.get("add_memory_check"):
        enable_memory_monitoring()
```

---

### 2. Request Permission

**Use when:** App wants to perform potentially risky/destructive action.

**Request:**
```python
{
    "type": "PERMISSION",
    "context": {
        "action": "delete_old_files",
        "file_count": 500,
        "age_days": 90,
        "total_size_mb": 1200
    },
    "question": "Permission to delete_old_files?",
    "priority": "HIGH"
}
```

**Response:**
```python
{
    "approved": true,
    "reason": "Files are old enough (90+ days) and safe to delete.
               Total size is reasonable for cleanup.",
    "suggested_action": "proceed_with_backup",
    "data": {
        "create_backup": true,
        "backup_location": "/backups/cleanup_2026_02_05"
    }
}
```

**Code Example:**
```python
response = protocol.request_permission(
    action="delete_old_files",
    details={"file_count": 500, "age_days": 90}
)

if response.approved:
    if response.data.get("create_backup"):
        backup_files(response.data["backup_location"])
    delete_files()
else:
    logger.warning(f"Permission denied: {response.reason}")
```

---

### 3. Report Error

**Use when:** App encounters unexpected error and needs recovery guidance.

**Request:**
```python
{
    "type": "ERROR_RECOVERY",
    "context": {
        "error_type": "ConnectionError",
        "error_message": "Failed to connect to database",
        "operation": "save_user_data",
        "attempt": 1,
        "max_retries": 3
    },
    "question": "How should I recover from this error?",
    "priority": "HIGH"
}
```

**Response:**
```python
{
    "approved": true,
    "guidance": "Database connection failed. This is likely temporary.
                 Retry with exponential backoff.",
    "should_retry": true,
    "data": {
        "retry_delay_seconds": 2,
        "use_exponential_backoff": true,
        "fallback_action": "queue_for_later"
    }
}
```

**Code Example:**
```python
try:
    save_to_database(data)
except ConnectionError as e:
    response = protocol.report_error(
        error=e,
        context={"operation": "save_user_data", "attempt": 1}
    )

    if response.should_retry:
        delay = response.data.get("retry_delay_seconds", 1)
        time.sleep(delay)
        retry_operation()
    else:
        handle_failure(response.data.get("fallback_action"))
```

---

### 4. Request Data Processing

**Use when:** App needs complex data transformation it can't handle.

**Request:**
```python
{
    "type": "DATA_PROCESSING",
    "context": {
        "task": "parse_complex_email_thread",
        "data": {
            "raw_email": "...",
            "format": "nested_replies"
        }
    },
    "question": "Please parse this complex email thread"
}
```

**Response:**
```python
{
    "approved": true,
    "data": {
        "messages": [
            {"from": "user@example.com", "body": "...", "timestamp": "..."},
            {"from": "other@example.com", "body": "...", "timestamp": "..."}
        ],
        "thread_depth": 3,
        "participants": ["user@example.com", "other@example.com"]
    }
}
```

---

### 5. Request Analysis

**Use when:** App needs insights from data.

**Request:**
```python
{
    "type": "ANALYSIS",
    "context": {
        "data": {
            "response_times": [100, 150, 200, 5000, 120],
            "error_rate": 0.02,
            "throughput": 1000
        },
        "analysis_type": "performance"
    },
    "question": "Analyze this performance data"
}
```

**Response:**
```python
{
    "approved": true,
    "guidance": "Performance is generally good but there's an outlier (5000ms).
                 This suggests occasional blocking. Investigate slow queries.",
    "data": {
        "outliers": [5000],
        "avg_normal": 142.5,
        "recommendations": [
            "Add query timeout",
            "Monitor for blocking operations",
            "Consider connection pooling"
        ]
    }
}
```

---

### 6. Request Decision

**Use when:** App faces choice between multiple options.

**Request:**
```python
{
    "type": "DECISION",
    "context": {
        "data_size": "10GB",
        "query_complexity": "high",
        "concurrent_users": 50
    },
    "question": "Which database should I use?",
    "options": ["SQLite", "PostgreSQL", "MongoDB"]
}
```

**Response:**
```python
{
    "approved": true,
    "suggested_action": "PostgreSQL",
    "guidance": "PostgreSQL is best for this use case because:
                 - Handles 10GB data well
                 - Excellent support for complex queries
                 - Good concurrent user handling
                 SQLite would struggle with concurrency.
                 MongoDB better for unstructured data.",
    "data": {
        "confidence": 0.95,
        "reasoning": [
            "Data size within PostgreSQL sweet spot",
            "Complex queries need relational DB",
            "50 concurrent users manageable"
        ]
    }
}
```

---

## Parent CC → App (Control Commands)

### Command Types

| Command | Purpose | Required Response |
|---------|---------|-------------------|
| `check_health` | Monitor app status | Health metrics |
| `get_diagnostics` | Detailed troubleshooting | Full diagnostics |
| `request_shutdown` | Graceful shutdown | Acknowledgment |
| `set_log_level` | Adjust logging | Confirmation |
| `set_config` | Update configuration | Confirmation |

### 1. Check Health

**Purpose:** Periodic health monitoring

**Command:**
```python
{
    "command": "check_health"
}
```

**Response:**
```python
{
    "status": "healthy",  # or "degraded", "unhealthy"
    "uptime_seconds": 3600,
    "error_count": 2,
    "last_error": "ConnectionTimeout at 14:30",
    "pending_requests": 0,
    "app_name": "My Application",
    "memory_mb": 150,
    "cpu_percent": 12
}
```

**Frequency:** Every 60 seconds (configurable)

---

### 2. Get Diagnostics

**Purpose:** Detailed diagnostics for troubleshooting

**Command:**
```python
{
    "command": "get_diagnostics",
    "include": ["logs", "config", "metrics"]  # optional filter
}
```

**Response:**
```python
{
    "app_name": "My Application",
    "version": "1.2.3",
    "uptime_seconds": 3600,
    "errors": 2,
    "config": {
        "max_retries": 3,
        "timeout_seconds": 30
    },
    "log_level": "INFO",
    "recent_logs": [
        "2026-02-05 14:30:00 - INFO - Started successfully",
        "2026-02-05 14:31:00 - ERROR - Connection timeout"
    ],
    "request_history": [
        {"type": "HELP", "timestamp": "2026-02-05 14:29:00"},
        {"type": "ERROR_RECOVERY", "timestamp": "2026-02-05 14:31:00"}
    ],
    "mesh_connected": true,
    "active_operations": 2
}
```

---

### 3. Request Shutdown

**Purpose:** Graceful application shutdown

**Command:**
```python
{
    "command": "request_shutdown",
    "reason": "Maintenance required",
    "urgent": false,
    "timeout_seconds": 60
}
```

**Response:**
```python
{
    "acknowledged": true,
    "cleanup_status": "success",  # or "partial", "failed"
    "message": "Saving state and closing connections...",
    "estimated_shutdown_seconds": 5
}
```

**App Actions:**
1. Stop accepting new work
2. Complete in-flight operations (if not urgent)
3. Save state
4. Close connections
5. Exit cleanly

---

### 4. Set Log Level

**Purpose:** Dynamic log level adjustment for debugging

**Command:**
```python
{
    "command": "set_log_level",
    "level": "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
}
```

**Response:**
```python
{
    "updated": true,
    "old_level": "INFO",
    "new_level": "DEBUG",
    "message": "Log level updated successfully"
}
```

---

### 5. Set Config

**Purpose:** Runtime configuration updates

**Command:**
```python
{
    "command": "set_config",
    "key": "max_retries",
    "value": 5
}
```

**Response:**
```python
{
    "updated": true,
    "key": "max_retries",
    "old_value": 3,
    "new_value": 5,
    "message": "Configuration updated"
}
```

---

## Data Formats

### AssistanceRequest

```python
{
    "request_type": str,  # RequestType enum value
    "context": dict,      # Situation context
    "question": str,      # Optional question
    "options": list,      # Optional list of choices
    "priority": str,      # RequestPriority enum value
    "timeout_seconds": int,
    "request_id": str     # Auto-generated
}
```

### AssistanceResponse

```python
{
    "approved": bool,           # True if approved/should proceed
    "guidance": str,            # Optional guidance text
    "suggested_action": str,    # Optional suggested action
    "data": dict,              # Optional additional data
    "should_retry": bool,      # For error recovery
    "reason": str,             # Optional reason
    "confidence": float        # Optional confidence (0-1)
}
```

### Priority Levels

```python
class RequestPriority(Enum):
    LOW = "low"         # Can wait, not time-sensitive
    NORMAL = "normal"   # Standard priority
    HIGH = "high"       # Important, should respond quickly
    URGENT = "urgent"   # Critical, needs immediate attention
```

---

## Error Handling

### Timeouts

**App → Parent CC:**
- Default timeout: 30 seconds
- Configurable per request
- On timeout: App proceeds with safe default

**Parent CC → App:**
- Apps must respond within 5 seconds
- On timeout: Parent CC marks app as unresponsive

### Connection Loss

**If MM mesh disconnected:**
1. Apps continue with cached guidance
2. Log all failed assistance requests
3. Attempt automatic reconnection
4. Queue requests for retry when reconnected

### Malformed Requests

**Apps must validate:**
- All required fields present
- Enums have valid values
- Data types correct

**Parent CC must:**
- Return helpful error messages
- Suggest corrections
- Never crash on bad input

---

## Best Practices

### For Apps

**DO:**
- ✅ Use specific, detailed context in requests
- ✅ Include all relevant information
- ✅ Set appropriate priorities
- ✅ Handle timeouts gracefully
- ✅ Log all assistance requests
- ✅ Cache frequently needed guidance

**DON'T:**
- ❌ Ask for permission for trivial actions
- ❌ Spam requests (rate limit yourself)
- ❌ Include sensitive data without sanitizing
- ❌ Block app on assistance requests
- ❌ Ignore Parent CC control commands

### For Parent CC

**DO:**
- ✅ Provide clear, actionable guidance
- ✅ Explain reasoning
- ✅ Consider app's context and constraints
- ✅ Respond quickly to URGENT requests
- ✅ Monitor app health proactively
- ✅ Suggest improvements

**DON'T:**
- ❌ Give vague or ambiguous guidance
- ❌ Approve destructive actions without careful review
- ❌ Ignore app context
- ❌ Provide overly complex solutions
- ❌ Send control commands excessively

---

## Examples

### Example 1: Import Data with Unknown Size

**Scenario:** App importing data, doesn't know if size is normal.

```python
# App code
def import_data(file_path):
    data = load_file(file_path)
    row_count = len(data)

    # More than expected?
    if row_count > EXPECTED_MAX:
        response = protocol.request_help(
            context={
                "row_count": row_count,
                "expected_max": EXPECTED_MAX,
                "file_size_mb": get_file_size(file_path),
                "available_memory_mb": get_available_memory()
            },
            question=f"Data has {row_count} rows (expected max {EXPECTED_MAX}).
                      Should I continue or paginate?",
            priority=RequestPriority.NORMAL
        )

        if not response.approved:
            logger.warning(response.guidance)
            return paginate_import(data)

        if response.data.get("add_progress_bar"):
            enable_progress_tracking()

    process_data(data)
```

**Parent CC Response:**
```python
{
    "approved": true,
    "guidance": "Continue with full import. 150k rows is large but manageable
                 with your available memory (8GB). Add progress reporting for
                 better UX.",
    "data": {
        "add_progress_bar": true,
        "chunk_size": 10000,
        "memory_safe": true
    }
}
```

---

### Example 2: Database Connection Failures

**Scenario:** App can't connect to database, not sure how to recover.

```python
# App code
def save_record(record):
    for attempt in range(MAX_RETRIES):
        try:
            db.connect()
            db.save(record)
            return True
        except ConnectionError as e:
            if attempt == 0:
                # Ask Parent CC on first failure
                response = protocol.report_error(
                    error=e,
                    context={
                        "operation": "save_record",
                        "attempt": attempt + 1,
                        "max_retries": MAX_RETRIES,
                        "database": "production",
                        "record_id": record.id
                    }
                )

                if response.should_retry:
                    delay = response.data.get("retry_delay_seconds", 1)
                    strategy = response.data.get("strategy", "exponential")
                    logger.info(f"Retrying with {strategy} backoff: {response.guidance}")
                else:
                    # Parent CC says don't retry
                    logger.error(f"Not retrying: {response.reason}")
                    return queue_for_later(record)

            # Apply Parent CC's guidance
            if strategy == "exponential":
                time.sleep(delay * (2 ** attempt))
            else:
                time.sleep(delay)

    return False
```

**Parent CC Response:**
```python
{
    "approved": true,
    "should_retry": true,
    "guidance": "Database connection failures are usually temporary. Retry with
                 exponential backoff. If all retries fail, queue for background
                 processing.",
    "data": {
        "retry_delay_seconds": 2,
        "strategy": "exponential",
        "max_delay_seconds": 60,
        "fallback_action": "queue_for_background"
    }
}
```

---

## Implementation Guide

### For App Developers

**1. Initialize Protocol:**
```python
from parent_cc_protocol import ParentCCProtocol

protocol = ParentCCProtocol(
    app_name="My Application",
    mesh_integration=mesh_client,
    enable_logging=True
)
```

**2. Use Throughout App:**
```python
# When unsure what to do
response = protocol.request_help(context, question)

# Before risky action
response = protocol.request_permission(action, details)

# After error
response = protocol.report_error(exception, context)
```

**3. Implement Health Endpoint:**
```python
def on_health_check():
    return protocol.check_health()

def on_diagnostics():
    return protocol.get_diagnostics()
```

### For Parent CC Developers

See: `docs/PARENT_CC_IMPLEMENTATION.md` (next document)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-05 | Initial specification |

---

## Related Documents

- `templates/pyqt_app/parent_cc_protocol.py` - Python implementation
- `docs/PARENT_CC_IMPLEMENTATION.md` - Parent CC implementation guide
- `PHASE_1_SUMMARY.md` - Project overview

---

**Questions?** See examples above or check the implementation code.
