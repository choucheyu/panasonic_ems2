# Panasonic EMS2 Phase 0 Test Protection Plan

> **For Hermes:** Use `test-driven-development` for every production-code change after this plan. Phase 0 itself may add test infrastructure, fixtures, and test files, but must not modify production integration code under `custom_components/panasonic_ems2/`.

**Goal:** Build a repeatable test protection net for `choucheyu/panasonic_ems2` before fixing P0 bugs or doing structural refactors.

**Architecture:** Start with low-risk, fast tests that protect current PXGD/VX behavior and the newly added UX/UJ/UK conservative capability mapping. Then add known-bug guard tests for P0 items as `xfail(strict=True)` or excluded RED tests so the default suite can stay green until each P0 bug is fixed in its own TDD commit.

**Tech Stack:** Python, pytest, pytest-asyncio where needed, Home Assistant custom integration testing utilities if/when HA entity-level tests are introduced.

---

## Current Context

- Repo: `/Users/choucheyu/Projects/panasonic_ems2`
- Current status when this plan was authored: clean git tree.
- Current release: `v0.1.1` / commit `d9827f9 Add conservative UX UJ UK climate support`.
- Existing tests: none.
- Existing CI: HACS action and hassfest only.
- Local plain `python3` has `pytest 8.4.2` but does not import `homeassistant`.
- HA shadow uses Home Assistant `2026.6.3`; its pipx venv imports HA modules but does not currently include pytest.
- Sensitive HA storage exists under `.storage`; do not read or commit tokens/passwords.

## Hard Constraints

1. **No production-code changes in Phase 0 design/scaffolding.** Do not modify files under `custom_components/panasonic_ems2/` except tests may import them.
2. **No HA shadow sync required for tests.** Unit and integration tests should run against fixtures/fakes by default.
3. **No secrets in fixtures.** Redact or synthesize `GWID`, `Auth`, account, token, IP, and any personal nicknames if fixture data is derived from live cloud output.
4. **Keep current working behavior protected.** PXGD/VX entity counts and VX supplemental command behavior should become characterization tests before refactors.
5. **Each later P0 fix must follow TDD:** remove/enable one failing test, watch it fail, implement minimal production fix, watch it pass, then commit.

---

## Proposed Test Layout

Create these files/directories in Phase 0:

```text
tests/
  conftest.py
  helpers/
    __init__.py
    fake_session.py
    import_helpers.py
  fixtures/
    README.md
    pxgd_vx_hdh_user_devices_redacted.json
    command_list_pxgd_hdh_minimal.json
    device_status_pxgd_vx_hdh.json
    device_get_info_vx_supplemental.json
    device_get_info_ux_candidate_supplemental.json
  unit/
    test_manifest_metadata.py
    test_fixture_redaction.py
    test_model_capability_mapping.py
    test_value_workarounds.py
    test_command_metadata_parser.py
    test_entity_description_registry.py
  characterization/
    test_pxgd_vx_entity_snapshot.py
    test_vx_supplemental_snapshot.py
  p0_known_bugs/
    test_options_flow_update_interval_does_not_overwrite_password.py
    test_fan_set_preset_mode_signature.py
    test_switch_is_on_contract.py
    test_dehumidifier_device_class.py
    test_set_device_unknown_command_fail_closed.py
pytest.ini
```

Optional later, after initial tests are stable:

```text
pyproject.toml
.github/workflows/test.yaml
```

---

## Fixture Design

### `tests/fixtures/pxgd_vx_hdh_user_devices_redacted.json`

Purpose: represent current observed device families without secrets.

Synthetic structure should keep Panasonic API shape but redact identifiers:

