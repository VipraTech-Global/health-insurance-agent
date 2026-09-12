# Django-managed database tables

These physical tables are created and maintained by Django. They are not custom CoverGuide application models and are not counted in the custom entity catalogue.

- `auth_group`
- `auth_permission`
- the `accounts.User` group and permission through tables
- `django_session`
- `django_content_type`
- `django_admin_log`

The replacement preserves their supported Django semantics, account UUID relationships, encoded passwords, sessions and permissions through normal Django migrations and a rehearsed migration. CoverGuide does not reimplement these tables.
