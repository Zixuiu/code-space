$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:8080/")
$listener.Start()
Write-Host "Server started: http://localhost:8080"
Write-Host "Press Ctrl+C to stop"

while ($listener.IsListening) {
    $context = $listener.GetContext()
    $request = $context.Request
    $response = $context.Response
    
    $url = $request.Url.LocalPath.TrimStart('/')
    if ([string]::IsNullOrEmpty($url)) { $url = "清单-2.html" }
    
    $filePath = Join-Path $PSScriptRoot $url
    
    if (Test-Path $filePath) {
        $content = [System.IO.File]::ReadAllBytes($filePath)
        if ($url -match "\.html$") { $response.ContentType = "text/html" }
        elseif ($url -match "\.css$") { $response.ContentType = "text/css" }
        elseif ($url -match "\.js$") { $response.ContentType = "application/javascript" }
        else { $response.ContentType = "application/octet-stream" }
        $response.ContentLength64 = $content.Length
        $response.OutputStream.Write($content, 0, $content.Length)
    } else {
        $response.StatusCode = 404
    }
    
    $response.Close()
}
