pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'drum_machine'
gnome = import('gnome')

blueprint_compiler = find_program('blueprint-compiler', required: true)

blueprint_files = files(
  'gtk/shortcuts-dialog.blp',
  'gtk/audio-export-dialog.blp',
  'gtk/save-changes-dialog.blp',
  'gtk/reset-defaults-dialog.blp',
)

compiled_ui_dir_name = 'compiled_ui_files'

compiled_blueprints = custom_target('compiled_blueprints',
  input: blueprint_files,
  output: compiled_ui_dir_name,
  command: [blueprint_compiler, 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@']
)

gnome.compile_resources('drum-machine',
  'drum-machine.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: [compiled_blueprints],
  source_dir: [meson.current_source_dir(), compiled_blueprints.full_path()],
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'drum-machine.in',
  output: 'drum-machine',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

drum_machine_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'application.py',
  'style.css',
  'style-dark.css',
]

subdir('config')
subdir('utils')
subdir('interfaces')
subdir('models')
subdir('handlers')
subdir('services')
subdir('dialogs')
subdir('ui')

install_data(drum_machine_sources, install_dir: moduledir)
