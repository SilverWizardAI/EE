# Phase 1: MCP Mesh Integration - Bootstrap C3 with Real-Time Orchestration

**Objective:** Integrate MCP Mesh (MM) into C3 to enable real-time instance communication, replacing file-based polling with synchronous mesh calls.

**Timeline:** 4-6 weeks
**Priority:** CRITICAL - Unlocks all future automation
**Approach:** Bootstrap and dogfood - improve MM by using it in C3

---

## CRITICAL CONSTRAINTS

### ⚠️ DO NOT Re-engineer C3 Working Functions

**PRESERVE these working systems:**
- ✅ Campaign management UI (campaigns_qt.py)
- ✅ Health scanning system (22 detectors)
- ✅ MCP server with hex commands (c3_mcp_server.py)
- ✅ Terminal manager (terminal_manager.py)
- ✅ All existing services and utilities
- ✅ Database schema and persistence
- ✅ UI/UX and user workflows

**ONLY ADD mesh capabilities:**
- Add MM client integration
- Create mesh-enabled alternatives to file polling
- Preserve fallback to existing file-based methods
- Enable gradual migration, not big-bang replacement

---

## CURRENT STATE ANALYSIS

### C3 Current Architecture

**File-Based TCC Monitoring (The Pain Point):**
```python
# Current approach in sw_factory_execution_engine.py
def _monitor_tcc_progress(self):
    monitor_file = Path(".claude/monitor_cc.md")
    while True:
        time.sleep(5)  # 5-second polling interval
        content = monitor_file.read_text()
        status = cc_monitor_parser.parse(content)  # Complex markdown parsing
        if status.tool_uses >= 300:
            self._restart_tcc()
```

**Problems:**
- 5-second latency on all status checks
- Complex markdown parsing (~400 LOC in cc_monitor_parser.py)
- No bi-directional communication
- File I/O overhead
- TCC unaware of C3's decisions until next poll

**Components Affected:**
1. `sw_factory_execution_engine.py` (863 LOC) - Core orchestration
2. `cc_monitor_parser.py` - Monitoring log parser
3. `cc_monitoring_templates.py` (389 LOC) - Monitoring templates
4. `terminal_manager.py` (917 LOC) - TCC process management

### MM Current State

**Status:** Production-ready infrastructure (3,668 LOC across 19 modules)

**What Works:**
- ✅ Central proxy server (port 6000 MCP + port 6001 HTTP)
- ✅ Service registry (SQLite, persistent)
- ✅ Health monitoring (2-min timeout, dead service detection)
- ✅ Instance server framework (@tool() decorator)
- ✅ Client library (MeshClient with context manager)
- ✅ 7 MCP tools (list_services, call_service, etc.)

**What Needs Enhancement:**
- ⚠️ HTTP call routing incomplete (MeshClient HTTP transport)
- ⚠️ Not yet dogfooded in production
- ⚠️ Error handling needs real-world testing
- ⚠️ Performance under load untested

---

## TARGET STATE (End of Phase 1)

### Goal: C3 Uses MM for Real-Time TCC Communication

**New Architecture:**
```python
# With MCP Mesh integration
class MeshEnabledExecutionEngine:
    def __init__(self):
        self.mesh = MeshClient()  # Connect to mesh proxy

    def _monitor_tcc_progress(self):
        # TCC reports directly via mesh (no polling!)
        # C3 receives instant notifications
        # Bi-directional: C3 can send commands back
        pass
```

**Benefits:**
- Zero polling latency (5s → 0s)
- Real-time bi-directional communication
- Simplified code (~400 LOC reduction in parsing)
- TCC can request help when stuck
- C3 can dynamically adjust TCC behavior

---

## PHASE 1 TASKS

### Week 1-2: MM Production Readiness

**Task 1.1: Complete MeshClient HTTP Transport**
- **Location:** `MM/client/mesh_client.py`
- **Current:** HTTP transport stub raises NotImplementedError
- **Target:** Fully functional HTTP calls to proxy
- **Success Criteria:**
  - Can call `mesh.call("instance", "tool", **params)` via HTTP
  - Error handling with timeouts
  - Response parsing and validation
  - Integration test passing

