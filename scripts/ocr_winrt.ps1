# ocr_winrt.ps1 — Windows.Media.OCR helper (PowerShell 5.1, zero pip deps)
# Usage: powershell -File ocr_winrt.ps1 -ImgPath <abs path> -OutPath <abs path>
# Output: UTF-8 JSON file:
#   {"lang":"zh-Hans-CN","lines":[{"x":..,"y":..,"w":..,"h":..,"text":"..",
#     "words":[{"x":..,"y":..,"w":..,"h":..,"text":".."}]}]}
param(
    [Parameter(Mandatory=$true)][string]$ImgPath,
    [Parameter(Mandatory=$true)][string]$OutPath
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime

function Await($WinRtTask, $ResultType) {
    $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
        Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
                       $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

$result = [ordered]@{ lang = ''; lines = @() }
try {
    $null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
    $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime]
    $null = [Windows.Storage.StorageFile, Windows.Foundation, ContentType=WindowsRuntime]

    # pick a Chinese engine: prefer user profile lang, else any zh-* recognizer
    $eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    if ($null -eq $eng -or -not $eng.RecognizerLanguage.LanguageTag.StartsWith('zh')) {
        $eng = $null
        foreach ($tag in @('zh-Hans-CN','zh-Hans','zh-CN','zh-TW','zh-Hant')) {
            $lang = [Windows.Globalization.Language, Windows.Foundation, ContentType=WindowsRuntime]::new($tag)
            $eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
            if ($null -ne $eng) { break }
        }
    }
    if ($null -eq $eng) {
        $result.lines = @()
        $result | ConvertTo-Json -Compress | Set-Content -Path $OutPath -Encoding UTF8
        exit 0
    }
    $result.lang = $eng.RecognizerLanguage.LanguageTag

    $p = $ImgPath -replace '/', '\'
    $file  = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($p)) ([Windows.Storage.StorageFile])
    $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bmp = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])

    # OCR prefers Bgra8|Premultiplied; convert if needed (static SoftwareBitmap::Convert)
    if ($bmp.BitmapPixelFormat.ToString() -ne 'Bgra8' -or $bmp.BitmapAlphaMode.ToString() -eq 'Straight') {
        $bmp = [Windows.Graphics.Imaging.SoftwareBitmap]::Convert($bmp,
                    [Windows.Graphics.Imaging.BitmapPixelFormat]::Bgra8,
                    [Windows.Graphics.Imaging.BitmapAlphaMode]::Premultiplied)
    }

    $res = Await ($eng.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
    $lines = @()
    foreach ($line in $res.Lines) {
        if ($line.Words.Count -eq 0) { continue }
        $x0 = [double]::MaxValue; $y0 = [double]::MaxValue
        $x1 = [double]::MinValue; $y1 = [double]::MinValue
        $words = @()
        foreach ($w in $line.Words) {
            $r = $w.BoundingRect
            if ($r.X -lt $x0) { $x0 = $r.X }
            if ($r.Y -lt $y0) { $y0 = $r.Y }
            if (($r.X + $r.Width)  -gt $x1) { $x1 = $r.X + $r.Width }
            if (($r.Y + $r.Height) -gt $y1) { $y1 = $r.Y + $r.Height }
            $words += [ordered]@{ x = [math]::Round($r.X,1); y = [math]::Round($r.Y,1);
                                  w = [math]::Round($r.Width,1); h = [math]::Round($r.Height,1);
                                  text = $w.Text }
        }
        $lines += [ordered]@{ x = [math]::Round($x0,1); y = [math]::Round($y0,1);
                              w = [math]::Round($x1-$x0,1); h = [math]::Round($y1-$y0,1);
                              text = $line.Text; words = $words }
    }
    $result.lines = $lines
} catch {
    # write minimal valid JSON so Python side can parse; error surfaced as empty lang+lines with err field
    $result = [ordered]@{ lang = ''; lines = @(); err = $_.Exception.Message }
}
$result | ConvertTo-Json -Compress -Depth 4 | Set-Content -Path ($OutPath -replace '/', '\') -Encoding UTF8
