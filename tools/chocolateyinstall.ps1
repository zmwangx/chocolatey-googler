$ErrorActionPreference = 'Stop';

$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
Copy-Item "$toolsDir\googler.py" "$($env:ChocolateyInstall)\bin"