```json
{
  "GwList": [
    {
      "GWID": "GWID_PXGD_1",
      "Auth": "AUTH_REDACTED",
      "NickName": "PXGD 空調 A",
      "DeviceType": "1",
      "ModelType": "PXGD",
      "Model": "CS-PX36FA2",
      "ModelID": "MODELID_PXGD",
      "Devices": [{"DeviceID": 1, "Name": "", "IsAvailable": true}]
    },
    {
      "GWID": "GWID_VX_1",
      "Auth": "AUTH_REDACTED",
      "NickName": "VX 空調",
      "DeviceType": "1",
      "ModelType": "VX",
      "Model": "CS-VX28BA2",
      "ModelID": "MODELID_VX",
      "Devices": [{"DeviceID": 1, "Name": "", "IsAvailable": true}]
    },
    {
      "GWID": "GWID_HDH_1",
      "Auth": "AUTH_REDACTED",
      "NickName": "HDH 洗衣機",
      "DeviceType": "3",
      "ModelType": "HDH",
      "Model": "NA-V160HDH",
      "ModelID": "MODELID_HDH",
      "Devices": [{"DeviceID": 1, "Name": "", "IsAvailable": true}]
    }
  ]
}
```

### `tests/fixtures/command_list_pxgd_hdh_minimal.json`

Purpose: mimic observed cloud behavior where `CommandList` has `PXGD` and `HDH`, but not `VX`.

Minimum needed PXGD commands:

- `0x01` operating mode enum: Cool, Dehumidify, Fan, Auto, Heat.
- `0x02` fan speed rangeA or enum including Auto/1-5.
- `0x03` target temperature range Min=16 Max=30.
- Swing vertical/horizontal ranges if entity snapshot tests need them.

Do not invent a full Panasonic cloud dump unless needed; start minimal.

### `tests/fixtures/device_status_pxgd_vx_hdh.json`

Purpose: normal `UserGetDeviceStatus` response and baseline `DeviceGetInfo` payloads.

Include enough status keys to validate:

- PXGD base climate creates expected command-backed entities.
- VX base climate remains PXGD-like before supplemental merge.
- HDH wash machine presence does not affect climate tests.

### `tests/fixtures/device_get_info_vx_supplemental.json`

Purpose: protect VX supplemental behavior.

Include:

```json
{
  "status": "success",
  "devices": [
    {
      "DeviceID": 1,
      "Info": [
        {"CommandType": "0x37", "status": 65535},
        {"CommandType": "0x53", "status": 1},
        {"CommandType": "0x55", "status": 0},
        {"CommandType": "0x57", "status": 55},
        {"CommandType": "0x59", "status": 1}
      ]
    }
  ]
}
```

Expected post-normalization:

- PM2.5 `0x37` becomes `-1` for VX.
- `0x53`, `0x55`, `0x57`, `0x59` merge into status.

### `tests/fixtures/device_get_info_ux_candidate_supplemental.json`

Purpose: future UX validation without live device.

Keep this clearly marked synthetic / candidate. Do not use it to claim UX `0x57` support. Include only currently enabled UX supplemental keys (`0x37`, `0x53`, `0x55`, `0x59`) unless a real UX snapshot becomes available.

---

## Default Test Commands

Start with a plain pytest suite that can run without live HA shadow:

```bash
cd /Users/choucheyu/Projects/panasonic_ems2
python3 -m pytest tests/unit tests/characterization -q
```

Known P0 guard tests should either be:

1. excluded from the default command until each fix begins, or
2. marked `pytest.mark.xfail(strict=True, reason="known P0 bug; remove xfail before fixing")`.

Preferred default command after all Phase 0 tests exist:

```bash
python3 -m pytest tests -q
```

If HA imports are required, define a separate command:

```bash
/Users/choucheyu/.local/pipx/venvs/homeassistant/bin/python -m pytest tests/ha -q
```

But because the HA venv currently lacks pytest, do not make this the first required command unless a dedicated test venv is added.

---

## Phase 0 Tasks

### Task 1: Add pytest discovery config

**Objective:** Make test execution predictable without touching production code.

**Files:**
- Create: `pytest.ini`

**Content:**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -ra
markers =
    characterization: tests that lock current behavior before refactor
    p0_bug: known P0 bug guard tests
