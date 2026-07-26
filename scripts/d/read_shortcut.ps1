$WshShell = New-Object -ComObject WScript.Shell
$shortcut = $WshShell.CreateShortcut("C:\Users\33487\Desktop\Cass10.1 For AutoCAD2016.lnk")
Write-Host "TargetPath:" $shortcut.TargetPath
Write-Host "Arguments:" $shortcut.Arguments
Write-Host "WorkingDirectory:" $shortcut.WorkingDirectory
Write-Host "IconLocation:" $shortcut.IconLocation