**Task 1.2: Deploy MM Central Proxy**
- **Location:** Create `/MM/deployment/` directory
- **Target:** Production deployment of mesh proxy
- **Components:**
  - Start proxy on system boot (launchd plist)
  - Log rotation and monitoring
  - Health check endpoint
  - Simple status dashboard
- **Success Criteria:**
  - Proxy runs reliably in background
  - Auto-restart on crash
  - Logs accessible for debugging
  - Can query registry via HTTP

**Task 1.3: Create C3 MCP Mesh Server**
- **Location:** `C3/services/c3_mesh_server.py` (new file)
- **Target:** C3 instance exposes tools via mesh
- **Implementation:**
  ```python
  from mcp_mesh.instance import InstanceServer

  class C3MeshServer(InstanceServer):
      def __init__(self):
          super().__init__(
              service_name="c3_orchestrator",
              description="C3 Campaign Orchestrator"
          )

      @server.tool()
      async def get_campaign_status(self, campaign_id: str) -> dict:
          """Get current campaign status"""
          campaign = campaign_manager.get(campaign_id)
          return {
              "status": campaign.status,
              "progress": campaign.progress,
              "current_step": campaign.current_step
          }

      @server.tool()
      async def report_tcc_progress(
          self,
          step_id: str,
          tool_uses: int,
          token_pct: int,
          status: str
      ) -> dict:
          """TCC reports progress (replaces monitor_cc.md polling)"""
          decision = execution_engine.should_continue(tool_uses, token_pct)
          return {
              "should_continue": decision.continue_exec,
              "create_checkpoint": decision.checkpoint_now,
              "restart_required": decision.restart_required,
              "reason": decision.reasoning
          }
  ```
- **Success Criteria:**
  - C3 registers with mesh proxy on startup
  - Tools callable from other instances
  - Integration test from Python REPL works

### Week 3-4: C3 Integration with MM

**Task 2.1: Add MeshClient to C3**
- **Location:** `C3/services/mesh_integration.py` (new file)
- **Target:** C3 can call mesh services
- **Implementation:**
  ```python
  from mcp_mesh.client import MeshClient

  class C3MeshIntegration:
      def __init__(self):
          self.mesh = MeshClient()

      def connect_to_proxy(self):
          """Connect to mesh proxy, register C3 server"""
          # Start C3 mesh server in background thread
          # Register with proxy
          pass

      def call_tcc_tool(self, instance_name: str, tool: str, **params):
          """Call TCC instance tool via mesh"""
          return self.mesh.call(instance_name, tool, **params)

      def broadcast_to_all_instances(self, tool: str, **params):
          """Call tool on all registered instances"""
          services = self.mesh.list_services()
          results = {}
          for service in services:
              results[service.name] = self.mesh.call(service.name, tool, **params)
          return results
  ```
- **Success Criteria:**
  - C3 can connect to mesh proxy
  - C3 can list available services
  - C3 can call tools on other instances
  - Error handling for disconnections

**Task 2.2: Create Mesh-Enabled TCC Monitoring (Parallel to Existing)**
- **Location:** `C3/services/mesh_tcc_monitor.py` (new file)
- **Target:** Alternative TCC monitor using mesh calls (keeps existing as fallback)
- **Implementation:**
  ```python
  class MeshTCCMonitor:
      """Mesh-based TCC monitoring (replaces file polling)"""

      def __init__(self, mesh_client):
          self.mesh = mesh_client
          self.tcc_instance_name = None

      async def register_tcc_instance(self, instance_name: str):
          """Register TCC instance with mesh"""
          self.tcc_instance_name = instance_name

      async def get_tcc_status(self) -> dict:
          """Get TCC status via mesh (no file polling!)"""
          if not self.tcc_instance_name:
              raise ValueError("TCC instance not registered")

          return self.mesh.call(
              self.tcc_instance_name,
              "get_status",  # TCC exposes this tool
              {}
          )

      async def send_command_to_tcc(self, command: str, params: dict):
          """Send command to TCC via mesh (bi-directional!)"""
          return self.mesh.call(
              self.tcc_instance_name,
              command,
              **params
          )
  ```
