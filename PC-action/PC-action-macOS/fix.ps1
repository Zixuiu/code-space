$path = "d:\code空间\PC-action\PC-action-macOS\app_macos.py"
$content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)

$old1 = [regex]::Escape("        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_font_size = int(screen_height * 0.022)
            font-size: {instruction_font_size}px;
            color: {MacOSColors.TEXT_SECONDARY};
            font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            background: transparent;
        """)
        layout.addWidget(instruction_label)")

$new1 = "        instruction_label = QLabel(\"请按下快捷键组合...\")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_font_size = int(screen_height * 0.022)
        instruction_label.setStyleSheet(f"""
            font-size: {instruction_font_size}px;
            color: {MacOSColors.TEXT_SECONDARY};
            font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            background: transparent;
        """)
        layout.addWidget(instruction_label)"

if ($content -match $old1) {
    $content = $content -replace $old1, $new1
    Write-Host "✅ 修复 1 成功" -ForegroundColor Green
} else {
    Write-Host "❌ 修复 1 未匹配" -ForegroundColor Red
}

$old2 = [regex]::Escape("        shortcut_label.setAlignment(Qt.AlignCenter)
        shortcut_font_size = int(screen_height * 0.03)
            font-size: {shortcut_font_size}px;
            font-weight: 600;
            padding: 14px;
            border: 2px solid {MacOSColors.ACCENT};
            border-radius: 12px;
            background-color: {MacOSColors.CARD_BG};
            min-height: 44px;
            font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            color: {MacOSColors.ACCENT};
        """)
        layout.addWidget(shortcut_label)")

$new2 = "        shortcut_label = QLabel(current_shortcut if current_shortcut else \"未设置\")
        shortcut_label.setAlignment(Qt.AlignCenter)
        shortcut_font_size = int(screen_height * 0.03)
        shortcut_label.setStyleSheet(f"""
            font-size: {shortcut_font_size}px;
            font-weight: 600;
            padding: 14px;
            border: 2px solid {MacOSColors.ACCENT};
            border-radius: 12px;
            background-color: {MacOSColors.CARD_BG};
            min-height: 44px;
            font-family: 'PingFang SC', 'SimHei', 'Helvetica Neue', 'Segoe UI', sans-serif;
            color: {MacOSColors.ACCENT};
        """)
        layout.addWidget(shortcut_label)"

if ($content -match $old2) {
    $content = $content -replace $old2, $new2
    Write-Host "✅ 修复 2 成功" -ForegroundColor Green
} else {
    Write-Host "❌ 修复 2 未匹配" -ForegroundColor Red
}

[System.IO.File]::WriteAllText($path, $content, [System.Text.Encoding]::UTF8)
Write-Host "
🎯 完成！" -ForegroundColor Green
