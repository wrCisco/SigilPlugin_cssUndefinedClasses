
if ( Test-Path -Path 'C:\Program Files\Sigil\plugin_launchers\python' -PathType Container ) {
  $Sigil_Plugin_launchers="C:\Program Files\Sigil\plugin_launchers\python"
}
else {
  $Sigil_Plugin_launchers=""
}
$env:PYTHONPATH="$PSScriptRoot\cssUndefinedClasses;$Sigil_Plugin_launchers;$PYTHONPATH"

if ( Test-Path -Path 'C:\Program Files\Sigil\sigilgumbo.dll' -PathType Leaf ) {
  $env:SigilGumboLibPath="C:\Program Files\Sigil\sigilgumbo.dll"
}

python -m unittest discover -s tests -v
