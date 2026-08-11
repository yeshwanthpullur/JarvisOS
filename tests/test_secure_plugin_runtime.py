from __future__ import annotations
import hashlib, unittest
from dataclasses import replace
from commands import CommandManager
from jarvis.plugin_runtime import *
from jarvis.skills import build_default_skill_registry

def manifest(**changes):
    base=dict(manifest_version="1.0",plugin_id="community.calendar",name="Calendar",version="1.2.3",description="Test metadata",author="Test",plugin_type=PluginType.SKILL,declared_capabilities=("calendar.read",),declared_skills=("calendar_read_external",))
    base.update(changes);return PluginManifest(**base)

class SecurePluginRuntimeTests(unittest.TestCase):
    def test_valid_manifest_and_registration_are_metadata_only(self):
        r=PluginRegistry();record=r.register(manifest());self.assertEqual(record.state,PluginState.UNTRUSTED);self.assertFalse(record.enabled)
    def test_manifest_from_dict_rejects_unknown_field(self):
        raw={"manifest_version":"1.0","plugin_id":"community.x","name":"x","version":"1.0.0","description":"x","author":"x","plugin_type":"skill_plugin","dangerous_admin":True}
        with self.assertRaisesRegex(ValueError,"unknown_manifest_fields"):PluginManifest.from_dict(raw)
    def test_invalid_manifest_version(self):
        with self.assertRaisesRegex(ValueError,"unsupported_manifest_version"):manifest(manifest_version="2.0")
    def test_invalid_id(self):
        with self.assertRaisesRegex(ValueError,"invalid_plugin_id"):manifest(plugin_id="Bad Plugin")
    def test_invalid_semver(self):
        with self.assertRaisesRegex(ValueError,"invalid_plugin_version"):manifest(version="latest")
    def test_duplicate_capability(self):
        with self.assertRaisesRegex(ValueError,"duplicate_plugin_capability"):manifest(declared_capabilities=("x","x"))
    def test_invalid_permission(self):
        raw={"manifest_version":"1.0","plugin_id":"community.x","name":"x","version":"1.0.0","description":"x","author":"x","plugin_type":"skill_plugin","declared_permissions":["admin_everything"]}
        with self.assertRaises(ValueError):PluginManifest.from_dict(raw)
    def test_path_traversal_and_absolute_entrypoint(self):
        for path in ("../evil.py","C:\\evil.py","/evil.py"):
            with self.assertRaisesRegex(ValueError,"path_forbidden"):manifest(entrypoint=path)
    def test_unsupported_runtime(self):
        raw={"manifest_version":"1.0","plugin_id":"community.x","name":"x","version":"1.0.0","description":"x","author":"x","plugin_type":"skill_plugin","runtime_type":"magic"}
        with self.assertRaises(ValueError):PluginManifest.from_dict(raw)
    def test_malformed_dependency(self):
        with self.assertRaises(ValueError):PluginDependency("bad dep","python")
    def test_duplicate_registry_rejected(self):
        r=PluginRegistry();r.register(manifest());self.assertRaisesRegex(ValueError,"duplicate_plugin_id",r.register,manifest())
    def test_protected_skill_and_agent_rejected(self):
        self.assertRaisesRegex(ValueError,"protected_skill",PluginRegistry().register,manifest(declared_skills=("approval_request_skill",)))
        self.assertRaisesRegex(ValueError,"protected_agent",PluginRegistry().register,manifest(declared_agents=("prime_agent",)))
    def test_checksum_verified_and_mismatch_blocked(self):
        content=b"safe";p=manifest(provenance=PluginProvenance(checksum_sha256=hashlib.sha256(content).hexdigest()))
        r=PluginRegistry();r.register(p);self.assertTrue(r.verify(p.plugin_id,content=content).valid)
        r2=PluginRegistry();r2.register(p);v=r2.verify(p.plugin_id,content=b"changed");self.assertFalse(v.valid);self.assertIn("checksum_mismatch",v.blocked_reasons)
    def test_unsigned_reported_truthfully(self):
        r=PluginRegistry();r.register(manifest());self.assertEqual(r.verify("community.calendar").signature,"unsigned")
    def test_dependency_and_credential_missing(self):
        p=manifest(dependencies=(PluginDependency("x","plugin"),),required_credentials=("CALENDAR_TOKEN",));r=PluginRegistry();r.register(p);v=r.verify(p.plugin_id)
        self.assertEqual(v.missing_dependencies,("x",));self.assertEqual(v.missing_credentials,("CALENDAR_TOKEN",))
    def test_declared_permissions_are_not_granted(self):
        p=manifest(declared_permissions=(PluginPermission.NETWORK_WRITE,));r=PluginRegistry();rec=r.register(p);v=r.verify(p.plugin_id)
        self.assertFalse(rec.enabled);self.assertIn("network_write",v.permission_risks)
    def test_network_filesystem_subprocess_and_inprocess_blocked(self):
        cases=(manifest(network_requirements=("example.com",)),manifest(filesystem_requirements=("write_workspace",)),manifest(runtime_type=PluginRuntimeType.EXTERNAL_PROCESS),manifest(runtime_type=PluginRuntimeType.PYTHON_INPROCESS))
        for p in cases:
            r=PluginRegistry();r.register(p);self.assertFalse(r.verify(p.plugin_id).valid)
    def test_enable_requires_verification_and_approval(self):
        content=b"x";p=manifest(provenance=PluginProvenance(checksum_sha256=hashlib.sha256(content).hexdigest()));r=PluginRegistry();r.register(p);r.verify(p.plugin_id,content=content)
        self.assertEqual(r.enable(p.plugin_id),"approval_required_or_invalid")
        approved=PluginRegistry(approval_validator=lambda approval,pid,version,permissions: approval=="approval" and pid==p.plugin_id and version==p.version);approved.register(p);approved.verify(p.plugin_id,content=content)
        self.assertEqual(approved.enable(p.plugin_id,"approval"),"enabled_metadata_only")
    def test_compatibility_is_checked(self):
        p=manifest(minimum_jarvis_version="9.0.0");r=PluginRegistry();r.register(p);v=r.verify(p.plugin_id);self.assertFalse(v.compatible);self.assertIn("jarvis_version_incompatible",v.blocked_reasons)
    def test_install_update_uninstall_execution_disabled(self):
        runtime=PluginRuntime();self.assertIn("disabled",runtime.install_plan("url"));self.assertIn("disabled",runtime.update_plan("x"));self.assertIn("disabled",runtime.uninstall_plan("x"))
    def test_registry_summary_and_history_are_bounded(self):
        r=PluginRegistry(PluginPolicy(max_history_items=2));r.register(manifest());r.verify("community.calendar");self.assertEqual(len(r.history),2);self.assertEqual(r.summary()["enabled"],0)
    def test_cli_is_bounded_and_non_executing(self):
        runtime=PluginRuntime();out=render_plugin_command("plugin install-plan",("https://example.invalid/x",),runtime);self.assertIn("installation_disabled",out);self.assertNotIn("C:\\Users",out)
    def test_registered_cli_commands_are_safe(self):
        manager=CommandManager();manager.initialize()
        commands=("plugin status","plugin help","plugin list","plugin show missing","plugin inspect missing","plugin capabilities missing","plugin permissions missing","plugin dependencies missing","plugin health missing","plugin history","plugin enable-plan missing","plugin enable missing","plugin disable-plan missing","plugin disable missing","plugin install-plan local","plugin update-plan missing","plugin uninstall-plan missing","plugin verify missing")
        for command in commands:
            output=manager.execute(command).response;self.assertNotIn("unknown command",output.lower());self.assertLess(len(output),2000);self.assertNotIn("C:\\Users",output)
    def test_skill_registry_has_safe_and_disabled_plugin_skills(self):
        skills=build_default_skill_registry();self.assertIsNotNone(skills.get_skill("plugin_registry_skill"));self.assertFalse(skills.get_skill("plugin_auto_install_skill").enabled)
    def test_plugin_and_mcp_trust_are_independent(self):
        p=manifest(plugin_type=PluginType.MCP,declared_mcp_servers=("calendar-mcp",));r=PluginRegistry();rec=r.register(p);self.assertEqual(rec.trust,PluginTrust.UNTRUSTED)
    def test_prime_routes_plugin_request_to_adapter(self):
        from jarvis.agents import AgentRegistry,PrimeAgent,PrimeRequest,register_specialist_agents
        decision=PrimeAgent(register_specialist_agents(AgentRegistry())).route(PrimeRequest("enable calendar plugin"));self.assertEqual(decision.selected_agent,"adapter_agent")
    def test_no_runtime_execute_surface(self):
        self.assertFalse(hasattr(PluginRuntime(),"execute"))

if __name__ == "__main__": unittest.main()
