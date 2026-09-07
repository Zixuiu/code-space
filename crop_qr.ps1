Add-Type -AssemblyName System.Drawing
function Crop-Coord {
    param([string]$Src,[string]$Dst,[int]$x0,[int]$y0,[int]$s,[int]$topPad,[int]$botPad,[int]$sidePad)
    $bmp = [System.Drawing.Bitmap]::new($Src)
    $W=$bmp.Width; $H=$bmp.Height
    $cx0=[math]::Max(0,$x0-$sidePad); $cy0=[math]::Max(0,$y0-$topPad)
    $sx1=[math]::Min($W,$x0+$s+$sidePad); $sy1=[math]::Min($H,$y0+$s+$botPad)
    $cw=$sx1-$cx0; $ch=$sy1-$cy0
    $rect=New-Object System.Drawing.Rectangle $cx0,$cy0,$cw,$ch
    $cr=$bmp.Clone($rect,$bmp.PixelFormat)
    $side=[math]::Max($cw,$ch)
    $out=New-Object System.Drawing.Bitmap $side,$side
    $g=[System.Drawing.Graphics]::FromImage($out)
    $g.Clear([System.Drawing.Color]::White)
    $dx=[int](($side-$cw)/2); $dy=[int](($side-$ch)/2)
    $g.DrawImage($cr,$dx,$dy,$cw,$ch)
    $out.Save($Dst,[System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose();$cr.Dispose();$out.Dispose();$bmp.Dispose()
    Write-Output ("SAVED "+$Dst+" box="+$cw+"x"+$ch)
}

# 支付宝: QR正方形边长370, 中心(465,745). 矩阵 x280-650, y560-930. 文字在y980外面
Crop-Coord -Src 'd:\codespace\qr_src\alipay_src.png' -Dst 'd:\codespace\qr_processed\alipay_custom.png' -x0 280 -y0 560 -s 370 -topPad 14 -botPad 0 -sidePad 14

# 微信: QR正方形边长430, 矩阵 x405-836, y560-980, 中心(620,770). 文字在y1100外面
Crop-Coord -Src 'd:\codespace\qr_src\wechat_src.jpg' -Dst 'd:\codespace\qr_processed\wechat_custom.png' -x0 405 -y0 555 -s 430 -topPad 14 -botPad 0 -sidePad 14

Get-ChildItem 'd:\codespace\qr_processed' | Format-Table Name,Length