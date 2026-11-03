# Export check on Windows (EXPORT-01): starts the packaged app against the synthetic fixture, lets it press the Pine export button
# once, types a path into the Windows save dialog and checks that the file landed. No source, no credentials.
param([string]$Exe, [string]$Out)
$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force $Out | Out-Null
New-Item -ItemType Directory -Force shots | Out-Null
Remove-Item "$Out\test.pine" -ErrorAction SilentlyContinue
Add-Type -AssemblyName System.Windows.Forms, System.Drawing, Microsoft.VisualBasic
function Shot($name) {
  $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
  $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
  $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
  $bmp.Save("shots\$name.png"); $g.Dispose(); $bmp.Dispose()
}
$srv = Start-Process python -ArgumentList "ci/mock/server.py", "ci/mock/markets.json" -PassThru -WindowStyle Hidden
Start-Sleep 3
$env:JAVA_TOOL_OPTIONS = "-Dlbt.api=http://127.0.0.1:8787/api/app -Dlbt.favorites=US,AT -Dlbt.market=US -Dlbt.autoExport=pine"
$app = Start-Process $Exe -PassThru
Start-Sleep 45
Shot "win-1-save-window"
try { [Microsoft.VisualBasic.Interaction]::AppActivate("fixture") } catch { Write-Host "could not activate the save dialog: $_" }
Start-Sleep 2
[System.Windows.Forms.SendKeys]::SendWait("^a")
Start-Sleep 1
[System.Windows.Forms.SendKeys]::SendWait($Out + "\test.pine")
Start-Sleep 1
[System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
Start-Sleep 10
Shot "win-2-after-save"
Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
Get-Process -Name "Little Bird Trading" -ErrorAction SilentlyContinue | Stop-Process -Force
Stop-Process -Id $srv.Id -Force -ErrorAction SilentlyContinue
if ((Test-Path "$Out\test.pine") -and ((Get-Item "$Out\test.pine").Length -gt 0)) {
  Write-Host "PASS windows: the Pine file was saved to $Out"
} else {
  Write-Host "FAIL windows: nothing was saved to $Out"
  exit 1
}
