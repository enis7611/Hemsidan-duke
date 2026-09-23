# Tester för mall/bygg-sida.ps1. Kör: pwsh -File mall/test/test-bygg-sida.ps1
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot\..\..").Path
$bygg = Join-Path $root 'mall\bygg-sida.ps1'
$tmp  = Join-Path ([IO.Path]::GetTempPath()) ("bygg-test-" + [guid]::NewGuid())
New-Item -ItemType Directory $tmp | Out-Null
$utf8 = [Text.UTF8Encoding]::new($false)
$script:fel = 0

function Ok($villkor, $text) {
  if ($villkor) { Write-Host "OK   $text" } else { Write-Host "FEL  $text" -ForegroundColor Red; $script:fel++ }
}
function Kastar([scriptblock]$block, $text) {
  try { & $block | Out-Null; Ok $false "$text (inget fel kastades)" } catch { Ok $true "$text [$($_.Exception.Message)]" }
}
function Skriv($namn, $text) { $p = Join-Path $tmp $namn; [IO.File]::WriteAllText($p, $text, $utf8); $p }

$giltig = "<!--`ntitle: Test | Duke Systems AB`ndescription: Beskrivning`npage-css:`n-->`n<section>Hej</section>`n"

# 1. De tre undersidorna byggs om byte-identiskt från sina innehållsfiler
$ut = Join-Path $tmp 'ut'; New-Item -ItemType Directory $ut | Out-Null
foreach ($n in 'extendmqtt', 'simulationsmcp', 'simulationsmcp-build') {
  & $bygg -Innehall (Join-Path $root "mall\innehall\$n.html") -Ut $ut | Out-Null
  $a = [IO.File]::ReadAllBytes((Join-Path $root "site\$n.html"))
  $b = [IO.File]::ReadAllBytes((Join-Path $ut "$n.html"))
  Ok ([Linq.Enumerable]::SequenceEqual($a, $b)) "$n.html byggs om byte-identiskt"
}

# 2. Tom page-css ger ett tomt <style>-block och platshållarna ersätts
$p = Skriv 'enkel.html' $giltig
& $bygg -Innehall $p -Ut $ut | Out-Null
$s = [IO.File]::ReadAllText((Join-Path $ut 'enkel.html'))
Ok ($s.Contains("<title>Test | Duke Systems AB</title>")) "titel ersatt"
Ok ($s.Contains('<meta name="description" content="Beskrivning">')) "beskrivning ersatt"
Ok ($s.Contains("<style>`n</style>`n`n<section>Hej</section>`n<footer>")) "tom sid-CSS + innehåll på rätt plats"
Ok (-not $s.Contains('{{')) "inga platshållare kvar"

# 3. CRLF + BOM i innehållsfilen → utdata LF utan BOM (Review Focus 1)
$p = Join-Path $tmp 'crlf.html'
[IO.File]::WriteAllText($p, $giltig.Replace("`n", "`r`n"), [Text.UTF8Encoding]::new($true))
& $bygg -Innehall $p -Ut $ut | Out-Null
$bytes = [IO.File]::ReadAllBytes((Join-Path $ut 'crlf.html'))
Ok (-not ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB)) "ingen BOM i utdata"
Ok ($bytes -notcontains 13) "inga CR i utdata"

# 4. Windows-1252-fil avvisas (Review Focus 2)
$p = Join-Path $tmp 'ansi.html'
# 0xE5 = 'å' i Windows-1252, ogiltig som ensam byte i UTF-8
[IO.File]::WriteAllBytes($p, [byte[]]($utf8.GetBytes($giltig) + [byte]0x70 + [byte]0xE5 + [byte]0x0A))
Kastar { & $bygg -Innehall $p -Ut $ut } "icke-UTF-8 avvisas"

# 5. Specialtecken ordagrant; citattecken i description avvisas (Review Focus 3)
$p = Skriv 'special.html' ($giltig.Replace('title: Test', 'title: Pris $1 & {{x}}'))
& $bygg -Innehall $p -Ut $ut | Out-Null
Ok ([IO.File]::ReadAllText((Join-Path $ut 'special.html')).Contains('<title>Pris $1 & {{x}} | Duke Systems AB</title>')) "titel med `$ & {{ ordagrant"
$p = Skriv 'citat.html' ($giltig.Replace('description: Beskrivning', 'description: Ett "citat"'))
Kastar { & $bygg -Innehall $p -Ut $ut } "citattecken i description avvisas"

# 6. Otillåtna filnamn (Review Focus 5)
$p = Skriv 'index.html' $giltig
Kastar { & $bygg -Innehall $p -Ut $ut } "index.html byggs aldrig"
$p = Skriv 'försäkring.html' $giltig
Kastar { & $bygg -Innehall $p -Ut $ut } "filnamn med å/ä/ö avvisas"

# 7. Trasig metadata
$p = Skriv 'utanmeta.html' "<section>Hej</section>`n"
Kastar { & $bygg -Innehall $p -Ut $ut } "saknad metadata-kommentar avvisas"
$p = Skriv 'tomtitel.html' ($giltig.Replace('title: Test | Duke Systems AB', 'title: '))
Kastar { & $bygg -Innehall $p -Ut $ut } "tom titel avvisas"
$p = Skriv 'ejstangd.html' "<!--`ntitle: T`ndescription: D`npage-css:`n<section>Hej</section>`n"
Kastar { & $bygg -Innehall $p -Ut $ut } "ostängd metadata avvisas"

Remove-Item -Recurse -Force $tmp
if ($script:fel) { Write-Host "$($script:fel) test fallerade" -ForegroundColor Red; exit 1 } else { Write-Host "Alla test OK"; exit 0 }
