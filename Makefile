.PHONY: generate-deps

generate-deps:
	flatpak_pip_generator --build-isolation --requirements-file=requirements/base.txt -o python-dependencies --runtime=org.gnome.Sdk/x86_64/master 