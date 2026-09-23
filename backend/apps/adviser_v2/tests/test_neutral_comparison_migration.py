from __future__ import annotations

import importlib

from django.db import migrations


def test_neutral_comparison_migration_renames_storage_in_place() -> None:
    module = importlib.import_module(
        "apps.adviser_v2.migrations.0013_neutral_policy_comparisons"
    )
    wrapper = module.Migration.operations[0]
    assert isinstance(wrapper, migrations.SeparateDatabaseAndState)

    state_operations = wrapper.state_operations
    renamed_models = {
        (operation.old_name, operation.new_name)
        for operation in state_operations
        if isinstance(operation, migrations.RenameModel)
    }
    assert renamed_models == {
        ("Recommendation", "Comparison"),
        ("PolicyCandidateAssessment", "PolicyComparisonAssessment"),
        ("RecommendationStatement", "ComparisonStatement"),
        ("RecommendationCitation", "ComparisonCitation"),
    }
    assert not any(
        isinstance(operation, (migrations.CreateModel, migrations.DeleteModel))
        for operation in state_operations
    )
    assert {
        operation.name
        for operation in state_operations
        if isinstance(operation, migrations.RemoveField)
    } == {"rank", "disposition"}

    sql = module.FORWARD_SQL.upper()
    assert "ALTER TABLE ADVISER_V2_RECOMMENDATION\n  RENAME TO ADVISER_V2_COMPARISON" in sql
    assert "DROP TABLE" not in sql
    assert "RENAME COLUMN RECOMMENDATION_ID TO COMPARISON_ID" in sql
    assert "RENAME COLUMN CANDIDATE_ASSESSMENT_ID TO COMPARISON_ASSESSMENT_ID" in sql
