# 안티그라비티 폴더 파일 변경 감지 → 자동 git 커밋+푸시
$watchPath = "C:\Users\a\Desktop\안티그라비티"
$debounceSeconds = 8   # 마지막 변경 후 8초 대기 (연속 저장 묶기)
$lastChange = [datetime]::MinValue
$timer = $null

Write-Output "[watcher] 시작: $watchPath"

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $watchPath
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor
                        [System.IO.NotifyFilters]::FileName -bor
                        [System.IO.NotifyFilters]::DirectoryName

# 무시할 경로 패턴
function ShouldIgnore($path) {
    $ignorePatterns = @(
        '\.git\\', '\.git/', 'node_modules\\', 'node_modules/',
        '\.next\\', '\.next/', '__pycache__', '\.pyc$',
        'auto-commit-watcher', 'Thumbs\.db', '\.tmp$'
    )
    foreach ($pattern in $ignorePatterns) {
        if ($path -match $pattern) { return $true }
    }
    return $false
}

function TryCommit {
    $now = [datetime]::Now
    $elapsed = ($now - $script:lastChange).TotalSeconds
    if ($elapsed -lt $debounceSeconds) { return }

    Push-Location $watchPath
    try {
        $status = git status --porcelain 2>$null
        if (-not $status) {
            Write-Output "[watcher] 변경사항 없음 - 스킵"
            return
        }
        $dateStr = Get-Date -Format "yyyy. M. d. tt hh:mm:ss"
        git add -A 2>$null
        git commit -m "auto: $dateStr" 2>$null
        git push origin main 2>$null
        Write-Output "[watcher] 커밋+푸시 완료: $dateStr"
    } catch {
        Write-Output "[watcher] 오류: $_"
    } finally {
        Pop-Location
    }
}

$onChange = {
    param($src, $e)
    if (ShouldIgnore $e.FullPath) { return }
    $script:lastChange = [datetime]::Now
    Write-Output "[watcher] 변경 감지: $($e.FullPath)"
}

Register-ObjectEvent $watcher "Changed" -Action $onChange | Out-Null
Register-ObjectEvent $watcher "Created" -Action $onChange | Out-Null
Register-ObjectEvent $watcher "Deleted" -Action $onChange | Out-Null
Register-ObjectEvent $watcher "Renamed" -Action $onChange | Out-Null

Write-Output "[watcher] 감시 중... (변경 감지 후 ${debounceSeconds}초 뒤 커밋)"

# 메인 루프: 8초마다 커밋 조건 확인
while ($true) {
    Start-Sleep -Seconds 4
    if ($script:lastChange -gt [datetime]::MinValue) {
        $elapsed = ([datetime]::Now - $script:lastChange).TotalSeconds
        if ($elapsed -ge $debounceSeconds) {
            TryCommit
            $script:lastChange = [datetime]::MinValue
        }
    }
}
