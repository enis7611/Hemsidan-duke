<#
  Bygger en undersida: mall/prefix.html + innehållsfil + mall/suffix.html → <Ut>/<filnamn>.
  Innehållsfilen börjar med en metadata-kommentar (title, description, page-css), se mall/komponenter.md.
  Kör: pwsh -File mall/bygg-sida.ps1 -Innehall mall/innehall/extendmqtt.html
#>
param(
  [Parameter(Mandatory)][string]$Innehall,
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

$namn = [IO.Path]::GetFileName($Innehall)
if ($namn -eq 'index.html') { throw 'index.html är handredigerad och byggs aldrig av bygg-sida.ps1' }
if ($namn -cnotmatch '^[a-z0-9-]+\.html$') { throw "Otillåtet filnamn '$namn': bara a-z, 0-9 och bindestreck (å/ä/ö → a/a/o)" }

$raw = Las-Lf $Innehall
# Felkodade tecken från en råfil som inte var UTF-8: ersättningstecken, eller UTF-8 läst som Windows-1252 (å → Ã¥).
if ($raw -cmatch '\uFFFD|\u00C3[\u0080-\u00BF]|\u00C2[\u00A0-\u00BF]') {
  throw "Innehållsfilen har felkodade tecken ('$($Matches[0])'). Råfilen var troligen inte UTF-8, så rätta å/ä/ö: $Innehall"
}
if (-not $raw.StartsWith("<!--`n")) { throw "Innehållsfilen saknar metadata-kommentar överst: $Innehall" }
$slut = $raw.IndexOf("`n-->`n")
if ($slut -lt 0) { throw "Metadata-kommentaren stängs inte med en egen rad '-->': $Innehall" }
$huvud = $raw.Substring(5, $slut - 5).Split("`n")
$kropp = $raw.Substring($slut + 5)

if ($huvud.Count -lt 3 -or -not $huvud[0].StartsWith('title:') -or -not $huvud[1].StartsWith('description:') -or $huvud[2] -ne 'page-css:') {
  throw "Metadata måste vara exakt raderna 'title:', 'description:', 'page-css:' i den ordningen: $Innehall"
}
$titel = $huvud[0].Substring(6).Trim()
$beskr = $huvud[1].Substring(12).Trim()
if (-not $titel) { throw "title saknar värde: $Innehall" }
if (-not $beskr) { throw "description saknar värde: $Innehall" }
if ($beskr.Contains('"')) { throw ('description får inte innehålla citattecken ("): ' + $Innehall) }
$cssRader = if ($huvud.Count -gt 3) { $huvud[3..($huvud.Count - 1)] } else { @() }
$css = if (($cssRader -join '').Trim()) { ($cssRader -join "`n") + "`n" } else { '' }

# String.Replace är ordagrann (ingen regex), så $, & och {{ i titeln är ofarliga.
# PAGE_CSS ersätts först så att en titel som råkar innehålla "{{PAGE_CSS}}" inte tolkas.
$prefix = (Las-Lf (Join-Path $PSScriptRoot 'prefix.html')).Replace('{{PAGE_CSS}}', $css).Replace('{{DESCRIPTION}}', $beskr).Replace('{{TITLE}}', $titel)
$suffix = Las-Lf (Join-Path $PSScriptRoot 'suffix.html')

New-Item -ItemType Directory -Force $Ut | Out-Null
$utfil = Join-Path (Resolve-Path $Ut).Path $namn
[IO.File]::WriteAllText($utfil, $prefix + $kropp + $suffix, $utf8)
$utfil
