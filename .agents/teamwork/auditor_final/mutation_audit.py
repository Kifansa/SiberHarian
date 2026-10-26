"""
Forensic Mutation Sensitivity Audit Script
Verifies that modifying/breaking production code behaviors causes the corresponding
tests in tests/test_cti_e2e_suite.py to FAIL (demonstrating genuine mutation kill rate).
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tests.test_cti_e2e_suite as e2e_suite
from tests.test_cti_e2e_suite import (
    TestTier1Tahap4PerNewsPipeline,
    TestTier1Tahap5PeriodicUpdateEngine,
    TestTier1R3DashboardAdditiveIntegration,
)
import src.cti.analyzer as analyzer_mod
import src.storage.db as db_mod
import src.cti.updater as updater_mod
import src.analytics.cti_agents as cti_agents_mod


def run_single_test(test_class, test_name):
    suite = unittest.TestSuite()
    suite.addTest(test_class(test_name))
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    return len(result.failures) + len(result.errors) > 0


def main():
    print("=== STARTING FORENSIC MUTATION SENSITIVITY AUDIT ===")
    results = []

    # -------------------------------------------------------------
    # 1. Baseline verification (Unmutated: must PASS)
    # -------------------------------------------------------------
    base_1 = run_single_test(TestTier1Tahap4PerNewsPipeline, "test_t1_f11_active_guard_rejects_hallucinated_id")
    base_2 = run_single_test(TestTier1Tahap4PerNewsPipeline, "test_t1_f12_deterministic_d3fend_zero_llm_additions")
    base_3 = run_single_test(TestTier1Tahap4PerNewsPipeline, "test_t1_f10_conditional_attack_flow_detector")
    base_4 = run_single_test(TestTier1Tahap5PeriodicUpdateEngine, "test_t1_f20_drop_guard_rejects_drop_greater_than_30_percent")
    base_5 = run_single_test(TestTier1Tahap5PeriodicUpdateEngine, "test_t1_f23_revoked_technique_auditor_flags_incidents")
    base_6 = run_single_test(TestTier1R3DashboardAdditiveIntegration, "test_t1_f15_section_1_makro_additive_distribution")
    base_7 = run_single_test(TestTier1R3DashboardAdditiveIntegration, "test_t1_f17_section_3_vektor_additive_mitre_reference")
    base_8 = run_single_test(TestTier1R3DashboardAdditiveIntegration, "test_t1_f18_section_4_rekomendasi_additive_d3fend_nist")

    baseline_clean = not any([base_1, base_2, base_3, base_4, base_5, base_6, base_7, base_8])
    print(f"Baseline Unmutated Execution: {'ALL PASS (CLEAN)' if baseline_clean else 'UNEXPECTED FAILURE'}")
    assert baseline_clean, "Baseline tests failed before mutation!"

    # -------------------------------------------------------------
    # Mutation 1: Active ATT&CK Validation Guard
    # Mutant: Accept all IDs including T9999 as valid
    # -------------------------------------------------------------
    orig_guard = analyzer_mod.CTINewsAnalyzer.guard_active_attack_id
    try:
        analyzer_mod.CTINewsAnalyzer.guard_active_attack_id = lambda self, tid: (tid, True)
        failed = run_single_test(TestTier1Tahap4PerNewsPipeline, "test_t1_f11_active_guard_rejects_hallucinated_id")
        results.append(("Mutation 1: Active ATT&CK Guard Neutered (Accept T9999)", "KILLED (Test Failed as expected)" if failed else "SURVIVED (Integrity Violation)"))
    finally:
        analyzer_mod.CTINewsAnalyzer.guard_active_attack_id = orig_guard

    # -------------------------------------------------------------
    # Mutation 2: Deterministic D3FEND SQL Lookup
    # Mutant: Return hallucinated mitigation on T9999
    # -------------------------------------------------------------
    orig_d3 = db_mod.ambil_d3fend_mitigasi_by_attack_id
    orig_d3_e2e = getattr(e2e_suite, "ambil_d3fend_mitigasi_by_attack_id", None)
    try:
        mutant_d3 = lambda tid, db_path=None: [{"technique_id": "D3-FAKE"}] if tid == "T9999" else []
        db_mod.ambil_d3fend_mitigasi_by_attack_id = mutant_d3
        e2e_suite.ambil_d3fend_mitigasi_by_attack_id = mutant_d3
        failed = run_single_test(TestTier1Tahap4PerNewsPipeline, "test_t1_f12_deterministic_d3fend_zero_llm_additions")
        results.append(("Mutation 2: Deterministic D3FEND Injected with LLM Hallucination", "KILLED (Test Failed as expected)" if failed else "SURVIVED (Integrity Violation)"))
    finally:
        db_mod.ambil_d3fend_mitigasi_by_attack_id = orig_d3
        e2e_suite.ambil_d3fend_mitigasi_by_attack_id = orig_d3_e2e

    # -------------------------------------------------------------
    # Mutation 3: Conditional ATT&CK Extraction
    # Mutant: Always report attack flow even for benign SPBE news
    # -------------------------------------------------------------
    orig_flow = analyzer_mod.CTINewsAnalyzer.detect_attack_flow
    try:
        analyzer_mod.CTINewsAnalyzer.detect_attack_flow = lambda self, text: (True, "fake_flow")
        failed = run_single_test(TestTier1Tahap4PerNewsPipeline, "test_t1_f10_conditional_attack_flow_detector")
        results.append(("Mutation 3: Conditional ATT&CK Flow Blindly Active", "KILLED (Test Failed as expected)" if failed else "SURVIVED (Integrity Violation)"))
    finally:
        analyzer_mod.CTINewsAnalyzer.detect_attack_flow = orig_flow

    # -------------------------------------------------------------
    # Mutation 4: Update Drop Guard (>30% drop rejected)
    # Mutant: Never raise DropDetectionError (returns without error)
    # -------------------------------------------------------------
    orig_drop = updater_mod.detect_catastrophic_drop
    orig_drop_e2e = getattr(e2e_suite, "detect_catastrophic_drop", None)
    try:
        mutant_drop = lambda source, new_count, old_count, threshold=0.3: False
        updater_mod.detect_catastrophic_drop = mutant_drop
        e2e_suite.detect_catastrophic_drop = mutant_drop
        failed = run_single_test(TestTier1Tahap5PeriodicUpdateEngine, "test_t1_f20_drop_guard_rejects_drop_greater_than_30_percent")
        results.append(("Mutation 4: Catastrophic Drop Guard Disabled", "KILLED (Test Failed as expected)" if failed else "SURVIVED (Integrity Violation)"))
    finally:
        updater_mod.detect_catastrophic_drop = orig_drop
        e2e_suite.detect_catastrophic_drop = orig_drop_e2e

    # -------------------------------------------------------------
    # Mutation 5: Historical Revoked Technique Audit Flagging
    # Mutant: tandai_flag_tinjauan_intelijen is a no-op
    # -------------------------------------------------------------
    orig_flag = db_mod.tandai_flag_tinjauan_intelijen
    orig_flag_e2e = getattr(e2e_suite, "tandai_flag_tinjauan_intelijen", None)
    try:
        mutant_flag = lambda tid, flag, db_path=None: 0
        db_mod.tandai_flag_tinjauan_intelijen = mutant_flag
        e2e_suite.tandai_flag_tinjauan_intelijen = mutant_flag
        failed = run_single_test(TestTier1Tahap5PeriodicUpdateEngine, "test_t1_f23_revoked_technique_auditor_flags_incidents")
        results.append(("Mutation 5: Revocation Auditor Flagging Suppressed", "KILLED (Test Failed as expected)" if failed else "SURVIVED (Integrity Violation)"))
    finally:
        db_mod.tandai_flag_tinjauan_intelijen = orig_flag
        e2e_suite.tandai_flag_tinjauan_intelijen = orig_flag_e2e

    # -------------------------------------------------------------
    # Mutation 6: Additive Section 1 Makro
    # Mutant: Omit eCSIRT distribution summary
    # -------------------------------------------------------------
    orig_sec1 = cti_agents_mod._format_distribusi_ecsirt
    try:
        cti_agents_mod._format_distribusi_ecsirt = lambda data=None: ""
        failed = run_single_test(TestTier1R3DashboardAdditiveIntegration, "test_t1_f15_section_1_makro_additive_distribution")
        results.append(("Mutation 6: Dashboard Section 1 Omits eCSIRT Distribution", "KILLED (Test Failed as expected)" if failed else "SURVIVED (Integrity Violation)"))
    finally:
        cti_agents_mod._format_distribusi_ecsirt = orig_sec1

    # -------------------------------------------------------------
    # Mutation 7: Additive Section 3 Vektor Serangan
    # Mutant: Omit MITRE ATT&CK reference block
    # -------------------------------------------------------------
    orig_sec3 = cti_agents_mod._format_rujukan_mitre
    try:
        cti_agents_mod._format_rujukan_mitre = lambda top3: ""
        failed = run_single_test(TestTier1R3DashboardAdditiveIntegration, "test_t1_f17_section_3_vektor_additive_mitre_reference")
        results.append(("Mutation 7: Dashboard Section 3 Omits MITRE Reference", "KILLED (Test Failed as expected)" if failed else "SURVIVED (Integrity Violation)"))
    finally:
        cti_agents_mod._format_rujukan_mitre = orig_sec3

    # -------------------------------------------------------------
    # Mutation 8: Additive Section 4 Rekomendasi
    # Mutant: Omit D3FEND/NIST blocks
    # -------------------------------------------------------------
    orig_sec4 = cti_agents_mod._format_mitigasi_d3fend_nist
    try:
        cti_agents_mod._format_mitigasi_d3fend_nist = lambda top3: ("", "")
        failed = run_single_test(TestTier1R3DashboardAdditiveIntegration, "test_t1_f18_section_4_rekomendasi_additive_d3fend_nist")
        results.append(("Mutation 8: Dashboard Section 4 Omits D3FEND/NIST Mitigations", "KILLED (Test Failed as expected)" if failed else "SURVIVED (Integrity Violation)"))
    finally:
        cti_agents_mod._format_mitigasi_d3fend_nist = orig_sec4

    # Print Summary Table
    print("\n--- MUTATION SENSITIVITY RESULTS ---")
    killed_count = sum(1 for _, res in results if "KILLED" in res)
    for name, res in results:
        print(f"[*] {name}: {res}")
    print(f"\nTotal Mutations: {len(results)}, Killed: {killed_count}/{len(results)} ({killed_count/len(results)*100:.1f}%)")


if __name__ == "__main__":
    main()
