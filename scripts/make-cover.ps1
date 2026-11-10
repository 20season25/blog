# 生成站点默认分享卡片图 og:image (1200x630)
Add-Type -AssemblyName System.Drawing
$w = 1200; $h = 630
$bmp = New-Object System.Drawing.Bitmap($w, $h)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'
$g.TextRenderingHint = 'AntiAlias'

# 背景：纸墨色 + 右下角装饰块
$bg = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 20, 20, 18))
$g.FillRectangle($bg, 0, 0, $w, $h)
$accent = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 179, 45, 45))
$g.FillRectangle($accent, 0, 0, 14, $h)
$dim = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 44, 43, 39))
$g.FillRectangle($dim, $w-220, $h-160, 220, 160)
$g.FillRectangle($accent, $w-220, $h-160, 220, 14)

# 大标题
$f1 = New-Object System.Drawing.Font("Microsoft YaHei", 88, [System.Drawing.FontStyle]::Bold)
$white = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 232, 230, 225))
$g.DrawString("认知增量", $f1, $white, 70, 150)

# 副标题
$f2 = New-Object System.Drawing.Font("Microsoft YaHei", 30)
$gray = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 154, 152, 143))
$g.DrawString("不复述新闻，只更新认知。", $f2, $gray, 74, 330)

# 小字
$f3 = New-Object System.Drawing.Font("Microsoft YaHei", 22)
$g.DrawString("AI 深度解读 · 算力金融 · 安全速写 · 每日更新", $f3, $gray, 74, 400)

$out = "D:\CODE\aiblog\docs\assets\cover.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output "saved $out"
