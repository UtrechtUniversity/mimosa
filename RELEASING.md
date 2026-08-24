# Releasing MIMOSA

This checklist describes how to prepare a MIMOSA release, publish it on GitHub and PyPI, and deploy
the corresponding version of the documentation. Replace the example version below with the version
being released.

```bash
VERSION=1.3.1
```

## 1. Prepare the release

Start from an up-to-date `master` and make the release metadata changes in a small release branch:

```bash
git switch master
git pull --ff-only origin master
git switch -c "release/${VERSION}"
```

Update the following files:

- Set `mimosa.__version__` in `mimosa/__init__.py` to the release version.
- Complete `docs/release_notes/<version>.md` and replace its unreleased or upcoming status with the
  release date.
- Update `docs/release_notes/index.md` so the new version is listed as the latest release.
- Add the release-notes page to the navigation in `mkdocs.yml` if it is not there yet.

Run the complete local checks in the `accreu` environment:

```bash
conda activate accreu
python -m pytest tests
python -m mkdocs build --strict
```

Commit the release preparation, push the branch, and open a pull request to `master`:

```bash
git add mimosa/__init__.py docs/release_notes mkdocs.yml
git commit -m "Prepare release ${VERSION}"
git push -u origin "release/${VERSION}"
```

Only include `mkdocs.yml` in the commit if it actually changed. Wait for all pull-request checks to
pass before merging.

## 2. Tag the released commit

After the release-preparation pull request has been merged, update the local `master` and create an
annotated tag on that exact commit:

```bash
git switch master
git pull --ff-only origin master
git tag -a "v${VERSION}" -m "MIMOSA ${VERSION}"
git push origin "v${VERSION}"
```

The version tag triggers the installation tests and the full cross-platform IPOPT test matrix. Wait
for these checks to pass before publishing the release artefacts.

## 3. Create the GitHub release

On GitHub, open **Releases**, choose **Draft a new release**, and:

1. select the tag `v<version>`;
2. use `MIMOSA <version>` as the title;
3. adapt `docs/release_notes/<version>.md` for the description; and
4. publish it as a normal release, unless the version is explicitly a prerelease.

The Git tag is the authoritative source for everything published below.

## 4. Publish the Python package

Build and upload the package from the released tag, not from later changes on `master`. Follow
[BUILDPIP.md](BUILDPIP.md) for the TestPyPI and PyPI commands. Before uploading, verify that:

- the checkout is at `v<version>`;
- the build output contains only artefacts for the version being released; and
- installing the TestPyPI package reports the expected `mimosa.__version__`.

## 5. Deploy the versioned documentation

Deploy the documentation from the same tag used for the package:

```bash
conda activate accreu
git switch --detach "v${VERSION}"
python -m pip install -e ".[docs]"
python -m mkdocs build --strict
mike deploy --push --update-aliases "${VERSION}" latest
mike set-default --push latest
```

This publishes:

- `/<version>/` as the permanent documentation for the release;
- `/latest/` as an alias for the newest release; and
- the documentation root as a redirect to `latest`.

Return to the normal development branch afterwards:

```bash
git switch master
```

Do not use `mkdocs gh-deploy` for a normal release: it replaces the versioned `mike` arrangement
with a single mutable documentation site.

## 6. Verify and close the release

Perform a short end-user smoke test:

- Install `mimosa==<version>` from PyPI in a clean environment.
- Confirm that `import mimosa; print(mimosa.__version__)` prints the released version.
- Run a small representative model if practical.
- Check the documentation root, `/latest/`, and `/<version>/` URLs.
- Check the GitHub release, tag, and release CI results.
- Delete the merged release branch when it is no longer needed.

Leave `mimosa.__version__` at the released version until work starts towards the next release.