```

**Verification:**

```bash
python3 -m pytest --collect-only -q
```

Expected initially: no tests collected or newly added tests collected; no production-code change.

---

### Task 2: Add fixture redaction guard

**Objective:** Prevent accidental fixture commits containing secrets or live identifiers.

**Files:**
- Create: `tests/fixtures/README.md`
- Create: `tests/unit/test_fixture_redaction.py`

**Test behavior:** scan `tests/fixtures/**/*.json` for forbidden patterns:

- `CPToken`
- `RefreshToken`
- raw `Auth` values not equal to `AUTH_REDACTED`
- emails
- IP addresses
- likely real long hex GWIDs unless explicitly synthetic prefix `GWID_`

**Important:** This is a meta-test. It should pass before any fixture data is committed.

**Verification:**

```bash
python3 -m pytest tests/unit/test_fixture_redaction.py -q
```

Expected: pass.

---

### Task 3: Add metadata tests

**Objective:** Protect fork identity and HACS/manifest basics.

**Files:**
- Create: `tests/unit/test_manifest_metadata.py`

**Assertions:**

- `manifest.json` parses as JSON.
- `domain == "panasonic_ems2"`.
- `name == "Panasonic Smart IoT TW"`.
- `version` is semantic version, currently `0.1.1`.
- `documentation` and `issue_tracker` point to `https://github.com/choucheyu/panasonic_ems2`.
- `codeowners == ["@choucheyu"]`.
- `hacs.json` name/documentation/issue tracker match fork.
- translations parse as JSON.

**Verification:**

```bash
python3 -m pytest tests/unit/test_manifest_metadata.py -q
```

Expected: pass.

---

### Task 4: Add model capability mapping tests

**Objective:** Lock the conservative UX/UJ/UK design from `v0.1.1`.

**Files:**
- Create: `tests/unit/test_model_capability_mapping.py`

**Behavior to assert:**

- `SUPPLEMENTAL_COMMANDS[str(DEVICE_TYPE_CLIMATE)]["VX"]` includes `0x37`, `0x53`, `0x55`, `0x57`, `0x59`.
- `UX` includes `0x37`, `0x53`, `0x55`, `0x59`, but **does not include** `0x57`.
- `UJ` supplemental list is empty or excludes `0x37`, `0x53`, `0x55`, `0x57`, `0x59`.
- `UK` and `uk` supplemental lists are empty or exclude high-risk keys.
- `CLIMATE_RANGE_FAMILY["UX"]` borrows operating mode and fan speed from `PXGD`.
- `CLIMATE_RANGE_FAMILY["UJ"]` borrows operating mode and fan speed from `PXGD`.
- `CLIMATE_RANGE_FAMILY["UK"]` and `["uk"]` borrow fan speed only and do not borrow operating mode.

**HA import concern:** importing `const.py` requires Home Assistant. If plain `python3` cannot import HA, use one of two approaches:

1. Run this test under a HA-capable test venv, or
2. first create lightweight import stubs in `tests/helpers/import_helpers.py` for HA entity description classes/enums.

Preferred for Phase 0 speed: create stubs only if importing HA is too heavy.

**Verification:**

```bash
python3 -m pytest tests/unit/test_model_capability_mapping.py -q
```

Expected: pass once import strategy is in place.

---

### Task 5: Add value workaround tests

**Objective:** Protect VX/UX PM2.5 invalid-value normalization.

**Files:**
- Create: `tests/unit/test_value_workarounds.py`

**Behavior to assert:**

- `_workaround_info("VX", CLIMATE_PM25, 65535)` returns `(CLIMATE_PM25, -1)`.
- `_workaround_info("UX", CLIMATE_PM25, 65535)` returns `(CLIMATE_PM25, -1)`.
- `_workaround_info("PXGD", CLIMATE_PM25, 65535)` does not incorrectly normalize unless explicitly intended.
- existing dehumidifier/fridge/washing-machine workarounds remain intact.

