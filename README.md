SublimeLinter-contrib-mypy
================================

[![Build Status](https://travis-ci.org/fredcallaway/SublimeLinter-contrib-mypy.svg?branch=master)](https://travis-ci.org/fredcallaway/SublimeLinter-contrib-mypy)

This linter plugin for [SublimeLinter][docs] provides an interface to [mypy](http://mypy-lang.org). It will be used with files that have the "python" syntax.

**Information for [Sublime Linter 4 beta][sl4] users**: This plugin is compatible with Sublime Linter 4, but functionality has been improved in the `sl4` branch.
You can get the latest release for SL4 by enabing pre-release installation for this package.

## Installation
SublimeLinter 3 must be installed in order to use this plugin. If SublimeLinter 3 is not installed, please follow the instructions [here][installation].

### Linter installation
Before using this plugin, you must ensure that `mypy` is installed on your system. To install `mypy`, do the following:

1. Install [Python](http://python.org/download/) and [pip](http://www.pip-installer.org/en/latest/installing.html).

1. Install `mypy` by typing the following in a terminal:
   ```
   [sudo] pip install mypy
   ```


**Note:** This plugin requires `mypy` 0.520 or later.

### Linter configuration
In order for `mypy` to be executed by SublimeLinter, you must ensure that its path is available to SublimeLinter. Before going any further, please read and follow the steps in [“Finding a linter executable”](http://sublimelinter.readthedocs.org/en/latest/troubleshooting.html#finding-a-linter-executable) through “Validating your PATH” in the documentation.

Once you have installed and configured `mypy`, you can proceed to install the SublimeLinter-contrib-mypy plugin, if it is not yet installed.

### Plugin installation
Please use [Package Control][pc] to install the linter plugin. This will ensure that the plugin will be updated when new versions are available. If you want to install from source so you can modify the source code, you probably know what you are doing so we won’t cover that here.

To install via Package Control, do the following:

1. Within Sublime Text, bring up the [Command Palette][cmd] (*Tools → Command Palette…*) and select `Package Control: Install Package`. There may be a pause of a few seconds while Package Control fetches the list of available packages.

1. When the package list appears, select `SublimeLinter-contrib-mypy`.

## Settings
For general information on how SublimeLinter works with settings, please see [Settings][settings]. For information on generic linter settings, please see [Linter Settings][linter-settings].

|Setting|Description|
|:------|:----------|
|cache-dir|The directory to store the cache in. Creates a sub-folder in your temporary directory if not specified.|
|follow-imports|Whether imports should be followed and linted. The default is `silent`, but `skip` may also be used. The other options are not interesting.|

A file named `mypy.ini` is automatically recognized as the `--config-file` parameter, if it exists.
All other args to mypy should be specified in the `args` list.

## Contributing
If you would like to contribute enhancements or fixes, please do the following:

1. Fork the plugin repository.
1. Hack on a separate topic branch created from the latest `master`.
1. Commit and push the topic branch.
1. Make a pull request.
1. Be patient.  ;-)

Please note that modifications should follow these coding guidelines:

- Indent is 4 spaces.
- Code should pass flake8 and pep257 linters.
- Vertical whitespace helps readability, don’t be afraid to use it.
- Please use descriptive variable names, no abbreviations unless they are very well known.

Thank you for helping out!

[sl4]: https://github.com/SublimeLinter/SublimeLinter#sublimelinter-4-beta
[docs]: https://sublimelinter.readthedocs.org
[installation]: https://sublimelinter.readthedocs.org/en/latest/installation.html
[locating-executables]: https://sublimelinter.readthedocs.org/en/latest/usage.html#how-linter-executables-are-located
[pc]: https://packagecontrol.io/installation
[cmd]: https://docs.sublimetext.info/en/sublime-text-3/extensibility/command_palette.html
[settings]: https://sublimelinter.readthedocs.org/en/latest/settings.html
[linter-settings]: https://sublimelinter.readthedocs.org/en/latest/linter_settings.html
