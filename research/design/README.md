# CoverGuide database-design package

Revision: `discussion-r25-final-review`

The proposal is ready for complete human review. All 17 batch decisions and the final critical audit are incorporated. No Django model, migration, database, benchmark freeze or production change is authorized yet.

The application proposal contains **62 custom models, 587 fields, 167 typed foreign-key relationships and 31 closed JSON definitions**. Django-managed framework tables are listed in [django-managed-tables.md](django-managed-tables.md). The physically separate benchmark proposal contains **24 models, 296 fields, 39 internal foreign keys and 12 closed payload contracts**.

Start with [SIMPLE_DATABASE_REVIEW_GUIDE.md](SIMPLE_DATABASE_REVIEW_GUIDE.md), then use [entity-catalogue.md](entity-catalogue.md) and [field-dictionary.md](field-dictionary.md) for every model and field. [FINAL_DATABASE_DESIGN.md](FINAL_DATABASE_DESIGN.md) explains the final architecture and unresolved evidence work. [final-critical-audit-r25.md](final-critical-audit-r25.md) records the last removals and scope checks.

The application covers health-insurance buying and comparison. Public claim procedures can be structured as policy rules when customers use them to compare products. Customer-specific claim administration, treatment bills, insurer receipts, payment ledgers, cancellation execution and refund tracking are outside the application schema.
