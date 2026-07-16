# Rule-Based Task Taxonomy

Task categories are assigned by
`src/warehouse_humanoid_tco/features/taxonomy.py`; no completed manual-review
dataset is claimed. `classify_task` first uses the dataset manifest source tag,
then applies normalized keyword rules to the repository identifier and task
description. Multiple matching rules produce multiple labels.

| Pattern | Category | Code path |
|---|---|---|
| `pick_medium` manifest source tag | `PICK_MEDIUM_OBJECT` | `features/taxonomy.py::SOURCE_CATEGORY_MAP` |
| `manipulate_diverse` manifest source tag | `PICK_MEDIUM_OBJECT` and `PLACE_GENERAL` | `features/taxonomy.py::SOURCE_CATEGORY_MAP` |
| `dual arm`, `dualarm`, or `bimanual` | `BIMANUAL_HANDLING` | `features/taxonomy.py::TAXONOMY_KEYWORD_RULES` |
| `pillow`, `plate`, `clothes`, or `pickup` | `PICK_MEDIUM_OBJECT` | `features/taxonomy.py::TAXONOMY_KEYWORD_RULES` |
| `into dishwasher` or `into washing machine` | `PLACE_GENERAL` and `TRANSPORT_SHORT` | `features/taxonomy.py::TAXONOMY_KEYWORD_RULES` |
| `insert`, `slot`, `align`, or `stack` | `PLACE_PRECISE` | `features/taxonomy.py::TAXONOMY_KEYWORD_RULES` |

When neither a source tag nor a keyword rule matches, the classifier assigns
`UNCLASSIFIED`; `needs_manual_review` exposes that state for a future,
separately governed review process.
