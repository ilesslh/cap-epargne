param([string]$OutDir)
Add-Type -AssemblyName System.Drawing
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function New-Icon([int]$size, [string]$path, [bool]$maskable, [bool]$rounded) {
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = 'AntiAlias'
    $g.Clear([System.Drawing.Color]::Transparent)
    $green = [System.Drawing.ColorTranslator]::FromHtml('#1D7454')
    $bg = New-Object System.Drawing.SolidBrush $green
    if ($rounded) {
        $r = [int]($size * 0.22); $gp = New-Object System.Drawing.Drawing2D.GraphicsPath
        $gp.AddArc(0, 0, 2*$r, 2*$r, 180, 90); $gp.AddArc($size-2*$r, 0, 2*$r, 2*$r, 270, 90)
        $gp.AddArc($size-2*$r, $size-2*$r, 2*$r, 2*$r, 0, 90); $gp.AddArc(0, $size-2*$r, 2*$r, 2*$r, 90, 90); $gp.CloseFigure()
        $g.FillPath($bg, $gp)
    } else { $g.FillRectangle($bg, 0, 0, $size, $size) }

    # Paper plane, scaled into the safe zone (smaller for maskable)
    $scale = if ($maskable) { 0.52 } else { 0.66 }
    $o = $size * (1 - $scale) / 2; $u = $size * $scale
    $P = { param($x, $y) [System.Drawing.PointF]::new([float]($o + $x * $u), [float]($o + $y * $u)) }
    $white = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $shade = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#CFE8DC'))
    $wing  = [System.Drawing.PointF[]]@((& $P 0.02 0.55), (& $P 0.98 0.12), (& $P 0.42 0.70))
    $body  = [System.Drawing.PointF[]]@((& $P 0.42 0.70), (& $P 0.98 0.12), (& $P 0.60 0.95))
    $fold  = [System.Drawing.PointF[]]@((& $P 0.42 0.70), (& $P 0.98 0.12), (& $P 0.47 0.92))
    $g.FillPolygon($white, $wing); $g.FillPolygon($white, $body); $g.FillPolygon($shade, $fold)
    # Coin: savings
    $cr = $u * 0.17; $cx = $o + $u * 0.16; $cy = $o + $u * 0.88
    $gold = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#F2C14E'))
    $g.FillEllipse($gold, [float]($cx - $cr), [float]($cy - $cr), [float](2*$cr), [float](2*$cr))
    $font = New-Object System.Drawing.Font 'Segoe UI', ([float]($cr * 1.15)), ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Pixel)
    $sf = New-Object System.Drawing.StringFormat; $sf.Alignment = 'Center'; $sf.LineAlignment = 'Center'
    $rect = [System.Drawing.RectangleF]::new([float]($cx-$cr), [float]($cy-$cr), [float](2*$cr), [float](2*$cr)); $g.DrawString([string][char]0x20AC, $font, [System.Drawing.SolidBrush]::new($green), $rect, $sf)
    $g.Dispose(); $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
}
New-Icon 192 (Join-Path $OutDir 'icon-192.png') $false $true
New-Icon 512 (Join-Path $OutDir 'icon-512.png') $false $true
New-Icon 512 (Join-Path $OutDir 'icon-maskable-512.png') $true $false
New-Icon 180 (Join-Path $OutDir 'apple-touch-icon.png') $false $false
Get-ChildItem $OutDir | Select-Object Name, Length
