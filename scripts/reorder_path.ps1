$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

$entries = $userPath -split ';' | Where-Object { $_ -ne '' }

# 把 WindowsApps 挪到最后
$windowsApps = $entries | Where-Object { $_ -like '*\Microsoft\WindowsApps' }
$others     = $entries | Where-Object { $_ -notlike '*\Microsoft\WindowsApps' }

$newPath = ($others + $windowsApps) -join ';'

[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

Write-Host "=== 修改后 User PATH ==="
[Environment]::GetEnvironmentVariable("Path", "User")
