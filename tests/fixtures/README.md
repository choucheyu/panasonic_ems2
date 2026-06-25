# Panasonic EMS2 Test Fixtures

Fixtures in this directory must be safe to commit.

## Redaction rules

Do not commit live Panasonic/Home Assistant data that contains:

- Panasonic account emails or passwords
- `CPToken`, `RefreshToken`, or any other bearer/session token
- raw `Auth` values
- real `GWID`, `ModelID`, or other unique household/device identifiers
- local or public IP addresses
- personal room/device nicknames unless intentionally synthesized

Use synthetic values instead, for example:

```json
{
  "GWID": "GWID_PXGD_1",
  "Auth": "AUTH_REDACTED",
  "NickName": "PXGD 空調 A",
  "ModelID": "MODELID_PXGD"
}
```

The `tests/unit/test_fixture_redaction.py` test enforces these rules for JSON fixtures.