**Implementation note:** instantiate `PanasonicSmartHome(None, fake_session, account="test", password="test")` without real network.

**Verification:**

```bash
python3 -m pytest tests/unit/test_value_workarounds.py -q
```

Expected: pass.

---

### Task 6: Add command metadata parser characterization tests

**Objective:** Lock current behavior before refactoring `_refactor_cmds_paras()`.

**Files:**
- Create: `tests/fixtures/command_list_pxgd_hdh_minimal.json`
- Create: `tests/unit/test_command_metadata_parser.py`

**Behavior to assert initially:**

- enum parameters become `{label: value}`.
- range parameters create expected values.
- `rangeA` adds `Auto: 0`.
- metadata lookup supports PXGD operating mode/fan speed needed by VX/UX fallback.

**Known future refactor guard:** add a separate test for no mutation of input, marked xfail initially if current code mutates:

```python
@pytest.mark.xfail(strict=True, reason="known design debt: parser mutates raw command metadata")
def test_refactor_cmds_paras_does_not_mutate_input():
    ...
```

When refactoring parser, remove xfail, watch test fail, then implement pure transform.

---

### Task 7: Add VX supplemental snapshot characterization test

**Objective:** Protect the behavior proven in HA shadow: VX supplemental commands merge into status.

**Files:**
- Create: `tests/fixtures/device_get_info_vx_supplemental.json`
- Create: `tests/characterization/test_vx_supplemental_snapshot.py`
- Create: `tests/helpers/fake_session.py`

**Behavior to assert:**

- `_fetch_device_command_snapshot()` returns `0x37=-1`, `0x53=1`, `0x55=0`, `0x57=55`, `0x59=1` for VX fixture.
- `_merge_supplemental_status()` merges those into an existing `Information` list without removing normal status.

**Fake session shape:** minimal async object with `.request()` returning fake response with `.status` and async `.json()`.

**Verification:**

```bash
python3 -m pytest tests/characterization/test_vx_supplemental_snapshot.py -q
```

Expected: pass.

---

### Task 8: Add entity description registry tests

**Objective:** Protect that command keys exposed by supplemental mappings have descriptors.

**Files:**
- Create: `tests/unit/test_entity_description_registry.py`

**Behavior to assert:**

- `CLIMATE_PM25` appears in climate sensors.
- `CLIMATE_HUMIDITY_INDOOR` appears in climate sensors.
- `CLIMATE_MONITOR_MILDEW` appears in climate switches.
- `CLIMATE_IMMEDIATE_MILDEW_DRY` appears in climate selects.
- `CLIMATE_VOICE` appears in climate switches.
- every key in enabled climate supplemental mappings is represented by at least one entity description or is intentionally non-entity.

**Verification:**

```bash
python3 -m pytest tests/unit/test_entity_description_registry.py -q
```

Expected: pass.

---

### Task 9: Add P0 known-bug guard tests without failing default CI

**Objective:** Prepare TDD starting points for P0 fixes while keeping Phase 0 mergeable.

**Files:**
- Create: `tests/p0_known_bugs/test_options_flow_update_interval_does_not_overwrite_password.py`
- Create: `tests/p0_known_bugs/test_fan_set_preset_mode_signature.py`
- Create: `tests/p0_known_bugs/test_switch_is_on_contract.py`
- Create: `tests/p0_known_bugs/test_dehumidifier_device_class.py`
- Create: `tests/p0_known_bugs/test_set_device_unknown_command_fail_closed.py`

**Policy:** each test is one of:

- `@pytest.mark.xfail(strict=True, reason="known P0 bug; remove xfail before fix")`, included in default suite, or
- excluded by default through pytest config and run manually when beginning the corresponding fix.

Preferred: `xfail(strict=True)` so the test file stays visible.

**P0 guards:**

