param([int]$Rounds = 3, [switch]$Reset)
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$w = $PSScriptRoot
$n = [char]0xC0B0 + "..."
$doc = Get-ChildItem "$w\*.hwpx" | Select-Object -First 1
$base = [IO.Path]::GetFileNameWithoutExtension($doc.Name)
$env:PYTHONIOENCODING = "utf-8"

function Export-Pdf {
  Get-Process Hwp* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep -Milliseconds 900
  $pdf = Join-Path $w ($base + ".pdf")
  if (Test-Path $pdf) { Remove-Item $pdf -Force }
  $hwp = New-Object -ComObject HWPFrame.HwpObject
  $hwp.RegisterModule("FilePathCheckDLL","FilePathCheckerModule") | Out-Null
  $hwp.XHwpWindows.Item(0).Visible = $false
  $hwp.Open($doc.FullName,"","forceopen:true") | Out-Null
  $pg = $hwp.PageCount
  $hwp.SaveAs($pdf,"PDF","") | Out-Null
  try { $hwp.Clear(1); $hwp.Quit() } catch {}
  [Runtime.InteropServices.Marshal]::ReleaseComObject($hwp) | Out-Null
  if (-not (Test-Path $pdf)) { throw "PDF export failed" }
  return $pg
}

if ($Reset) {
  if (Test-Path "$w\tighten.json") { Remove-Item "$w\tighten.json" -Force }
  "-- reset --"
  & python "$w\build.py" 0 | Select-Object -Last 2
  $pg = Export-Pdf
  "baseline pages: $pg"
  & python "$w\orphan.py" | Select-Object -First 2
  ""
}

for ($r = 1; $r -le $Rounds; $r++) {
  "===== round $r ====="
  & python "$w\orphan.py" --write | Select-Object -Last 1
  & python "$w\build.py" 0 | Select-Object -Last 2
  $pg = Export-Pdf
  "pages: $pg"
  & python "$w\orphan.py" | Select-Object -First 2
  ""
}
