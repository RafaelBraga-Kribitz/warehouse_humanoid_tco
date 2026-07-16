# Release Checklist

## Before tagging

- [ ] Run `python scripts/check_publication_pack.py`.
- [ ] Run the full verification suite in the release environment.
- [ ] Regenerate and review committed reports and charts.
- [ ] Confirm the version in `pyproject.toml` and `CITATION.cff` matches the tag.
- [ ] Archive the exact configuration and input manifests.

## Publication

- [ ] Render `docs/case_study.qmd` to the intended formats.
- [ ] Create a GitHub release and attach rendered artifacts.
- [ ] Request DOI registration through the selected repository.
- [ ] Add the DOI to `CITATION.cff` after it is issued.
- [ ] Publish the external-review response with reviewer status.
