# GitHub Hosts 配置脚本
# 请以管理员身份运行此脚本

$hostsFile = "C:\Windows\System32\drivers\etc\hosts"

# 要添加的GitHub hosts配置
$newHosts = @"

# GitHub Start
140.82.112.3    github.com
140.82.112.4    github.com
185.199.108.153 assets-cdn.github.com
199.232.69.194  github.global.ssl.fastly.net
185.199.108.133 raw.githubusercontent.com
185.199.108.133 gist.githubusercontent.com
# GitHub End
"@

# 检查是否已存在GitHub配置
$content = Get-Content $hostsFile -Raw
if ($content -match "# GitHub Start") {
    Write-Host "GitHub hosts 配置已存在！"
} else {
    # 追加配置
    Add-Content -Path $hostsFile -Value $newHosts -Force -Encoding UTF8
    Write-Host "GitHub hosts 配置已添加！"
}

# 刷新DNS缓存
ipconfig /flushdns

Write-Host "`nDNS缓存已刷新，请重启浏览器后访问GitHub"
Write-Host "按任意键退出..."
$host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
