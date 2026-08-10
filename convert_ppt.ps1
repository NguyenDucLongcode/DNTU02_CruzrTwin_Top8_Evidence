param (
    [string]$PptPath = "c:\Users\Ngoc Tan\Downloads\DNTU02_CruzrTwin_Top8_Evidence\PPTCRUZTWIN.pptx",
    [string]$OutputDir = "c:\Users\Ngoc Tan\Downloads\DNTU02_CruzrTwin_Top8_Evidence\ppt_html"
)

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$PptPath = (Resolve-Path $PptPath).Path

Write-Host "Starting PowerPoint COM object..."
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue

Write-Host "Opening Presentation: $PptPath"
$pres = $ppt.Presentations.Open($PptPath)

Write-Host "Exporting slides to PNG..."
# ppSaveAsPNG is 18
$pres.SaveAs($OutputDir, 18)

$pres.Close()
$ppt.Quit()

Write-Host "Generating HTML Viewer..."

# Find all exported PNGs (PowerPoint sometimes creates a subfolder based on the filename, but since we passed OutputDir it should save directly, or inside a folder named like the PPT).
# Actually, SaveAs(..., 18) creates a folder named after the presentation name (e.g. "PPTCRUZTWIN") inside OutputDir, or treats OutputDir as the prefix.
# Let's just find the actual folder where PNGs were placed.
$pngs = Get-ChildItem -Path $OutputDir -Filter "*.png" -Recurse | Sort-Object Name
$imageFolder = ""
if ($pngs.Count -gt 0) {
    $imageFolder = $pngs[0].Directory.FullName
}

if ($imageFolder -eq "") {
    Write-Host "Error: No PNGs found!"
    exit
}

$htmlPath = Join-Path $imageFolder "index.html"

$htmlContent = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CruzrTwin Presentation</title>
    <style>
        body { margin: 0; background-color: #333; display: flex; flex-direction: column; align-items: center; font-family: Arial, sans-serif; }
        .slide-container { margin-top: 20px; width: 90%; max-width: 1200px; box-shadow: 0 4px 8px rgba(0,0,0,0.5); }
        .slide-container img { width: 100%; display: none; border-radius: 8px; }
        .slide-container img.active { display: block; }
        .controls { margin-top: 20px; display: flex; gap: 10px; margin-bottom: 40px;}
        button { padding: 10px 20px; font-size: 16px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 5px; }
        button:hover { background: #0056b3; }
        .counter { color: white; font-size: 18px; align-self: center; margin: 0 15px;}
    </style>
</head>
<body>
    <div class="slide-container" id="slides">
"@

foreach ($img in $pngs) {
    $htmlContent += "`n        <img src='`"$($img.Name)`"' alt='`"$($img.Name)`"'>"
}

$htmlContent += @"
    </div>
    <div class="controls">
        <button onclick="prevSlide()">Previous</button>
        <div class="counter" id="counter">1 / $($pngs.Count)</div>
        <button onclick="nextSlide()">Next</button>
    </div>

    <script>
        let currentIndex = 0;
        const slides = document.querySelectorAll('#slides img');
        const counter = document.getElementById('counter');

        function updateSlide() {
            slides.forEach((s, i) => {
                s.classList.remove('active');
                if(i === currentIndex) s.classList.add('active');
            });
            counter.innerText = (currentIndex + 1) + " / " + slides.length;
        }
        
        function nextSlide() {
            if (currentIndex < slides.length - 1) {
                currentIndex++;
                updateSlide();
            }
        }

        function prevSlide() {
            if (currentIndex > 0) {
                currentIndex--;
                updateSlide();
            }
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === ' ') nextSlide();
            if (e.key === 'ArrowLeft') prevSlide();
        });

        // Init
        if(slides.length > 0) updateSlide();
    </script>
</body>
</html>
"@

Set-Content -Path $htmlPath -Value $htmlContent -Encoding UTF8
Write-Host "Done! Viewer created at: $htmlPath"
Invoke-Item $htmlPath