- **Success Criteria:**
  - Can query TCC status without file polling
  - Can send commands to TCC
  - Falls back to file polling if mesh unavailable
  - Integration test with mock TCC

**Task 2.3: Update SW Factory Execution Engine (Gradual Migration)**
- **Location:** `C3/services/sw_factory_execution_engine.py`
- **Target:** Add mesh monitoring alongside existing file monitoring
- **Approach:**
  ```python
  class SWFactoryExecutionEngine:
      def __init__(self):
          self.mesh_monitor = None  # Optional mesh monitor
          self.file_monitor = CCMonitorParser()  # Existing fallback

          # Try to enable mesh if available
          try:
              from services.mesh_integration import C3MeshIntegration
              from services.mesh_tcc_monitor import MeshTCCMonitor
              mesh = C3MeshIntegration()
              mesh.connect_to_proxy()
              self.mesh_monitor = MeshTCCMonitor(mesh.mesh)
              logger.info("✅ Mesh monitoring enabled")
          except Exception as e:
              logger.warning(f"Mesh unavailable, using file monitoring: {e}")

      def _monitor_tcc_progress(self):
          """Monitor TCC progress (mesh or file fallback)"""
          if self.mesh_monitor:
              # Try mesh first (real-time, zero latency)
              try:
                  return self._monitor_via_mesh()
              except Exception as e:
                  logger.warning(f"Mesh error, falling back to file: {e}")

          # Fallback to file polling (existing code unchanged)
          return self._monitor_via_file()

      def _monitor_via_mesh(self):
          """Real-time mesh-based monitoring (NEW)"""
          # No sleep() needed - instant status
          status = self.mesh_monitor.get_tcc_status()
          # Process status...

      def _monitor_via_file(self):
          """File-based monitoring (EXISTING - unchanged)"""
          # Existing implementation preserved
          pass
  ```
- **Success Criteria:**
  - Mesh monitoring works when available
  - Gracefully falls back to file monitoring
  - No breaking changes to existing campaigns
  - Can toggle mesh on/off via config flag

### Week 5-6: Dogfooding and Refinement

**Task 3.1: Dogfood on C3 Self-Refactoring Campaign**
- **Objective:** Use C3 with mesh to run a campaign on itself
- **Campaign:** "Optimize C3 Health Detectors"
- **Process:**
  1. Start mesh proxy
  2. Launch C3 with mesh enabled
  3. Create campaign targeting C3 codebase
  4. Monitor via mesh (not files)
  5. Observe latency improvements
  6. Document any issues

**Task 3.2: Measure Performance Improvements**
- **Metrics to Track:**
  - Polling latency: 5s → 0s ✅
  - TCC response time improvements
  - CPU usage (mesh vs file polling)
  - Memory footprint
  - LOC reduction (measure deleted code)
- **Success Criteria:**
  - Zero polling delay demonstrated
  - <5% CPU overhead from mesh
  - At least 200 LOC deleted (from cc_monitor_parser.py)

**Task 3.3: Document Mesh Integration Patterns**
- **Location:** `C3/docs/mesh_integration_guide.md` (new file)
- **Content:**
  - How C3 uses mesh for TCC monitoring
  - How to enable/disable mesh
  - Troubleshooting guide
  - Migration path from file polling
  - Lessons learned from dogfooding
- **Success Criteria:**
  - Other projects can follow this guide
  - Clear examples and code snippets
  - Known issues and workarounds documented

**Task 3.4: Refine MM Based on C3 Usage**
- **Improvements from Dogfooding:**
  - Better error messages
  - Auto-reconnect on proxy restart
  - Timeout tuning
  - Performance optimizations
  - Documentation improvements
- **Success Criteria:**
  - MM more robust after real-world use
  - Edge cases handled
  - Developer experience improved

