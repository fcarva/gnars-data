param(
    [switch]$SkipWebBuild,
    [switch]$SkipPagesBuild
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Action
}

Push-Location $repoRoot
try {
    Invoke-Step -Name "Sync Gnars web sources" -Action { python scripts\sync_gnars.py }
    Invoke-Step -Name "Sync proposal archive" -Action { python scripts\sync_proposals.py }
    Invoke-Step -Name "Sync treasury" -Action { python scripts\sync_treasury.py }
    Invoke-Step -Name "Seed proposal tags" -Action { python scripts\tag_proposals.py --init-pilot 30 --scope pilot-30 }

    Invoke-Step -Name "Derive analytics datasets" -Action { python scripts\derive_analytics.py }
    Invoke-Step -Name "Validate data" -Action { python scripts\validate_data.py }
    Invoke-Step -Name "Export CSVs" -Action { python scripts\export_csv.py }

    if (-not $SkipPagesBuild) {
        Invoke-Step -Name "Build Pages site" -Action { python scripts\build_site.py }
    }

    if (-not $SkipWebBuild) {
        Push-Location (Join-Path $repoRoot "web")
        try {
            Invoke-Step -Name "Install web dependencies" -Action { npm ci }
            Invoke-Step -Name "Build Vercel frontend" -Action { npm run build }
        }
        finally {
            Pop-Location
        }
    }

    Write-Host ""
    Write-Host "MVP refresh complete." -ForegroundColor Green
    Write-Host "Review changes with: git status --short"
}
finally {
    Pop-Location
}
