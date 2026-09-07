& 'D:\Docker Toolbox\docker-machine.exe' env default | Out-String | Invoke-Expression
docker cp 'D:\codespace\PayPro-src\PayPro-master\qr\alipay\custom.png' pay:/app/appsystems/qr/alipay/custom.png
docker cp 'D:\codespace\PayPro-src\PayPro-master\qr\wechat\custom.png' pay:/app/appsystems/qr/wechat/custom.png
echo ===容器内验证===
docker exec pay sh -c 'wc -c /app/appsystems/qr/alipay/custom.png /app/appsystems/qr/wechat/custom.png'
echo ===与裁剪成品对比===
Write-Output ("alipay container should be 141301, wechat 72704")