# cssUndefinedClasses
Sigil plugin to delete all classes and ids from xhtml files in an epub that are not referenced in css nor in xml and xhtml attributes.

There is a graphical interface that allows the user to choose which classes and IDs to delete, in which files to look for them and in which attributes to look for fragment identifiers and id references (for a complete list of the default attributes, cfr. the thread of the plugin on [mobileread](https://www.mobileread.com/forums/showthread.php?t=332317)).

The plugin's code is licensed under the [GPL v3](https://www.gnu.org/licenses/gpl-3.0.html), unless expressly stated otherwise for individual parts.

The plugin_utils module is from Doug Massay's [sigil_plugin_utils](https://github.com/dougmassay/sigil-plugin-utils) repository and is licensed under the BSD 2-clause license.