1. **Options flow:** update interval changes must not overwrite password.
2. **Fan preset:** `async_set_preset_mode()` must call `set_device(gwid, device_id, func, value)` with exactly four arguments after `self`.
3. **Switch contract:** `is_on` must return `bool | None`, not `STATE_UNAVAILABLE` string.
4. **Dehumidifier class:** dehumidifier should use `HumidifierDeviceClass.DEHUMIDIFIER`.
5. **Unknown write command:** unknown command should fail closed rather than guessing `int(func, 16) + 128`.

**Verification:**

```bash
python3 -m pytest tests/p0_known_bugs -q
```

Expected before fixes: xfailed tests, no unexpected passes.

---

### Task 10: Add CI test workflow after local tests are stable

**Objective:** Ensure future PRs/commits run the protection net.

**Files:**
- Create or modify: `.github/workflows/test.yaml`

**Initial workflow:**

```yaml
name: Tests

on:
  push:
  pull_request:

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install test dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install pytest pytest-asyncio
      - name: Run tests
        run: python -m pytest tests -q
      - name: Compile integration
        run: python -m compileall -q custom_components/panasonic_ems2 scripts
      - name: Validate JSON
        run: |
          python - <<'PY'
          import json
          from pathlib import Path
          for path in Path('.').rglob('*.json'):
              if '.git' not in path.parts:
                  json.loads(path.read_text())
          PY
```

If tests import Home Assistant directly, add `homeassistant==2026.6.3` or `pytest-homeassistant-custom-component` only after verifying install time and compatibility.

---

## Execution Strategy After This Plan

1. Implement only Phase 0 test files and fixtures first.
2. Run the default suite until it is green.
3. Commit Phase 0 as a test-only commit, e.g.:

```bash
git add pytest.ini tests .github/workflows/test.yaml
git commit -m "Add Phase 0 test protection net"
```

4. Start P0 fixes one at a time:
   - Remove `xfail` for one P0 test.
   - Run it and confirm it fails for the expected bug.
   - Make the minimal production-code fix.
   - Run the specific test and full suite.
   - Commit only that bug fix.

Suggested P0 fix order after Phase 0:

1. `config_flow.py`: options flow update interval/password bug.
2. `fan.py`: `set_device()` extra argument in `async_set_preset_mode()`.
3. `switch.py`: `is_on` return contract.
4. `humidifier.py`: dehumidifier device class and duplicate helper cleanup.
5. `cloud.py`: unknown `set_device()` command fail-closed behavior.

---

## Verification Checklist for Phase 0 Completion

- [ ] `git diff --name-only` shows only test/config/CI docs, no production integration files.
- [ ] Fixture redaction test passes.
- [ ] Metadata tests pass.
- [ ] UX/UJ/UK capability mapping tests pass.
- [ ] VX supplemental characterization tests pass.
- [ ] P0 known-bug tests are present and xfailed or excluded by default.
- [ ] `python3 -m pytest tests -q` passes or gives only intentional strict xfails.
- [ ] `python3 -m compileall -q custom_components/panasonic_ems2 scripts` passes.
- [ ] JSON parse validation passes.

---

## Risks / Tradeoffs

- Importing `const.py` currently imports Home Assistant entity description classes. If installing HA test dependencies is too heavy, use lightweight stubs for early unit tests, then add HA-level tests later.
- Snapshot tests can become brittle if they assert entity IDs. Prefer command keys, unique IDs, and descriptions over user-specific entity IDs.
- Synthetic fixtures prove code paths, not real UX/UJ/UK device behavior. Real model support still requires cloud/status snapshots.
- Xfailed P0 tests keep the baseline green but must be actively converted to RED when implementing each fix.

---

## Open Questions for User Review

1. Should Phase 0 commit include only tests/fixtures, or also a GitHub Actions test workflow?
2. Should fixture device nicknames be generic English/Taiwanese labels, or should they mirror current HA names but redacted?
3. Should P0 guard tests be `xfail(strict=True)` in the default suite, or excluded from default runs until each bug fix starts?
4. Do you want HA-level integration tests using `pytest-homeassistant-custom-component` immediately, or keep Phase 0 lightweight with pure unit/characterization tests first?