---

## SUCCESS CRITERIA

### Phase 1 Complete When:

1. ✅ **MM Production Ready**
   - Central proxy runs reliably
   - C3 can register and call services
   - HTTP transport fully functional

2. ✅ **C3 Mesh Integration Working**
   - C3 monitors TCC via mesh (no file polling)
   - Bi-directional communication demonstrated
   - Fallback to file monitoring works

3. ✅ **Dogfooding Successful**
   - C3 runs campaign on itself using mesh
   - Performance improvements measured
   - Zero regressions in existing functionality

4. ✅ **Documentation Complete**
   - Integration guide for other projects
   - Lessons learned documented
   - Known issues and workarounds listed

5. ✅ **LOC Reduction Achieved**
   - At least 200 LOC deleted (cc_monitor_parser.py)
   - Code simpler and more maintainable
   - No increase in complexity elsewhere

---

## RISK MITIGATION

### Risk 1: MM Not Stable Enough
**Mitigation:**
- Keep file monitoring as fallback (already planned)
- Extensive testing before enabling by default
- Gradual rollout (opt-in first, then default)

### Risk 2: Breaking Existing Campaigns
**Mitigation:**
- Zero changes to existing campaign execution
- Mesh is additive, not replacing
- Feature flag to disable mesh if issues

### Risk 3: Performance Degradation
**Mitigation:**
- Benchmark before/after
- Profile mesh overhead
- Optimize or rollback if needed

### Risk 4: Complexity Increase
**Mitigation:**
- Keep integration code isolated (mesh_integration.py)
- Clear separation of concerns
- Fallback reduces risk

---

## DEVELOPMENT WORKFLOW

### Day-to-Day Execution

**Week 1:**
- Monday-Tuesday: Complete MeshClient HTTP transport (MM)
- Wednesday-Thursday: Deploy mesh proxy, test stability
- Friday: Create C3 mesh server, integration tests

**Week 2:**
- Monday-Tuesday: Add MeshClient to C3 (mesh_integration.py)
- Wednesday-Thursday: Create mesh TCC monitor
- Friday: Update execution engine with fallback logic

**Week 3:**
- Monday-Wednesday: Integration testing
- Thursday-Friday: Dogfood campaign on C3 itself

**Week 4:**
- Monday-Wednesday: Measure performance, refine MM
- Thursday-Friday: Documentation and wrap-up

### Testing Strategy

**Unit Tests:**
- MM: Test each tool, transport, registry
- C3: Test mesh integration, fallback logic

**Integration Tests:**
- Mesh proxy + C3 server registration
- TCC status reporting via mesh
- Campaign execution with mesh monitoring

**End-to-End Tests:**
- Full campaign using mesh (no file polling)
- Verify bi-directional communication
- Stress test with multiple TCC instances

---

## DOGFOODING CAMPAIGN SPECIFICATION

### Campaign: "C3 Health Detector Optimization"

**Objective:** Use C3 with mesh to improve C3's own health detectors

**Target:** `C3/health_checks/` directory (29 detectors, 2,393 LOC)

**Steps:**
1. **Scan C3 codebase** - Run health scan on C3 itself
2. **Identify improvements** - Find detectors that could be optimized
3. **Execute via mesh** - TCC refactors detectors, reports via mesh
4. **Monitor in real-time** - C3 receives instant progress updates
5. **Validate** - Run tests, verify improvements

**Success Metrics:**
- Zero file polling during campaign
- Real-time progress visible in C3 UI
- TCC can report blockers instantly
- C3 can send guidance to TCC mid-execution

**Expected Duration:** 2-3 hours (vs 4-6 hours with file polling)

---

## DELIVERABLES

### Code Deliverables

1. **MM Enhancements:**
   - `MM/client/mesh_client.py` - HTTP transport complete
   - `MM/deployment/` - Production deployment scripts
   - `MM/docs/` - Updated documentation

