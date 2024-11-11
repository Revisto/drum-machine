pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'drum_machine'
gnome = import('gnome')

gnome.compile_resources('drum-machine',
  'drum-machine.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
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
]

subdir('interfaces')
subdir('services')

install_data(drum_machine_sources, install_dir: moduledir)
