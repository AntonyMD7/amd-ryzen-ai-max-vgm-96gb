# Read-only post-reboot attestation for AMD VGM.
# This script DOES NOT call SetOption and DOES NOT change VGM.

$ErrorActionPreference = 'Stop'

Write-Output '============================================================'
Write-Output 'AMD VGM POST-REBOOT ATTESTATION'
Write-Output 'MODE=STRICT_READ_ONLY'
Write-Output '============================================================'

$os = Get-CimInstance Win32_OperatingSystem
Write-Output ('WINDOWS_VISIBLE_GIB=' + [math]::Round(($os.TotalVisibleMemorySize * 1KB) / 1GB, 2))

$gpuValues = @()
Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Video\*\0000' -ErrorAction SilentlyContinue |
ForEach-Object {
    if ($_.PSObject.Properties.Name -contains 'HardwareInformation.qwMemorySize') {
        $v = [math]::Round($_.'HardwareInformation.qwMemorySize' / 1GB, 2)
        $gpuValues += $v
        Write-Output ('DRIVER_GPU_MEMORY_GIB=' + $v)
    }
}

Write-Output ''
Write-Output '=== RECOVERY SERVICES ==='
Get-Service Tailscale,sshd -ErrorAction SilentlyContinue |
ForEach-Object {
    Write-Output ('SERVICE=' + $_.Name + '|STATUS=' + $_.Status + '|STARTTYPE=' + $_.StartType)
}

Write-Output ''
Write-Output '=== 96GB SANITY GATE ==='
$windowsGiB = [math]::Round(($os.TotalVisibleMemorySize * 1KB) / 1GB, 2)
$gpu96 = $gpuValues | Where-Object { [math]::Abs($_ - 96) -lt 1 }

if (($windowsGiB -ge 30) -and ($windowsGiB -le 34) -and $gpu96) {
    Write-Output 'WINDOWS_32GIB_CLASS_GATE=PASS'
    Write-Output 'DRIVER_96GB_CLASS_GATE=PASS'
} else {
    Write-Output 'POST_STATE_GATE=REVIEW_REQUIRED'
}

Write-Output ''
Write-Output 'SETOPTION_CALLED=FALSE'
Write-Output 'VGM_CHANGED_BY_THIS_SCRIPT=FALSE'
Write-Output 'REBOOT_PERFORMED_BY_THIS_SCRIPT=FALSE'
Write-Output 'ATTESTATION_COMPLETE=TRUE'
