# Trusted Python source and execution review — 2026-11-03

Owner explicitly authorized autonomous selection of two small public pure-Python
repositories, pinned commits/historical issues, code/dependency/test review, and
offline Docker tests only. No third-party source was imported, installed, or run
on the host. Git object export and Python AST parsing treat source as data.

| Repository | Baseline SHA | Issue | Input scope |
| --- | --- | --- | --- |
| pallets/itsdangerous | 1a9b8d1f9968eb248bda69f39d373a6330b692ba | [126](https://github.com/pallets/itsdangerous/issues/126) | all 9 package Python files under src/itsdangerous |
| more-itertools/more-itertools | 64be96ceb2a6e836f76f069f4a96d2394d59fd0c | [1336](https://github.com/more-itertools/more-itertools/issues/1336) | all 3 package Python modules; v11.1.0 |

These are executable package-source projections, not complete repository working
trees. Setup/build scripts, upstream test config/plugins, documentation, stubs and
non-source files are not execution inputs. Per-file SHA256 identities and commit
provenance are recorded in each source.json. Original MIT/BSD license notices are
included. Export script uses read-only `git show`/`ls-tree`, not checkout hooks.

Selection rationale: maintained upstream projects, small source sets, reproducible
bugs in bounded functions, no external services or runtime dependency installation.
ItsDangerous setup.cfg has no mandatory runtime dependency. Its optional simplejson
import falls back to Python json; simplejson is not installed. Its imports are
standard-library crypto/encoding/JSON/time utilities. more-itertools pyproject has
no runtime dependency; flit is build-only and is not invoked. Package imports are
standard-library iterator/math/collections helpers, including threading utilities;
reviewed validation invokes only replacement iteration. No network/process launch,
credential access or filesystem writes appear in the exercised functions. Static
import/call-site inspection is not a hostile-code security guarantee.

Protected independent tests use only preinstalled pinned pytest and standard
library, with no project config/plugins or setup/install steps. Tests verify the
imported package path is inside /workspace, preventing installed-package fallback.
The trusted runner accepts only `.` or `src` import roots. The command/entrypoint
remain fixed. Image is pinned by local immutable ID in the approved policy.
Nonroot, network none, readonly mounts/root, seccomp, caps dropped, no socket or
credentials, CPU/memory/pids/output/deadline limits remain unchanged.

Actual first probe: ItsDangerous reproduced three failed assertions and passed
8/8 after deterministic patch. more-itertools reproduced the empty-input bug but
one new test incorrectly required a two-argument predicate for a final short
window; that TypeError was a validation authoring error. Also the existing 40KB
whole-source patch evidence budget refused its 170350-byte module. Initial raw
report is preserved in pre-v8-python-initial-probe.json. Corrected predicate uses
the documented variable argument contract. A reviewed profile may now select a
source evidence budget up to 1MB (500KB for this module), retaining 40KB defaults
and the unchanged 40KB diff budget. Model/tool input cannot set these budgets.

Corrected actual probe: ItsDangerous baseline 3 failed/5 passed, patched 8 passed;
more-itertools baseline 6 failed/3 passed, patched 9 passed. Both verify exact
revision 1, mandatory runtime isolation and confirmed cleanup. See
[raw report](pre-v8-python-probe.json). These are deterministic patches with real
Docker tests, not LLM success or GitHub publication. Further integration, safe
decision/negative cases, independent final regression and live model evaluation
remain pending in the active execution plan.
