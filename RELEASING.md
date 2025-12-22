# Releasing

1. Create a release branch from `dev`:
   ```bash
   git checkout dev
   git pull
   git checkout -b release/X.Y.Z
   ```
2. Update version in `meson.build` following [Semantic Versioning](https://semver.org/)
3. Update `data/io.github.revisto.drum-machine.metainfo.xml` with release notes
4. Commit and push:
   ```bash
   git add meson.build data/io.github.revisto.drum-machine.metainfo.xml
   git commit -m "Release X.Y.Z"
   git push origin release/X.Y.Z
   ```
5. Open a PR targeting `main` and merge it
6. Announce string freeze on [GNOME Discourse](https://discourse.gnome.org/tag/i18n)

7. Wait for string freeze (1-2 weeks depending on changes)

8. Tag and push after translations are complete:
   ```bash
   git tag vX.Y.Z
   git push origin --tags
   ```

9. Release to Flathub
