# Tag the release on the built commit (#90)

The "Create GitHub Release" step passed no `target_commitish`, so a missing tag was created on
main's tip when the step ran, not on the commit the build used. v0.3.3 was tagged that way.

- [x] `release-pypi.yaml` passes `target_commitish: ${{ github.sha }}` to the release step.
- [ ] The next release's tag sha equals the run's `head_sha`.
