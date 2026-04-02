# Проверка всех эндпоинтов API.
# Использование:
#   .\test_endpoints.ps1          # Go-сервер на :8080 (по умолчанию)
#   .\test_endpoints.ps1 -Port 5000  # Python/Flask-сервер на :5000

param(
    [int]$Port = 8080
)

$Base = "http://localhost:$Port"
$Pass = 0
$Fail = 0

function Check-Endpoint {
    param(
        [string]$Label,
        [int]$ExpectedStatus,
        [int]$ActualStatus,
        [string]$Body
    )
    if ($ActualStatus -eq $ExpectedStatus) {
        Write-Host "[PASS] $Label -> HTTP $ActualStatus" -ForegroundColor Green
        $script:Pass++
    } else {
        Write-Host "[FAIL] $Label -> expected HTTP $ExpectedStatus, got HTTP $ActualStatus" -ForegroundColor Red
        $script:Fail++
    }
    Write-Host "       $Body"
    Write-Host ""
}

function Invoke-API {
    param(
        [string]$Method = "GET",
        [string]$Url,
        [string]$Body = $null
    )
    try {
        $params = @{
            Method  = $Method
            Uri     = $Url
            Headers = @{ "Content-Type" = "application/json" }
        }
        if ($Body) { $params["Body"] = $Body }

        $response = Invoke-WebRequest @params -ErrorAction Stop
        return @{ Status = $response.StatusCode; Body = $response.Content }
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        $body   = $_.ErrorDetails.Message
        return @{ Status = $status; Body = $body }
    }
}

Write-Host "=== Testing API on $Base ===" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# POST /adduser — успешное создание
# ---------------------------------------------------------------------------
$r = Invoke-API -Method POST -Url "$Base/adduser" -Body '{"name":"Alice"}'
Check-Endpoint "POST /adduser (valid name)" 201 $r.Status $r.Body

# Извлекаем ID
$UserId = ($r.Body | ConvertFrom-Json).id

# ---------------------------------------------------------------------------
# POST /adduser — пустое имя → 400
# ---------------------------------------------------------------------------
$r = Invoke-API -Method POST -Url "$Base/adduser" -Body '{"name":""}'
Check-Endpoint "POST /adduser (empty name -> 400)" 400 $r.Status $r.Body

# ---------------------------------------------------------------------------
# POST /adduser — нет поля name → 400
# ---------------------------------------------------------------------------
$r = Invoke-API -Method POST -Url "$Base/adduser" -Body '{}'
Check-Endpoint "POST /adduser (missing name -> 400)" 400 $r.Status $r.Body

# ---------------------------------------------------------------------------
# GET /user/{id} — найден
# ---------------------------------------------------------------------------
$id = if ($UserId) { $UserId } else { 1 }
$r = Invoke-API -Url "$Base/user/$id"
Check-Endpoint "GET /user/$id (found -> 200)" 200 $r.Status $r.Body

# ---------------------------------------------------------------------------
# GET /user/{id} — не найден → 404
# ---------------------------------------------------------------------------
$r = Invoke-API -Url "$Base/user/99999"
Check-Endpoint "GET /user/99999 (not found -> 404)" 404 $r.Status $r.Body

# ---------------------------------------------------------------------------
# GET /activate/{id}
# ---------------------------------------------------------------------------
$r = Invoke-API -Url "$Base/activate/$id"
Check-Endpoint "GET /activate/$id (-> 200)" 200 $r.Status $r.Body

# ---------------------------------------------------------------------------
# POST /activate/{id}
# ---------------------------------------------------------------------------
$r = Invoke-API -Method POST -Url "$Base/activate/$id"
Check-Endpoint "POST /activate/$id (-> 200)" 200 $r.Status $r.Body

# ---------------------------------------------------------------------------
# GET /slow
# ---------------------------------------------------------------------------
$r = Invoke-API -Url "$Base/slow"
Check-Endpoint "GET /slow (-> 202)" 202 $r.Status $r.Body

# ---------------------------------------------------------------------------
# GET /wrong
# ---------------------------------------------------------------------------
$r = Invoke-API -Url "$Base/wrong"
Check-Endpoint "GET /wrong (-> 500)" 500 $r.Status $r.Body

# ---------------------------------------------------------------------------
# Итог
# ---------------------------------------------------------------------------
Write-Host "=== Results ===" -ForegroundColor Cyan
Write-Host "PASS: $Pass" -ForegroundColor Green
Write-Host "FAIL: $Fail" -ForegroundColor Red
if ($Fail -gt 0) { exit 1 }
