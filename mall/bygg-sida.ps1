<#
  Bygger en undersida: mall/prefix.html + innehållsfil + mall/suffix.html → <Ut>/<sökväg>.
  Innehållsfilen börjar med en metadata-kommentar (title, description, [lang], [robots], page-css), se mall/komponenter.md.
  Utfilens väg: -Sokvag, annars vägen under mall/innehall/, annars filnamnet.
  Kör: pwsh -File mall/bygg-sida.ps1 -Innehall mall/innehall/extendmqtt.html
#>
param(
  [Parameter(Mandatory)][string]$Innehall,
  [string]$Sokvag,
  [string]$Ut = (Join-Path $PSScriptRoot '..\site')
)
$ErrorActionPreference = 'Stop'
$utf8 = [Text.UTF8Encoding]::new($false)

function Las-Lf([string]$sokvag) {
  if (-not (Test-Path -LiteralPath $sokvag -PathType Leaf)) { throw "Filen finns inte: $sokvag" }
  $strikt = [Text.UTF8Encoding]::new($false, $true)   # kastar på ogiltig UTF-8
  try { $text = $strikt.GetString([IO.File]::ReadAllBytes($sokvag)) }
  catch { throw "Filen är inte giltig UTF-8 (spara om den som UTF-8): $sokvag" }
  if ($text.Length -gt 0 -and $text[0] -eq [char]0xFEFF) { $text = $text.Substring(1) }
  $text -replace "`r`n", "`n"
}

if (-not $Sokvag) {
  $innehallRot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'innehall')) + [IO.Path]::DirectorySeparatorChar
  $full = [IO.Path]::GetFullPath($Innehall)
  $Sokvag = if ($full.StartsWith($innehallRot, [StringComparison]::OrdinalIgnoreCase)) { $full.Substring($innehallRot.Length) } else { [IO.Path]::GetFileName($full) }
}
$Sokvag = $Sokvag.Replace('\', '/')
if ($Sokvag -eq 'index.html') { throw 'index.html i roten är handredigerad och byggs aldrig av bygg-sida.ps1' }
$delar = $Sokvag.Split('/')
$namn = $delar[-1]
foreach ($d in ($delar | Select-Object -SkipLast 1)) {
  if ($d -cnotmatch '^[a-z0-9-]+$') { throw "Otillåtet mappnamn '$d' i '$Sokvag': bara a-z, 0-9 och bindestreck" }
}
if ($namn -cnotmatch '^[a-z0-9-]+\.html$') { throw "Otillåtet filnamn '$namn': bara a-z, 0-9 och bindestreck (å/ä/ö → a/a/o)" }
$rotvag = '../' * ($delar.Count - 1)

$raw = Las-Lf $Innehall
# Felkodade tecken från en råfil som inte var UTF-8: ersättningstecken, eller UTF-8 läst som Windows-1252 (å → Ã¥).
if ($raw -cmatch '\uFFFD|\u00C3[\u0080-\u00BF]|\u00C2[\u00A0-\u00BF]') {
  throw "Innehållsfilen har felkodade tecken ('$($Matches[0])'). Råfilen var troligen inte UTF-8, så rätta å/ä/ö: $Innehall"
}
if (-not $raw.StartsWith("<!--`n")) { throw "Innehållsfilen saknar metadata-kommentar överst: $Innehall" }
$slut = $raw.IndexOf("`n-->`n")
if ($slut -lt 5) { throw "Metadata-kommentaren stängs inte med en egen rad '-->': $Innehall" }
$huvud = $raw.Substring(5, $slut - 5).Split("`n")
$kropp = $raw.Substring($slut + 5)

if ($huvud.Count -lt 3 -or -not $huvud[0].StartsWith('title:') -or -not $huvud[1].StartsWith('description:')) {
  throw "Metadata måste börja med raderna 'title:' och 'description:': $Innehall"
}
$titel = $huvud[0].Substring(6).Trim()
$beskr = $huvud[1].Substring(12).Trim()
if (-not $titel) { throw "title saknar värde: $Innehall" }
if (-not $beskr) { throw "description saknar värde: $Innehall" }
if ($beskr.Contains('"')) { throw ('description får inte innehålla citattecken ("): ' + $Innehall) }

# Valfria rader före page-css:, i ordningen lang, robots
$lang = 'sv'; $robots = ''
$i = 2
if ($huvud[$i] -and $huvud[$i].StartsWith('lang:')) { $lang = $huvud[$i].Substring(5).Trim(); $i++ }
if ($huvud[$i] -and $huvud[$i].StartsWith('robots:')) { $robots = $huvud[$i].Substring(7).Trim(); $i++ }
if ($lang -cnotin 'sv', 'en') { throw "lang måste vara sv eller en (fick '$lang'): $Innehall" }
if ($robots -and $robots -cnotmatch '^[a-z]+(, ?[a-z]+)*$') { throw "Ogiltigt robots-värde '$robots': $Innehall" }
if ($huvud[$i] -ne 'page-css:') { throw "Metadata: efter title/description (och ev. lang, robots) ska raden 'page-css:' komma: $Innehall" }
$cssRader = if ($huvud.Count -gt $i + 1) { $huvud[($i + 1)..($huvud.Count - 1)] } else { @() }
$css = if (($cssRader -join '').Trim()) { ($cssRader -join "`n") + "`n" } else { '' }

$robotsMeta = if ($robots) { "`n<meta name=`"robots`" content=`"$robots`">" } else { '' }
$enStart = if ($lang -eq 'en') { "<script>toggleLang();</script>`n" } else { '' }

# String.Replace är ordagrann (ingen regex). TITLE sist så att en titel med "{{…}}" aldrig tolkas.
$prefix = (Las-Lf (Join-Path $PSScriptRoot 'prefix.html')).Replace('{{PAGE_CSS}}', $css).Replace('{{ROOT}}', $rotvag).Replace('{{LANG}}', $lang).Replace('{{ROBOTS}}', $robotsMeta).Replace('{{DESCRIPTION}}', $beskr).Replace('{{TITLE}}', $titel)
$suffix = (Las-Lf (Join-Path $PSScriptRoot 'suffix.html')).Replace('{{ROOT}}', $rotvag).Replace('{{EN_START}}', $enStart)

New-Item -ItemType Directory -Force $Ut | Out-Null
$utfil = Join-Path (Resolve-Path $Ut).Path ($Sokvag.Replace('/', [IO.Path]::DirectorySeparatorChar))
New-Item -ItemType Directory -Force (Split-Path $utfil) | Out-Null
[IO.File]::WriteAllText($utfil, $prefix + $kropp + $suffix, $utf8)
$utfil
