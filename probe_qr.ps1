Add-Type -AssemblyName System.Drawing
$bmp = [System.Drawing.Bitmap]::new('d:\codespace\qr_src\wechat_src.jpg')
$imgW=$bmp.Width
$yy0=560
$yy1=980
# 只探 x830-1200 找右边界
for ($xx=830; $xx -lt 1230; $xx++) {
    $bk=0
    for ($yy=$yy0; $yy -lt $yy1; $yy+=2) {
        $pp=$bmp.GetPixel($xx,$yy)
        $mx=[math]::Max($pp.R,[math]::Max($pp.G,$pp.B))
        $mm=[math]::Min($pp.R,[math]::Min($pp.G,$pp.B))
        if ($mx -lt 115) { if (($mx-$mm) -lt 55) { $bk++ } }
    }
    if ($bk -gt 3) { Write-Output ("X{0} black={1}" -f $xx,$bk) }
}
$bmp.Dispose()