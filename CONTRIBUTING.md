# Contributing

## Branches

- `dev` — default branch, all PRs go here
- `main` — releases only, string freeze for translations

## Workflow

1. Create a branch from `dev`
2. Open a PR targeting `dev`
3. Merge to `dev`

## Pre-commit hooks

Install the hooks once so checks run before every commit:

```bash
pip install -r requirements/local.txt
pre-commit install
```

Some hooks use system tools. On Debian/Ubuntu:

```bash
sudo apt install blueprint-compiler appstream desktop-file-utils \
    gettext meson libglib2.0-bin
```

The `blueprint-compiler format` hook compiles each `.blp` file, so it needs the
GTK 4 and libadwaita introspection data (libadwaita 1.8+ for the shortcuts
dialog). If yours is older, skip it with `SKIP=blueprint-format git commit`.