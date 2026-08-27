param([int]$Rounds = 2)
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$w = $PSScriptRoot
$doc = Get-ChildItem "$w\*.hwpx" | Where-Object { $_.BaseName -match "01" } | Select-Object -First 1
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
  return $pg
}

for ($r = 1; $r -le $Rounds; $r++) {
  "===== round $r ====="
  & python "$w\colfit.py" --write | Select-Object -Last 1
  & python "$w\build.py" 0 | Select-Object -Last 1
  $pg = Export-Pdf
  "pages: $pg"
  & python "$w\colfit.py" | Select-Object -First 1
  ""
}
