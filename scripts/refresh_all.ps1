param(
    [switch]$SkipWebBuild,
    [switch]$SkipPagesBuild,
    [int]$ProposalSyncRetries = 3
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
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed ($LASTEXITCODE): $Name"
    }
}

function Invoke-StepWithRetry {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action,
        [Parameter(Mandatory = $true)]
        [int]$MaxAttempts,
        [int]$DelaySeconds = 20
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt += 1) {
        Write-Host ""
        Write-Host "==> $Name (attempt $attempt/$MaxAttempts)" -ForegroundColor Cyan
        & $Action
        if ($LASTEXITCODE -eq 0) {
            return
        }
        if ($attempt -lt $MaxAttempts) {
            Write-Host "Retrying in $DelaySeconds seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds $DelaySeconds
            continue
        }
        throw "Step failed after $MaxAttempts attempts ($LASTEXITCODE): $Name"
    }
}

Push-Location $repoRoot
try {
    Invoke-Step -Name "Sync Gnars web sources" -Action { python scripts\sync_gnars.py }
    Invoke-StepWithRetry -Name "Sync proposal archive" -Action { python scripts\sync_proposals.py } -MaxAttempts $ProposalSyncRetries
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
            Write-Host ""
            Write-Host "==> Install web dependencies" -ForegroundColor Cyan
            npm ci
            if ($LASTEXITCODE -ne 0) {
                Write-Host "npm ci failed; retrying with npm install" -ForegroundColor Yellow
                npm install
                if ($LASTEXITCODE -ne 0) {
                    throw "Step failed: Install web dependencies"
                }
            }
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
