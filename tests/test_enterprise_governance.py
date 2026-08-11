"""Focused Prompt 84 enterprise governance and zero-trust tests."""
from dataclasses import FrozenInstanceError
import unittest

from commands.command_parser import CommandParser
from config import load_settings
from config.schema import GovernanceConfig
from jarvis.governance import *
from jarvis.jarvis_manager import JarvisManager


class GovernanceTests(unittest.TestCase):
    def setUp(self):self.runtime=build_default_governance_runtime()

    def test_identity_creation(self):self.assertEqual(self.runtime.identities["local_user"].identity_type,IdentityType.USER)
    def test_duplicate_identity_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate_identity"):self.runtime.register_identity(self.runtime.identities["local_user"])
    def test_identity_spoofing_shape_rejected(self):
        with self.assertRaisesRegex(ValueError,"invalid_identity_state"):Identity("x","user","x")
    def test_identity_isolation(self):self.assertNotEqual(self.runtime.permissions_for("local_user"),self.runtime.permissions_for("prime"))
    def test_identity_propagation(self):
        chain=self.runtime.identity_chain("executive",("prime",),"workflow",("diagnostics.read",));self.assertEqual(chain.effective_permissions,("diagnostics.read",))
    def test_child_cannot_gain_permission(self):
        chain=self.runtime.identity_chain("executive",("prime",),"workflow",("provider.use",));self.assertNotIn("provider.read",chain.effective_permissions)
    def test_unknown_identity_chain_fails(self):
        with self.assertRaisesRegex(ValueError,"identity_chain_invalid"):self.runtime.identity_chain("missing",(),"x")
    def test_verified_explicit_permission_allowed(self):self.assertTrue(self.runtime.authorize("local_user","diagnostics.read").allowed)
    def test_missing_permission_denied(self):self.assertFalse(self.runtime.authorize("local_user","workflow.execute").allowed)
    def test_unverified_identity_denied(self):self.assertFalse(self.runtime.authorize("missing","diagnostics.read").allowed)
    def test_privileged_default_denied(self):self.assertFalse(self.runtime.evaluate_policy("execute_commands")["allowed"])
    def test_policy_does_not_authorize_execution(self):self.assertFalse(self.runtime.evaluate_policy("diagnostics.read")["execution_authorized"])
    def test_policy_precedence_security_deny(self):
        self.runtime.register_policy(Policy("runtime-allow","runtime.allow","1","global","executive",("write_memory",),("allow:write_memory",),900,PolicyState.ACTIVE));self.assertFalse(self.runtime.evaluate_policy("write_memory")["allowed"])
    def test_policy_conflict_rejected_transactionally(self):
        self.runtime.register_policy(Policy("p1","workflow.one","1","x","executive",("op",),("allow:op",),1,PolicyState.ACTIVE))
        with self.assertRaisesRegex(ValueError,"policy_conflict"):self.runtime.register_policy(Policy("p2","workflow.two","1","x","executive",("op",),("deny:op",),1,PolicyState.ACTIVE))
        self.assertNotIn("p2",self.runtime.policies)
    def test_inactive_policy_not_enforced(self):
        self.runtime.register_policy(Policy("draft","security.draft","1","global","executive",("diagnostics.read",),("deny:diagnostics.read",),1000,PolicyState.DRAFT));self.assertTrue(self.runtime.evaluate_policy("diagnostics.read")["allowed"])
    def test_duplicate_policy_rejected(self):
        policy=self.runtime.policies["security-default-deny"]
        with self.assertRaisesRegex(ValueError,"duplicate_policy"):self.runtime.register_policy(policy)
    def test_unsupported_policy_action_rejected(self):
        with self.assertRaisesRegex(ValueError,"unsupported_policy_action"):Policy("x","x","1","global","x",(),("execute:anything",))
    def test_zero_trust_validates_each_operation(self):self.assertTrue(self.runtime.zero_trust_validate("local_user","diagnostics.read")["valid"])
    def test_zero_trust_blocks_permission_gap(self):self.assertFalse(self.runtime.zero_trust_validate("local_user","workflow.execute")["valid"])
    def test_risk_levels(self):
        self.assertEqual(self.runtime.classify_risk(("status",)),GovernanceRisk.LOW);self.assertEqual(self.runtime.classify_risk(("credential access",)),GovernanceRisk.CRITICAL)
    def test_trust_explainable_and_advisory(self):
        trust=self.runtime.evaluate_trust("provider","provider",("identity_verified","policy_compliant"));self.assertGreater(trust.current_score,.5);self.assertIn("grants no permission",trust.warnings[0])
    def test_trust_revocation(self):self.assertEqual(self.runtime.revoke_trust("provider").trust_level,TrustLevel.REVOKED)
    def test_trust_does_not_change_permissions(self):
        before=self.runtime.permissions_for("prime");self.runtime.evaluate_trust("prime","agent",("identity_verified","policy_compliant","runtime_healthy"));self.assertEqual(before,self.runtime.permissions_for("prime"))
    def test_audit_records_are_frozen(self):
        record=self.runtime.audit_records[0]
        with self.assertRaises(FrozenInstanceError):record.result="changed"
    def test_audit_chain_tamper_evident(self):self.assertTrue(self.runtime.verify_audit_chain())
    def test_audit_correction_appends(self):
        count=len(self.runtime.audit_records);self.runtime.audit_correction(self.runtime.audit_records[0].audit_id,"metadata correction");self.assertEqual(len(self.runtime.audit_records),count+1)
    def test_audit_history_bounded(self):
        runtime=GovernanceRuntime(GovernanceLimits(max_audit_records=3));[runtime.security_event("x","x",SecuritySeverity.WARNING,"safe") for _ in range(5)];self.assertEqual(len(runtime.audit_records),3);self.assertTrue(runtime.verify_audit_chain())
    def test_audit_lookup(self):self.assertTrue(self.runtime.search_audit(event_type="identity_registered"))
    def test_audit_redacts_secret_shaped_values(self):
        event=self.runtime.security_event("credential_misuse","provider",SecuritySeverity.HIGH,"token=do-not-store");self.assertNotIn("do-not-store",str(event));self.assertNotIn("do-not-store",str(self.runtime.audit_records[-1]))
    def test_audit_hides_absolute_path(self):
        event=self.runtime.security_event("path","plugin",SecuritySeverity.WARNING,"C:\\Users\\Private\\file.txt");self.assertNotIn("Users",event.summary)
    def test_compliant_state(self):self.assertEqual(self.runtime.compliance("prime",("security-default-deny",)).status,ComplianceState.COMPLIANT)
    def test_compliance_warning_state(self):
        self.runtime.register_policy(Policy("draft","x","1","global","executive",(),(),status=PolicyState.DRAFT));self.assertEqual(self.runtime.compliance("x",("draft",)).status,ComplianceState.WARNING)
    def test_compliance_non_compliant_state(self):self.assertEqual(self.runtime.compliance("x",("missing",)).status,ComplianceState.NON_COMPLIANT)
    def test_compliance_unknown_state(self):self.assertEqual(self.runtime.compliance("x",()).status,ComplianceState.UNKNOWN)
    def test_event_correlation(self):
        self.runtime.security_event("denied","plugin",SecuritySeverity.HIGH,"blocked",correlation_id="corr");self.assertEqual(len(self.runtime.correlate_events("corr")),1)
    def test_incident_lifecycle(self):
        event=self.runtime.security_event("bypass","plugin",SecuritySeverity.CRITICAL,"blocked");incident=self.runtime.create_incident((event.event_id,));self.assertEqual(incident.risk_level,GovernanceRisk.CRITICAL);self.assertEqual(self.runtime.transition_incident(incident.incident_id,IncidentState.CONTAINED).status,IncidentState.CONTAINED)
    def test_incident_recommendations_are_advisory(self):
        event=self.runtime.security_event("denied","plugin",SecuritySeverity.HIGH,"blocked");incident=self.runtime.create_incident((event.event_id,));self.assertIn("request_operator_review",incident.recommended_actions)
    def test_config_defaults(self):
        config=load_settings().governance;self.assertTrue(config.zero_trust_enabled);self.assertTrue(config.audit_enabled);self.assertLessEqual(config.max_audit_records,5000)
    def test_config_limits_fail_safely(self):
        with self.assertRaisesRegex(ValueError,"invalid_governance_limits"):GovernanceLimits(max_audit_records=0)
    def test_config_invalid_boolean_fails_safely(self):
        with self.assertRaisesRegex(ValueError,"invalid_governance_boolean"):GovernanceConfig(enabled="yes")
    def test_manager_integrations(self):
        manager=JarvisManager();self.assertIs(manager.prime_agent.governance_runtime,manager.governance);self.assertIs(manager.workflow.runtime.governance_runtime,manager.governance);self.assertIs(manager.reliability.governance_runtime,manager.governance)
    def test_cli_parser_routes_security_commands(self):
        parser=CommandParser()
        for command in ("security status","security policy-show security-default-deny","security trust-show prime"):self.assertTrue(parser.parse(command).name.startswith("security "))
    def test_cli_outputs_bounded(self):
        commands=("status","health","identities","permissions","policies","trust","incidents","audit","compliance","risks","governance","events","metrics","dashboard","validate","verify","policy-show","incident-show","audit-show","trust-show")
        for operation in commands:self.assertLessEqual(len(render_security_command(self.runtime,"security "+operation,("security-default-deny",))),5000)
    def test_verify_authority_boundaries(self):
        result=self.runtime.verify();self.assertTrue(result["valid"]);self.assertFalse(result["execution_authority"]);self.assertFalse(result["automatic_permission_escalation"]);self.assertFalse(result["automatic_policy_override"])


if __name__=="__main__":unittest.main()