2. **C3 Integration:**
   - `C3/services/mesh_integration.py` - Mesh client integration
   - `C3/services/mesh_tcc_monitor.py` - Mesh-based monitoring
   - `C3/services/c3_mesh_server.py` - C3 as mesh service
   - `C3/services/sw_factory_execution_engine.py` - Updated with mesh support

3. **Tests:**
   - `MM/tests/` - Unit and integration tests
   - `C3/tests/test_mesh_integration.py` - C3 mesh tests

### Documentation Deliverables

1. **Integration Guide:**
   - `C3/docs/mesh_integration_guide.md` - How to use mesh in C3
   - `MM/docs/c3_integration_example.md` - Example usage

2. **Performance Report:**
   - `EE/Assessment/PHASE1_RESULTS.md` - Metrics and outcomes
   - Before/after comparisons
   - LOC reduction analysis

3. **Lessons Learned:**
   - What worked well
   - What needs improvement
   - Recommendations for Phase 2

---

## BOOTSTRAP STRATEGY

### Why Bootstrap?

**Use what we have to build what we need:**
1. C3 already orchestrates multiple instances
2. MM provides the infrastructure C3 needs
3. By integrating MM into C3, we improve both:
   - C3 gets real-time orchestration
   - MM gets real-world testing and refinement

### The Loop:

```
1. Improve MM (complete HTTP transport, deploy proxy)
   ↓
2. Use MM in C3 (integrate mesh monitoring)
   ↓
3. Dogfood C3 on itself (run campaign using mesh)
   ↓
4. Learn from dogfooding (find MM issues, fix them)
   ↓
5. Goto step 1 (iterate and improve)
```

### Key Principle: Additive, Not Replacing

**DO:**
- ✅ Add mesh as alternative to file polling
- ✅ Keep file polling as fallback
- ✅ Enable gradual migration
- ✅ Preserve all working functionality

**DON'T:**
- ❌ Remove working code prematurely
- ❌ Break existing campaigns
- ❌ Force mesh adoption before ready
- ❌ Increase complexity unnecessarily

---

## VALIDATION CHECKLIST

Before considering Phase 1 complete, verify:

- [ ] MM central proxy runs reliably in background
- [ ] C3 can register with mesh proxy
- [ ] C3 can call tools on other mesh instances
- [ ] C3 monitors TCC via mesh (zero file polling)
- [ ] Fallback to file monitoring works if mesh unavailable
- [ ] Dogfooding campaign completes successfully
- [ ] Performance improvements measured and documented
- [ ] At least 200 LOC deleted from monitoring code
- [ ] Integration guide written and tested
- [ ] Known issues documented with workarounds
- [ ] No regressions in existing C3 functionality
- [ ] All tests passing (unit + integration + e2e)

---

## NEXT PHASE PREVIEW

### Phase 2: Standardize CC Instrumentation (3-4 weeks)

Once Phase 1 completes, we'll have:
- Proven mesh integration pattern from C3
- Documentation and examples
- Lessons learned from dogfooding

Phase 2 will:
- Apply mesh integration to 6 more projects
- Standardize CLAUDE.md files across ecosystem
- Create reusable integration templates
- Enable mesh communication between all apps

**Phase 1 is the foundation. Get it right, and everything else follows naturally.**

---

## IMMEDIATE NEXT STEPS

### To Start Phase 1:

1. **Review this prompt** - Understand the approach
2. **Set up development environment:**
   ```bash
   cd /Users/stevedeighton/Library/CloudStorage/Dropbox/A_Coding/MM
   pip install -e .  # Install MM in development mode
   ```

3. **Start with Task 1.1** - Complete MeshClient HTTP transport
4. **Work incrementally** - Small commits, frequent testing
5. **Document as you go** - Keep notes on issues and solutions
6. **Ask questions early** - If unclear, clarify before proceeding

### First Concrete Action:

Open `MM/client/mesh_client.py` and implement the HTTP transport method that currently raises `NotImplementedError`. This is the foundation for everything else.

**Good luck! You're building the future of the Silver Wizard ecosystem. 🚀**
