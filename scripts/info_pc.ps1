$cpu  = Get-CimInstance Win32_Processor | Select-Object -First 1
$cs   = Get-CimInstance Win32_ComputerSystem
$os   = Get-CimInstance Win32_OperatingSystem
$out  = @()
$out += "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
$out += "Fabricante y modelo: $($cs.Manufacturer) $($cs.Model)"
$out += "Procesador: $($cpu.Name)"
$out += "Nucleos fisicos: $($cpu.NumberOfCores) | Hilos logicos: $($cpu.NumberOfLogicalProcessors) | Frecuencia maxima: $($cpu.MaxClockSpeed) MHz"
$out += "Memoria RAM total: $([math]::Round($cs.TotalPhysicalMemory / 1GB, 1)) GB"
$out += "Memoria RAM libre en este momento: $([math]::Round($os.FreePhysicalMemory / 1MB, 1)) GB"
$out += "Sistema operativo: $($os.Caption) (version $($os.Version))"
$out += ""
$out += "Discos:"
try {
  Get-PhysicalDisk | ForEach-Object { $out += "  $($_.FriendlyName) | tipo: $($_.MediaType) | $([math]::Round($_.Size / 1GB)) GB" }
} catch { $out += "  (no disponible)" }
$out += ""
$out += "Configuracion de WSL (.wslconfig):"
$wsl = Join-Path $env:USERPROFILE ".wslconfig"
if (Test-Path $wsl) { $out += Get-Content $wsl } else { $out += "  (no existe: Docker usa la configuracion por defecto de WSL)" }
$out += ""
$out += "Plan de energia activo:"
$out += (powercfg /getactivescheme)
$destino = Join-Path (Split-Path -Parent $PSScriptRoot) "resultados\info_pc.txt"
$out | Out-File -FilePath $destino -Encoding utf8
Write-Host "Informacion guardada en resultados\info_pc.txt"
