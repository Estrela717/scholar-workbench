$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'video_manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$speaker = New-Object -ComObject SAPI.SpVoice
foreach ($voice in $speaker.GetVoices()) {
    if ($voice.GetDescription() -like '*Huihui*') { $speaker.Voice = $voice; break }
}
$speaker.Rate = 1
foreach ($track in @('innovation', 'llm')) {
    $audioDir = Join-Path $projectRoot ('artifacts\video-raw\' + $track + '\audio')
    New-Item -ItemType Directory -Path $audioDir -Force | Out-Null
    $chapters = $manifest.$track
    for ($i=0; $i -lt $chapters.Count; $i++) {
        $stream = New-Object -ComObject SAPI.SpFileStream
        $stream.Format.Type = 22
        $stream.Open((Join-Path $audioDir ($i.ToString('00') + '.wav')), 3, $false)
        $speaker.AudioOutputStream = $stream
        [void]$speaker.Speak($chapters[$i].narration)
        $stream.Close()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($stream)
    }
    Write-Host ($track + ' narration complete')
}
[void][Runtime.InteropServices.Marshal]::ReleaseComObject($speaker)
