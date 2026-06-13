# ExtendMQTT — Product Requirements Document

**MQTT-integration för ExtendSim**
*Custom block + native DLL för bidirektionell kommunikation mellan simuleringsmodeller och externa enheter*

| | |
|---|---|
| **Dokumentversion** | v0.1 (initial draft) |
| **Datum** | 2026-05-04 |
| **Författare** | Jonas / Duke Systems AB |
| **Status** | Draft – under granskning |
| **Målprodukt** | ExtendSim 10 / 2024 (64-bit) |
| **Distribution** | Open source + kommersiell support |

---

## Innehållsförteckning

1. [Executive Summary](#1-executive-summary)
2. [Bakgrund och problemformulering](#2-bakgrund-och-problemformulering)
3. [Mål och framgångskriterier](#3-mål-och-framgångskriterier)
4. [Omfattning](#4-omfattning)
5. [Användare och personas](#5-användare-och-personas)
6. [Arkitektur](#6-arkitektur)
7. [DLL-design](#7-dll-design)
8. [ModL-block design](#8-modl-block-design)
9. [Topic-konventioner och payload-format](#9-topic-konventioner-och-payload-format)
10. [Exempelmodeller](#10-exempelmodeller)
11. [Icke-funktionella krav](#11-icke-funktionella-krav)
12. [Användarflöden](#12-användarflöden)
13. [Risker och antaganden](#13-risker-och-antaganden)
14. [Utvecklingsplan](#14-utvecklingsplan)
15. [Teststrategi](#15-teststrategi)
16. [Dokumentationsplan](#16-dokumentationsplan)
17. [Öppna frågor](#17-öppna-frågor)
18. [Appendix](#18-appendix)

---

## 1. Executive Summary

ExtendMQTT är ett tillägg till ExtendSim som gör simuleringsmodeller till en fullvärdig deltagare i moderna IoT-, automation- och digital twin-arkitekturer. Lösningen består av en native Windows-DLL skriven i C++ som kapslar in en MQTT-klient (Eclipse Paho), samt en uppsättning ModL-baserade custom blocks som exponerar publish/subscribe-funktionalitet inuti ExtendSim-modeller på samma sätt som inbyggda bibliotekskomponenter.

Med ExtendMQTT kan en ExtendSim-modell ta emot mätvärden från fysiska sensorer i realtid, styras av externa PLC:er eller controllers, publicera prediktioner till instrumentpaneler (Grafana, Home Assistant, Node-RED), eller agera som en digital twin som körs parallellt med en fysisk process. Lösningen är generellt designad och stödjer både snabbsimulering (offline batch-analys) och realtidssimulering (hardware-in-the-loop).

Produkten är primärt riktad till Duke Systems ABs befintliga ExtendSim-kundbas i Norden, samt internationella ExtendSim-användare via det öppna communityt. Den positioneras som en gratis open source-komponent med möjlighet till kommersiell support, integrationsuppdrag och kundanpassningar via Duke Systems AB.

### 1.1 Centrala mål

- **Modernisera ExtendSim** som plattform genom att tillgängliggöra MQTT — den de facto-standard som idag används inom industriell IoT, smarta hem och edge-arkitekturer.
- **Möjliggöra digital twin-användning** av ExtendSim-modeller, där simuleringen körs synkroniserat med eller parallellt med en fysisk process.
- **Förenkla hardware-in-the-loop-testning** av styrsystem genom att låta riktiga PLC:er, controllers eller embedded systems kommunicera med en simulerad process via MQTT.
- **Bygga ett distributionsbart bibliotek** som följer ExtendSims standarder för custom blocks och kan installeras av en användare utan C++-kunskap.
- **Stärka Duke Systems position** som teknisk thought leader på den nordiska marknaden och som kompetent integrationspartner för komplexa ExtendSim-projekt.

### 1.2 Leveransform

ExtendMQTT levereras som ett installerbart paket innehållande:

- `ExtendMQTT.dll` (64-bit) — den native MQTT-klienten.
- Ett ExtendSim-bibliotek (`.lix`) med fyra block: `MQTT_Connection`, `MQTT_Publish`, `MQTT_Subscribe` och `MQTT_Bridge`.
- Fem exempelmodeller (`.mox`) som demonstrerar varje block i isolation och i kombination.
- Dokumentation: installationsguide, blockreferens, topic-konventioner samt en troubleshooting-guide.
- Stödfiler: Mosquitto-konfiguration, Python-publishers för testning samt en Node-RED-flow för PLC-emulering.

---

## 2. Bakgrund och problemformulering

### 2.1 Affärskontext

Duke Systems AB har distribuerat ExtendSim på den nordiska marknaden sedan 1988 och har en lång historik av att bygga kundanpassningar, custom blocks och systemintegrationer. ExtendSim är en kraftfull simuleringsplattform som täcker både diskreta händelsesimuleringar, kontinuerliga modeller och hybridmodeller, men plattformens ekosystem för extern kommunikation har historiskt varit begränsat till COM/ActiveX, ODBC och fil-IO.

Sedan tidigt 2020-tal har MQTT etablerats som dominerande standard för kommunikation mellan distribuerade system inom industriell automation, smarta hem, fordonstelematik och edge-baserade AI-system. ExtendSim saknar idag en first-class integration med MQTT, vilket gör det svårt att använda plattformen i moderna digital twin-arkitekturer eller i miljöer där simuleringen behöver interagera med fysisk hårdvara i realtid.

Parallellt har Duke Systems byggt SimulationsMCP — en MCP-server som bryggar ExtendSim mot AI-assistenter via COM-automation. ExtendMQTT är en logisk komplettering: medan SimulationsMCP fokuserar på AI-agenters interaktion med modeller, fokuserar ExtendMQTT på maskin-till-maskin-kommunikation i realtid, ofta utan AI i loopen.

### 2.2 Problembeskrivning

Idag finns inget enkelt sätt att låta en ExtendSim-modell:

- Ta emot strömmande data från fysiska sensorer eller IoT-enheter under pågående simulering.
- Skicka simuleringsresultat till externa system i realtid (BI-verktyg, dashboards, AI-modeller).
- Styra eller styras av externa kontrollsystem (PLC, SCADA, embedded controllers) i ett HIL-scenario.
- Synkronisera tillstånd med en fysisk process för digital twin-applikationer.
- Delta i loosely coupled multi-system-arkitekturer där varje deltagare kommunicerar via en gemensam message broker.

Befintliga workarounds — som att skriva data till en databas eller fil och låta en extern bryggprocess publicera den vidare — introducerar latens, ökar komplexitet och kräver att kunden bygger och underhåller egen integrationskod. Detta begränsar i praktiken antalet projekt där ExtendSim är en realistisk lösning.

### 2.3 Varför just MQTT?

MQTT (MQ Telemetry Transport) är en lättviktig publish/subscribe-protokollstandard som har följande egenskaper som gör den lämplig för ExtendSim-integration:

- **Brett standardiserat** — ISO/IEC 20922:2016, stödd av i princip alla industriella IoT-plattformar, OPC UA-broar, Home Assistant, Node-RED, AWS IoT, Azure IoT Hub, Google Cloud IoT m.fl.
- **Lättviktigt** — minimal protokollöverhead jämfört med HTTP eller AMQP, vilket är viktigt när simuleringen producerar tusentals meddelanden per sekund.
- **Decoupled arkitektur** — pub/sub-modellen innebär att simuleringen inte behöver känna till externa konsumenter och vice versa. Detta passar väl ihop med ExtendSims modulära blockmodell.
- **QoS-nivåer** — MQTT erbjuder tre QoS-nivåer (0, 1, 2) som låter modellbyggaren välja mellan låg latens och leveransgaranti per meddelande.
- **Mogna klientbibliotek** — Eclipse Paho och Mosquitto erbjuder välunderhållna C-bibliotek med Windows-stöd, vilket är en förutsättning för att kunna länka in funktionaliteten i en ExtendSim-DLL.

### 2.4 Konkurrentsituation

Inga kommersiella eller öppna MQTT-bibliotek för ExtendSim är kända i nuläget. Andra simuleringsplattformar har lösningar i varierande mognadsgrad:

- **AnyLogic** har Java-baserad MQTT-integration via tredjepartsbibliotek (Eclipse Paho Java).
- **Simio** kan integrera via .NET-API:et och MQTTnet, men kräver C#-kodning.
- **Arena** saknar officiellt stöd och kräver VBA + COM-bryggor.
- **Plant Simulation** har OPC UA-stöd men inget native MQTT.

ExtendMQTT positionerar sig därför som en av de första turnkey MQTT-integrationerna inom det generella simuleringsverktygsmarknaden, och som den första för ExtendSim-användare.

---

## 3. Mål och framgångskriterier

### 3.1 Affärsmål

| Nr | Mål | Mätbart utfall |
|----|-----|----------------|
| **B1** | Stärka Duke Systems position som teknisk ExtendSim-partner i Norden. | Minst 3 referenscase publicerade inom 12 månader efter release. |
| **B2** | Generera nya kundprojekt inom HIL-testning och digital twin. | Minst 2 betalda integrationsuppdrag inom 18 månader. |
| **B3** | Etablera Duke Systems som thought leader i ExtendSim-communityt. | Konferenspresentation på ExtendSim User Conference eller motsvarande. |
| **B4** | Skapa lead generation-kanal genom open source-distribution. | 100+ GitHub-stjärnor och 10+ externa nedladdningar inom 6 månader. |
| **B5** | Bygga internt återanvändbar plattform för framtida integrationer (OPC UA, Kafka). | Arkitektur dokumenterad och hexagonal struktur etablerad i kodbas. |

### 3.2 Tekniska mål

| Nr | Mål | Acceptanskriterium |
|----|-----|--------------------|
| **T1** | Native DLL utan externa runtime-beroenden förutom Windows-systembibliotek. | DLL:en kör på en ren Windows 10/11 utan Visual C++ Redistributable-installation. |
| **T2** | Publish-latens under 5 ms median i loopback (broker på samma maskin). | Mätt med 10 000 meddelanden, QoS 0, payload 64 byte. |
| **T3** | Subscribe-genomströmning minst 5 000 meddelanden/sekund. | Test med synthetic load, kö ska inte överflöda under 10 minuter. |
| **T4** | Auto-reconnect vid broker-bortfall. | Simuleringen fortsätter och ansluter automatiskt inom 30 sekunder efter att brokern återkommer. |
| **T5** | Stöd för MQTT 3.1.1 i v1.0; MQTT 5.0 i v1.1. | Klient kan ansluta till Mosquitto, HiveMQ och AWS IoT Core. |
| **T6** | TLS-stöd inklusive självsignerade certifikat. | Kan ansluta till broker via `ssl://` med konfigurerbart CA-cert. |
| **T7** | Robust felhantering — ingen krasch i ExtendSim vid felkonfiguration. | Felaktiga parametrar returnerar felkod, INGEN exception/access violation. |
| **T8** | Diagnostisk loggning via fil. | Konfigurerbar logfil med tidstämplade händelser, max-storlek och rotering. |

### 3.3 Användarmål

För en typisk ExtendSim-modellbyggare ska följande vara sant efter installation:

- En första fungerande publish/subscribe-modell ska kunna byggas inom 15 minuter.
- Ingen C++-kunskap eller kommandoradsverktyg ska behövas för normal användning.
- Felmeddelanden ska vara förståeliga på svenska och engelska och peka på vanliga orsaker (broker nere, fel port, fel credentials, fel topic).
- Blocken ska följa ExtendSims visuella konventioner och dialogmönster.

---

## 4. Omfattning

### 4.1 In scope för v1.0

- MQTT 3.1.1 över TCP och TLS.
- Användarautentisering med username/password.
- Publish (QoS 0/1/2) och Subscribe med wildcard-stöd (`+` och `#`).
- Last Will and Testament (LWT).
- Auto-reconnect med exponential backoff.
- JSON-payload helpers (extrahera fält som number/string).
- Realtidssynkronisering (sim-tid följer wall-clock).
- Bounded message queue med konfigurerbar storlek.
- Stöd för en samtidig broker-anslutning per modell.

### 4.2 Out of scope för v1.0 (planerat senare)

- MQTT 5.0 features (user properties, shared subscriptions, topic aliases).
- Klientcertifikatautentisering (mTLS).
- Multipla samtidiga broker-anslutningar.
- Persistent sessions med disk-baserad köning.
- Bridge mode mellan flera brokers.
- WebSocket-transport (`ws://` och `wss://`).
- Cluster-stöd (Sparkplug B, EMQX cluster awareness).
- Inbyggd MQTT-broker (vi förlitar oss alltid på extern broker).

### 4.3 Explicit utelämnat

- OPC UA — separat produkt om efterfrågan finns.
- AMQP / Kafka / Redis pub-sub — utvärderas baserat på kunddialog.
- Linux-stöd för DLL:en — ExtendSim körs primärt på Windows.
- Mac-stöd — samma orsak.

---

## 5. Användare och personas

### 5.1 Persona 1: Anders, simuleringsingenjör

- **Roll:** Senior simuleringsingenjör hos en svensk pappersbruksleverantör.
- **Bakgrund:** 20 års erfarenhet av ExtendSim, bygger processmodeller för pappersmaskiner och deras stödsystem.
- **Behov:** Vill validera nya styrstrategier mot en simulerad processmodell innan implementation i fysisk PLC.
- **Smärtpunkt:** Måste idag exportera simdata till CSV och köra styrlogik i separat verktyg, vilket är långsamt och felbenäget.
- **Hur ExtendMQTT hjälper:** Exempel 3 (PLC-styrd produktionslina) löser hans use case direkt.

### 5.2 Persona 2: Maria, R&D-ingenjör inom IoT

- **Roll:** R&D-ingenjör i ett startup som bygger IoT-baserade energiövervakningssystem.
- **Bakgrund:** Bekväm med Python, Node-RED och MQTT. Begränsad ExtendSim-erfarenhet.
- **Behov:** Vill testa hur hennes algoritm för lastbalansering presterar mot en simulerad fastighetsportfölj.
- **Smärtpunkt:** ExtendSim känns som en sluten värld; vill att simuleringen ska vara en "server" som hennes Python-kod kan tala med.
- **Hur ExtendMQTT hjälper:** MQTT är hennes naturliga gränssnitt; hon kan köra sin Python-kod oförändrad och låta ExtendSim agera som digital tvilling.

### 5.3 Persona 3: Erik, AI-utvecklare

- **Roll:** Senior utvecklare som bygger AI-baserade beslutssystem.
- **Bakgrund:** Stark inom .NET, Python och AI/ML. Använder ExtendSim sporadiskt.
- **Behov:** Vill träna en RL-agent (reinforcement learning) mot en simulerad miljö med realistiska processdynamik.
- **Smärtpunkt:** Custom Gym-environments är dyra att bygga; vill återanvända befintlig ExtendSim-modell.
- **Hur ExtendMQTT hjälper:** RL-agenten talar MQTT, ExtendSim agerar simulerad miljö med rika fysikbaserade modeller.

### 5.4 Persona 4: Lars, konsult hos Duke Systems

- **Roll:** Senior konsult hos Duke Systems AB.
- **Bakgrund:** Bygger kundanpassningar i ExtendSim. C++-kunskap men föredrar deklarativa lösningar.
- **Behov:** Levererar HIL-projekt åt kunder och behöver återanvändbara byggblock.
- **Hur ExtendMQTT hjälper:** Sparar veckor av utvecklingstid per projekt; kan fokusera på kundens domänlogik istället för integrationsmellanlager.

---

## 6. Arkitektur

### 6.1 Översikt

ExtendMQTT består av tre logiska lager:

- **ModL-lagret** — ExtendSim-blocken som modellbyggaren placerar ut på arbetsytan. Blocken har dialogrutor, in- och utgångar och hanterar simuleringseventslivscykeln (`InitSim`, item-flow, `ScheduledEvent`, `EndSim`).
- **Bryggan (DLL-API)** — En tunn C-ABI som ModL kan anropa via `CallExternal`. Detta lager hanterar string marshalling, calling convention och felöversättning.
- **MQTT-kärnan** — Den interna C++-implementationen som äger Paho-klienten, meddelandekön, trådhantering och loggning.

Designen följer hexagonal arkitektur: ModL-lagret är en "adapter" som kan bytas ut (t.ex. mot ett .NET-API eller ett kommandoradsverktyg) utan att ändra kärnan. På sikt möjliggör detta delning med SimulationsMCP och andra Duke-verktyg.

### 6.2 Komponentdiagram

```
+--------------------------------------------------------------+
|  ExtendSim Process (32-bit eller 64-bit)                     |
|                                                              |
|  +------------------+  +------------------+                  |
|  | MQTT_Connection  |  | MQTT_Publish     |                  |
|  |   (singleton)    |  |   (per topic)    |                  |
|  +--------+---------+  +--------+---------+                  |
|           |                     |                            |
|           |    CallExternal     |                            |
|           v                     v                            |
|  +-------------------------------------------+               |
|  | ExtendMQTT.dll (C++ / Paho MQTT C)        |               |
|  |                                           |               |
|  |  +-------------------+  +-------------+   |               |
|  |  | Public C-API      |  | Logger      |   |               |
|  |  +-------------------+  +-------------+   |               |
|  |  +-------------------+  +-------------+   |               |
|  |  | Paho async client |  | MPSC queue  |   |               |
|  |  +---------+---------+  +------+------+   |               |
|  +------------|---------------------|--------+               |
+---------------|---------------------|------------------------+
                | TCP/TLS             | callback thread
                v                     ^
         +-------------+               |
         | MQTT broker |---------------+
         +------+------+
                |
    +-----------+-----------+-----------+
    |           |           |           |
    v           v           v           v
 Sensors      PLC      Node-RED   AI-clients
```

### 6.3 Trådmodell

Trådhantering är den mest kritiska arkitekturella detaljen, och felaktig design här leder till svårfelsökta bugg. ExtendMQTT använder följande modell:

- **ExtendSim-tråden** (huvudtråd) — kör all ModL-kod, all simuleringslogik och anropar DLL-funktioner. Är aldrig blockerad mer än några millisekunder.
- **Paho IO-tråden** — intern Paho-tråd som hanterar TCP-IO, TLS-handshake och keep-alive. Skapas och hanteras av Paho.
- **Paho callback-tråden** — intern Paho-tråd som anropar `OnMessageArrived`. Här konverteras Paho-meddelanden till våra interna `IncomingMessage`-strukturer och köas i den thread-safe MPSC-kön.

All synkronisering sker via `std::mutex` och `std::atomic`. Inga lås hålls under callback-anrop till ExtendSim eftersom ExtendSim aldrig anropas från callback-tråden — modellen pollar istället via `MQTT_HasMessage` / `MQTT_PollMessage`.

### 6.4 Tillståndsmodell

DLL:en har global state (en singleton) eftersom ExtendSim laddar DLL:en en gång per process. Detta är medvetet — multipla samtidiga broker-anslutningar är out of scope för v1.0. Tillstånden är:

| Tillstånd | Beskrivning | Tillåtna övergångar |
|-----------|-------------|---------------------|
| **Idle** | Ingen klient skapad. Initialvärde efter DLL-load. | → Connecting (`MQTT_Connect`) |
| **Connecting** | Klient skapad, anslutning pågår. Synkron väntan upp till 10 sek. | → Connected (success), → Idle (failure) |
| **Connected** | Aktiv anslutning. Pub/Sub fungerar. | → Reconnecting (broker bortfall), → Idle (Disconnect) |
| **Reconnecting** | Anslutning förlorad, automatisk återanslutning pågår. | → Connected (success), → Idle (max retries eller Disconnect) |

### 6.5 Kommunikationsmönster

#### 6.5.1 Publicering (synkront ur ModL-perspektiv)

1. ModL-block tar emot ett item på sin in-port.
2. Block bygger payload (sträng, double eller JSON).
3. Block anropar `MQTT_PublishString/Double/Json` via CallExternal.
4. DLL kontrollerar connected-flagga och anropar `MQTTAsync_sendMessage` (fire-and-forget för QoS 0).
5. DLL returnerar omedelbart med statuskod.
6. Block skickar item vidare på ut-porten.

#### 6.5.2 Prenumeration (asynkront via polling)

1. `MQTT_Connection`-blocket anropar `MQTT_Connect` i `InitSim`.
2. `MQTT_Subscribe`-blocket anropar `MQTT_Subscribe` i `InitSim` och schemalägger sig själv för polling.
3. Inkommande meddelanden levereras av Paho till callback-tråden, som köar dem.
4. Vid varje schemalagd polling anropar blocket `MQTT_HasMessage` och `MQTT_PollMessage` tills kön är tom.
5. För varje meddelande triggar blocket sin event-output, som downstream-block kan reagera på.
6. Blocket schemalägger nästa polling.

---

## 7. DLL-design

### 7.1 Bygginstruktioner och beroenden

- **Kompilator:** MSVC v143 (Visual Studio 2022/2026), C++17 standard.
- **Plattformar:** x64 primärt, x86 om 32-bit ExtendSim ska stödjas (lågprioriterat).
- **Beroenden:** Eclipse Paho MQTT C 1.3.x (statiskt länkat för att slippa runtime-beroenden), OpenSSL 3.x (för TLS-stöd, statiskt länkat).
- **Build system:** CMake 3.20+ med presets för Debug/Release och Win32/x64.
- **Versionshantering:** Embedded version resource. Symbol `MQTT_GetVersion` returnerar semver-sträng.

### 7.2 Headerfil — komplett publik C-ABI

```cpp
// ExtendMQTT.h
#pragma once

#ifdef EXTENDMQTT_EXPORTS
#define MQTT_API extern "C" __declspec(dllexport)
#else
#define MQTT_API extern "C" __declspec(dllimport)
#endif

// Status codes
#define MQTT_OK                  0
#define MQTT_ERR_NOT_CONNECTED  -1
#define MQTT_ERR_CONNECT_FAIL   -2
#define MQTT_ERR_PUBLISH_FAIL   -3
#define MQTT_ERR_SUBSCRIBE_FAIL -4
#define MQTT_ERR_INVALID_PARAM  -5
#define MQTT_ERR_BUFFER_TOO_SMALL -6
#define MQTT_ERR_TIMEOUT        -7
#define MQTT_ERR_INTERNAL       -99

// --- Lifecycle ---
MQTT_API int MQTT_Connect(
    const char* brokerUri,    // "tcp://host:1883" or "ssl://host:8883"
    const char* clientId,
    const char* username,     // may be NULL or empty
    const char* password,     // may be NULL or empty
    int keepAliveSec,         // typical: 20
    int cleanSession);        // 0 or 1

MQTT_API int MQTT_Disconnect();
MQTT_API int MQTT_IsConnected();
MQTT_API int MQTT_GetVersion(char* buf, int bufLen);

// --- TLS configuration (optional) ---
MQTT_API int MQTT_SetTlsConfig(
    const char* caCertPath,
    const char* clientCertPath,  // for mTLS, v1.1+
    const char* clientKeyPath,
    int verifyServer);           // 0 = skip verification, 1 = strict

// --- Last Will and Testament ---
MQTT_API int MQTT_SetLastWill(
    const char* topic,
    const char* payload,
    int qos,
    int retain);

// --- Publishing ---
MQTT_API int MQTT_PublishString(
    const char* topic, const char* payload, int qos, int retain);

MQTT_API int MQTT_PublishDouble(
    const char* topic, double value, int qos, int retain);

MQTT_API int MQTT_PublishJson(
    const char* topic, const char* jsonPayload, int qos, int retain);

MQTT_API int MQTT_PublishBinary(
    const char* topic, const void* data, int dataLen, int qos, int retain);

// --- Subscription ---
MQTT_API int MQTT_Subscribe(const char* topicFilter, int qos);
MQTT_API int MQTT_Unsubscribe(const char* topicFilter);

// --- Polling API ---
MQTT_API int MQTT_HasMessage();
MQTT_API int MQTT_QueueDepth();
MQTT_API int MQTT_PollMessage(
    char* topicBuf, int topicBufLen,
    char* payloadBuf, int payloadBufLen,
    int* qosOut, int* truncatedOut);

// --- JSON helpers (avoid building a JSON parser in ModL) ---
MQTT_API int    MQTT_ExtractJsonNumber(
    const char* json, const char* path, double* outValue);
MQTT_API int    MQTT_ExtractJsonString(
    const char* json, const char* path, char* outBuf, int outBufLen);
MQTT_API int    MQTT_BuildJsonNumber(
    char* outBuf, int outBufLen, const char* key, double value);

// --- Diagnostics ---
MQTT_API int MQTT_GetLastError(char* buf, int bufLen);
MQTT_API int MQTT_SetLogFile(const char* path);
MQTT_API int MQTT_SetLogLevel(int level);  // 0=off,1=error,2=info,3=debug
MQTT_API int MQTT_SetMaxQueueSize(int maxMessages);
```

### 7.3 Funktionssemantik och kontrakt

| Funktion | Blockerande? | Trådsäker? | Anropas från |
|----------|--------------|------------|--------------|
| **MQTT_Connect** | Ja, upp till 10 s timeout | Ja | InitSim |
| **MQTT_Disconnect** | Ja, upp till 5 s | Ja | EndSim, SimulationStop |
| **MQTT_PublishString** | Nej (asynkron) | Ja | Var som helst |
| **MQTT_Subscribe** | Ja, upp till 5 s | Ja | InitSim |
| **MQTT_PollMessage** | Nej (mikrosekunder) | Ja | Var som helst |
| **MQTT_HasMessage** | Nej (mikrosekunder) | Ja | Var som helst |

### 7.4 Felhantering

DLL:en följer principen "return codes, never throw" mot ModL eftersom undantag inte kan korsa C-ABI-gränsen säkert. Alla interna `std::exception` fångas i en yttersta try/catch i varje exporterad funktion och översätts till `MQTT_ERR_INTERNAL` med detaljerad info i `MQTT_GetLastError`-buffern.

Felklasser:

- Konfigurationsfel (ogiltig URI, ogiltigt QoS-värde) — returnerar `MQTT_ERR_INVALID_PARAM`.
- Anslutningsfel (broker nere, fel credentials) — returnerar `MQTT_ERR_CONNECT_FAIL` och loggar detaljer.
- Tillståndsfel (publish utan connect) — returnerar `MQTT_ERR_NOT_CONNECTED`.
- Bufferfel (för liten payload-buffert i poll) — returnerar antal byte som behövs och `truncated=1`.

### 7.5 Minneshantering

All allokering sker inom DLL:en. ModL-strängar kopieras in vid funktionsanrop och kopieras ut vid poll. Inga ägande-pekare passerar API-gränsen. RAII används internt (`std::string`, `std::queue`, `std::lock_guard`).

### 7.6 Trådsäkerhet — kritiska invarianter

- **Invariant 1:** `queueMutex` skyddar all access till meddelandekön. Hålls aldrig samtidigt med andra lås.
- **Invariant 2:** `connected`-flaggan är `std::atomic<bool>`; skrivs av Paho-callbacks och läses av publish/poll.
- **Invariant 3:** Logger har eget mutex och kan skrivas till från valfri tråd.
- **Invariant 4:** `MQTT_Connect` och `MQTT_Disconnect` serialiseras genom ett separat `lifecycleMutex`.

---

## 8. ModL-block design

### 8.1 Block 1: MQTT_Connection

#### 8.1.1 Syfte och placering

Singleton-block som etablerar broker-anslutningen. Placeras en gång per modell, typiskt i ett "infrastruktur"-område. Har ingen item-flow — det är ett rent infrastrukturblock.

#### 8.1.2 Dialogfält

| Fält | Typ | Beskrivning |
|------|-----|-------------|
| Broker URI | string | Format: `tcp://host:port` eller `ssl://host:port`. Default `tcp://localhost:1883`. |
| Client ID | string | Unik identifierare. Default `"extendsim-{modelname}-{pid}"`. |
| Username | string | Tom om broker tillåter anonym anslutning. |
| Password | string (mask) | Maskerat fält. Lagras inte i klartext i .mox-filen om checkbox för "Säker lagring" är vald (v1.1). |
| Keep-alive (s) | integer | Default 20. MQTT-keepalive-intervall. |
| Clean session | checkbox | Default på. Bestämmer om brokern lagrar session-state. |
| Auto-reconnect | checkbox | Default på. |
| Log file path | filepath | Tom = ingen loggning. Föreslås `%TEMP%\extendmqtt.log`. |
| Log level | dropdown | Off / Error / Info / Debug. Default Info. |
| Max queue size | integer | Default 10000. Skydd mot OOM. |

#### 8.1.3 Pseudokod (ModL)

```c
real Broker[256], ClientId[128], Username[128], Password[128];
real KeepAlive, CleanSession, AutoReconnect;
real LogFile[260], LogLevel, MaxQueueSize;
real Status, ConnectedFlag;

on InitSim {
    if (LogFile != "") {
        CallExternal("ExtendMQTT.dll", "MQTT_SetLogFile", LogFile);
        CallExternal("ExtendMQTT.dll", "MQTT_SetLogLevel", LogLevel);
    }
    CallExternal("ExtendMQTT.dll", "MQTT_SetMaxQueueSize", MaxQueueSize);

    Status = CallExternal("ExtendMQTT.dll", "MQTT_Connect",
                           Broker, ClientId, Username, Password,
                           KeepAlive, CleanSession);

    if (Status != 0) {
        errBuf = "";
        CallExternal("ExtendMQTT.dll", "MQTT_GetLastError",
                     ref errBuf, 512);
        AlertUser("MQTT connect failed: " + errBuf);
        AbortSim();
    }
    ConnectedFlag = 1;
}

on EndSim {
    if (ConnectedFlag) {
        CallExternal("ExtendMQTT.dll", "MQTT_Disconnect");
        ConnectedFlag = 0;
    }
}

on SimulationStop {
    // Säkerställ disconnect även vid manuell stopp
    if (ConnectedFlag) {
        CallExternal("ExtendMQTT.dll", "MQTT_Disconnect");
        ConnectedFlag = 0;
    }
}
```

### 8.2 Block 2: MQTT_Publish

#### 8.2.1 Syfte

Publicerar ett meddelande till en topic varje gång ett item passerar genom blocket. Stöder tre payload-lägen: enkel sträng, numeriskt värde och JSON med template-substitution.

#### 8.2.2 Connectors

- **Item in:** trigger för publicering.
- **Item out:** samma item passerar igenom oförändrat.
- **Value in (numerisk):** valfri input för numeric mode.
- **Topic in (sträng):** valfri input som överstyr topic-fältet i dialogen.

#### 8.2.3 Dialogfält

| Fält | Typ | Beskrivning |
|------|-----|-------------|
| Topic | string | MQTT-topic. Får innehålla `{item.attr}` för item-attributsubstitution. |
| Mode | dropdown | "Static string" / "Numeric value" / "JSON template" |
| Payload | multiline | För string mode: literal payload. För JSON: template med `{placeholders}`. |
| QoS | dropdown | 0 / 1 / 2. Default 0 (snabbast). |
| Retain | checkbox | Om på, brokern behåller senaste meddelandet för nya prenumeranter. |
| Block on error | checkbox | Om på, items hålls upp vid publish-fel; om av, items passerar genom även vid fel. |

#### 8.2.4 JSON-template-syntax

Template använder `{nyckel}`-syntax. Följande platshållare stöds:

- `{simtime}` — aktuell simuleringstid (double).
- `{walltime}` — aktuell wall-clock (ISO 8601).
- `{value}` — värdet på Value in-connectorn.
- `{item.id}` — item-ID.
- `{item.priority}` — item-prioritet.
- `{item.attr.<namn>}` — godtyckligt item-attribut.

Exempel:

```json
{
  "t": {simtime},
  "orderId": {item.attr.OrderID},
  "weight": {value},
  "unit": "kg"
}
```

### 8.3 Block 3: MQTT_Subscribe

#### 8.3.1 Syfte

Prenumererar på en topic-filter och triggar event eller skapar items när meddelanden anländer. Använder polling-modell internt — pollar DLL:ens kö med konfigurerbart intervall.

#### 8.3.2 Connectors

- **Item out:** skapar ett item per inkommande meddelande (om "Generate items" är på).
- **Value out:** senast tolkat numeriskt värde från payload.
- **Topic out:** senaste topic (för wildcard-prenumerationer).
- **Payload out:** senaste raw-payload som sträng.
- **Event out:** trigger-utgång som aktiveras vid varje meddelande.

#### 8.3.3 Dialogfält

| Fält | Typ | Beskrivning |
|------|-----|-------------|
| Topic filter | string | MQTT-topic-filter. Stödjer `+` (single-level) och `#` (multi-level) wildcards. |
| QoS | dropdown | 0 / 1 / 2. Default 1 för pålitlig leverans. |
| Poll interval (sim-s) | real | Hur ofta i simuleringstid blocket pollar. Default 0.01. |
| Generate items | checkbox | Om på, skapas ett item per meddelande på Item out. |
| Parse mode | dropdown | "Raw" / "Numeric" / "JSON". Bestämmer hur Value out fylls. |
| JSON path | string | Bara aktiv när Parse mode = JSON. T.ex. `"value"` eller `"data.temperature"`. |
| Item attribute mappings | table | Mappa JSON-fält till item-attribut. Tabell med kolumner: JSON path, Attribute name. |

### 8.4 Block 4: MQTT_Bridge (Real-Time Pacing)

#### 8.4.1 Syfte

Bromsar simuleringen så att simuleringstiden följer wall-clock-tid med en konfigurerbar faktor. Krävs för hardware-in-the-loop-scenarion där simuleringen interagerar med fysiska system som inte kan accelereras.

#### 8.4.2 Beteende

Blocket schemalägger sig själv vid varje sim-sekund (eller annan upplösning) och anropar Sleep om sim-tid hunnit före wall-clock. Om sim-tid är efter wall-clock är simuleringen "sen" och blocket loggar en varning.

#### 8.4.3 Dialogfält

| Fält | Typ | Beskrivning |
|------|-----|-------------|
| Real-time factor | real | 1.0 = realtid, 2.0 = dubbel hastighet, 0.5 = halv hastighet. |
| Sync interval (sim-s) | real | Hur ofta blocket synkroniserar. Default 0.1. |
| Late warning threshold (s) | real | Om sim hamnar efter mer än detta loggas varning. Default 1.0. |
| Publish heartbeat | checkbox | Om på, publiceras heartbeat på `extendsim/{modelid}/heartbeat` varje sync. |

---

## 9. Topic-konventioner och payload-format

### 9.1 Topic-hierarki

Vi rekommenderar (men kräver inte) följande topic-hierarki för konsekvens mellan ExtendSim-projekt:

```
extendsim/<modelId>/in/<channel>          # Data till simuleringen
extendsim/<modelId>/out/<channel>         # Data från simuleringen
extendsim/<modelId>/state/<entity>        # Kontinuerligt tillstånd
extendsim/<modelId>/event/<eventType>     # Diskreta händelser
extendsim/<modelId>/control/<command>     # Extern styrning
extendsim/<modelId>/status                # Heartbeat, sim-tid
extendsim/<modelId>/log/<level>           # Loggar för debug
```

Där:

- `modelId` är ett unikt namn per modell, t.ex. `"papermill1"`.
- `channel`/`entity`/`eventType` etc är fritt valda av modellbyggaren.

### 9.2 Payload-format

Vi rekommenderar JSON för strukturerad data, med en standardiserad omslagsstruktur:

```json
{
  "t": 123.456,
  "wt": "2026-05-04T14:23:45Z",
  "src": "papermill1",
  "value": 42.7,
  "unit": "kg/h",
  "meta": { }
}
```

Fältförklaring:

- `t` — Simuleringstid i sekunder
- `wt` — Wall-clock (valfritt)
- `src` — Källmodell-ID
- `value` — Primärvärde
- `unit` — Enhet (valfritt)
- `meta` — Övrig metadata

För enkla numeriska sensorer kan plain-text (`"42.7"`) användas vid behov av minimal payload. Detta stöds av `MQTT_PublishDouble`.

### 9.3 QoS-rekommendationer

| QoS | Garanti | Använd för |
|-----|---------|-----------|
| **0** | At most once | Högfrekvent telemetri där enstaka meddelandeförluster är acceptabla (t.ex. temperatursensorer som samplas varje sekund). |
| **1** | At least once | Default-rekommendation. Händelsedrivna meddelanden där alla måste komma fram men dubletter är OK. |
| **2** | Exactly once | Kritiska kommandon där dubletter skulle orsaka skada (t.ex. "starta motor", "öppna ventil"). Mest overhead. |

---

## 10. Exempelmodeller

Fem exempelmodeller levereras med produkten. De är ordnade i stigande komplexitet och var och en demonstrerar ett distinkt arkitekturmönster.

### 10.1 Exempel 1: Hello MQTT

- **Syfte:** Verifiera att DLL, broker och block hänger ihop.
- **Arkitekturmönster:** Fire-and-forget publishing.
- **Komplexitet:** Trivial.

#### Innehåll

- 1 × MQTT_Connection (broker = `tcp://localhost:1883`).
- 1 × Generator (skapar item var 5:e sekund).
- 1 × MQTT_Publish (topic = `test/hello`, mode = string, payload = `"tick at {simtime}"`).
- 1 × Exit.

#### Verifiering

Kör `mosquitto_sub -h localhost -t test/hello` i terminal. Kör simuleringen. Förvänta tick-meddelanden var 5:e sim-sekund.

#### Lärandemål

- Förstå hur MQTT_Connection placeras.
- Förstå publishing-flödet (item triggar publish).
- Förstå template-substitution med `{simtime}`.

### 10.2 Exempel 2: Sensor-driven ankomstprocess

- **Syfte:** Låta extern sensordata påverka simuleringens beteende.
- **Arkitekturmönster:** External-data-driven simulation.
- **Komplexitet:** Låg-medel.

#### Scenario

En butik vill simulera kundankomster baserat på utomhustemperatur — högre temperatur ger fler kunder. En extern sensor (eller Python-skript som emulerar sensor) publicerar temperaturer; ExtendSim mappar dessa till en ankomstintensitet.

#### Innehåll

- MQTT_Connection.
- MQTT_Subscribe (topic = `sensors/temp/outside`, parse mode = JSON, JSON path = `value`).
- Equation block: `λ = max(0.1, (Value out - 15) * 0.5)`.
- Create block driven av λ via Poisson-fördelning.
- Activity (kassakön).
- Exit + statistikinsamling.

#### Stödfiler

- `python_sensor_simulator.py` — publicerar temperaturer var 2:a sekund med diurnal variation.

#### Lärandemål

- Subscribe-flöde och poll-baserad delivery.
- JSON-extraktion.
- Hur extern data kan styra simuleringsparametrar i realtid.

### 10.3 Exempel 3: PLC-styrd produktionslina (HIL)

- **Syfte:** Hardware-in-the-loop-testning av styrlogik mot en simulerad process.
- **Arkitekturmönster:** Closed-loop control.
- **Komplexitet:** Hög.

#### Scenario

En tank med inflöde och utflöde ska hållas på en målnivå (50%). En extern "PLC" — emulerad via Node-RED — implementerar en PID-regulator som tar emot tanknivån via MQTT och skickar tillbaka ventilöppning. ExtendSim simulerar tankens fysik.

#### Innehåll

- MQTT_Connection.
- MQTT_Bridge (real-time factor = 1.0, sync interval = 0.1 s).
- Tank block (continuous, kapacitet 1000 liter).
- Inflöde-ventil (continuous flow source, modulerad av MQTT-input).
- Utflöde (konstant 50 l/min).
- MQTT_Subscribe på `plc/valve/setpoint` → moduleringsvärde 0–100%.
- MQTT_Publish av tanknivå på `plc/sensor/level` var 100 ms simtid.
- MQTT_Publish av faktiskt flöde på `plc/sensor/flow`.

#### Stödfiler

- `nodered_pid_controller.json` — Node-RED-flow med PID-regulator (Kp=2, Ki=0.1, Kd=0.05).
- `docker-compose.yml` för Mosquitto + Node-RED.

#### Lärandemål

- Realtidssynkronisering med MQTT_Bridge.
- Closed-loop-arkitektur över MQTT.
- Hur kontinuerliga modeller integrerar med diskret meddelandekommunikation.

### 10.4 Exempel 4: Fjärrstyrd simulering (Control Plane)

- **Syfte:** Demonstrera hur en simulering kan startas, pausas och konfigureras via MQTT.
- **Arkitekturmönster:** Command pattern över message broker.
- **Komplexitet:** Medel.

#### Scenario

En operatör vill kunna styra simuleringen från en webbdashboard utan att öppna ExtendSim. Styrkommandon (pause, resume, set speed, reset) skickas som MQTT-meddelanden; status och progress publiceras tillbaka.

#### Innehåll

- MQTT_Connection.
- MQTT_Subscribe på `extendsim/control/+` med wildcard.
- ModL-logik som tolkar topic-suffix: `pause` / `resume` / `setspeed` / `reset`.
- MQTT_Publish av status varje sekund på `extendsim/{modelid}/status`.
- Bakomliggande "dummy" simuleringsmodell (en M/M/1-kö).

#### Stödfiler

- `html_dashboard/` — enkel webbapp med Eclipse Paho JavaScript som ansluter till broker via WebSocket.

#### Lärandemål

- Wildcard-prenumerationer.
- Bidirektionell kommunikation.
- Separation mellan data plane och control plane.

### 10.5 Exempel 5: Digital twin med sensor-fusion

- **Syfte:** Visa en fullständig digital twin-pipeline.
- **Arkitekturmönster:** Multi-source fusion + predictive publishing.
- **Komplexitet:** Hög.

#### Scenario

En pappersmaskin har tre sensorer: massflöde in, ångtemperatur, valstryck. ExtendSim har en kalibrerad processmodell som tar dessa som input och predikterar slutprodukt-densitet 30 sekunder framåt. Predikterad densitet publiceras tillbaka och visualiseras i Grafana tillsammans med faktiska mätvärden.

#### Innehåll

- MQTT_Connection.
- MQTT_Bridge (real-time factor = 1.0).
- 3 × MQTT_Subscribe (en per sensor).
- Stat collection block som bygger state-vector.
- Hybridmodell: continuous heat exchange-block + discrete kvalitetskontrollpunkter.
- Equation block för 30-sekunders prediktion.
- MQTT_Publish av prediktion på `digitaltwin/papermill1/prediction`.

#### Stödfiler

- `grafana_dashboard.json` — färdig Grafana-dashboard med InfluxDB-koppling.
- `influxdb_mqtt_bridge.py` — bryggar MQTT till InfluxDB för time-series-lagring.
- `python_sensor_simulator_paper.py` — emulerar tre sensorer med realistisk korrelation.

#### Lärandemål

- Multi-source data ingestion.
- Kombinera kontinuerlig och diskret modellering.
- Skapa predictive output för external consumption.
- End-to-end digital twin-arkitektur.

---

## 11. Icke-funktionella krav

### 11.1 Prestanda

- **Publish-latens:** ≤ 5 ms median, ≤ 20 ms p99 (loopback, QoS 0, 64-byte payload).
- **Subscribe-genomströmning:** ≥ 5000 msg/s utan kö-overflow vid 10 minuters belastning.
- **Connect-tid:** ≤ 2 sekunder mot lokal broker.
- **Minne:** ≤ 50 MB residual för DLL inklusive 10 000 köade meddelanden.
- **CPU-overhead:** ≤ 5% av single core vid 1000 msg/s.

### 11.2 Tillförlitlighet

- Auto-reconnect inom 30 sekunder efter broker-återkomst.
- Inga orphaned anslutningar efter ExtendSim-process avslutas.
- Persistens av in-flight QoS 1/2-meddelanden vid återanslutning (Paho hanterar).
- Bounded queue förhindrar OOM vid broker-bortfall.

### 11.3 Säkerhet

- TLS 1.2/1.3 stöd för krypterad transport.
- Stöd för broker-auth via username/password.
- Klientcertifikatautentisering (mTLS) i v1.1.
- Lösenord lagras inte i klartext i exporterade .mox-filer (om "Säker lagring" valt — v1.1).
- Inga loggade lösenord eller TLS-nycklar ens på debug-loggnivå.

### 11.4 Användbarhet

- "Hello world" på under 15 minuter för en ny användare.
- Felmeddelanden på svenska och engelska.
- Dialog-tooltips för alla fält.
- Inbyggd "Test connection"-knapp i MQTT_Connection-dialogen.
- Statusindikator i MQTT_Connection-blockets ikon (grön = ansluten, röd = nere, gul = återansluter).

### 11.5 Underhållbarhet

- Hexagonal arkitektur i kodbasen — kärnan är fri från ExtendSim-specifika beroenden.
- Unit tests för all kärnlogik (köhantering, JSON-parsning, state machine) — minst 80% line coverage.
- Integration tests mot lokal Mosquitto via Docker.
- CI-pipeline med automatisk build, test och artefakt-publicering.

### 11.6 Distribution och installation

- MSI-installer som lägger DLL och bibliotek i ExtendSim-katalogen.
- Installer detekterar ExtendSim-installation automatiskt.
- Avinstallation lämnar inga rester.
- Ingen administratörsbehörighet krävs för installation i användarens hemkatalog (per-user-installation).

### 11.7 Licensiering

- ExtendMQTT: MIT- eller Apache 2.0-licens.
- Eclipse Paho: EPL/EDL dual-licens (kompatibel).
- OpenSSL: Apache 2.0 (3.x-serien).
- Tredjepartsbibliotek listas i NOTICE-fil.

---

## 12. Användarflöden

### 12.1 Flöde 1: Första installationen

1. Användaren laddar ner ExtendMQTT-installer från GitHub releases.
2. Kör installern. Den hittar ExtendSim-installationen automatiskt.
3. DLL kopieras till `ExtendSim/Extensions/`, biblioteket till `ExtendSim/Libraries/`.
4. Installern erbjuder att starta Mosquitto via Docker (valfritt steg).
5. Användaren öppnar ExtendSim, ser ExtendMQTT-biblioteket i Library Manager.

### 12.2 Flöde 2: Bygga första modellen

1. Användaren öppnar Hello MQTT-exemplet.
2. Klickar Run.
3. Får felmeddelandet "Cannot connect to broker" eftersom Mosquitto inte körs.
4. Startar Mosquitto via Docker (eller Windows-tjänst).
5. Klickar Run igen. Lyckas. Verifierar med `mosquitto_sub`.

### 12.3 Flöde 3: Felsökning av subscribe som inte fungerar

1. Användaren ser att MQTT_Subscribe inte triggar trots att meddelanden publiceras.
2. Aktiverar Debug-loggning i MQTT_Connection.
3. Tittar i logfilen och ser `"Topic filter mismatch: subscribed to 'sensors/+/temp', received 'sensors/temp/outside'"`.
4. Korrigerar topic-filtret. Modellen fungerar.

### 12.4 Flöde 4: Demo för kund

1. Lars (Duke Systems-konsult) öppnar exempel 3 (PLC-styrd produktionslina).
2. Startar docker-compose med Mosquitto + Node-RED + Grafana.
3. Visar kunden hur Node-RED-PID-regulatorn styr tanken.
4. Modifierar Node-RED-flow live för att visa hur olika regulatorparametrar påverkar systemet.
5. Lägger till störning i ExtendSim-modellen och visar hur regulatorn återhämtar sig.

---

## 13. Risker och antaganden

### 13.1 Tekniska risker

| Risk | Sannolikhet | Påverkan | Mitigering |
|------|-------------|----------|-----------|
| ModL string marshalling beter sig oväntat | Hög | Hög | Bygg minimal proof-of-concept tidigt; testa empiriskt med olika strängformat och längder. |
| ExtendSim kraschar pga calling convention-mismatch | Medel | Hög | Strikt `__stdcall`/`__cdecl`-konvention dokumenterad och testad. Använd ExtendSim Developer Reference. |
| Trådkonflikt vid callbacks | Medel | Hög | Pollar-modell istället för callbacks till ModL. Stress-tester med thread sanitizer. |
| Kö-overflow vid hög meddelanderate | Medel | Medel | Bounded queue, drop-strategi, tydlig loggning. Användaren kan justera storlek. |
| TLS-konfiguration komplex för slutanvändare | Hög | Medel | Tydlig dokumentation och exempel; "insecure mode" för dev/test. |
| Paho-licensvillkor ändras | Låg | Medel | Pinna en specifik Paho-version i submodule. Mosquitto-klienten är alternativ. |
| ExtendSim-API ändras i framtida version | Låg | Medel | Tunt CallExternal-lager som kan portas. Testa mot betaversioner när tillgängliga. |

### 13.2 Affärsrisker

| Risk | Sannolikhet | Påverkan | Mitigering |
|------|-------------|----------|-----------|
| Imago Simulation släpper officiell MQTT-modul | Låg | Medel | Vi får trovärdighet som community-bidrag; positionerar oss som integrationspartner. |
| Få nordiska kunder har behov av MQTT | Låg | Medel | Marknadsför globalt via ExtendSim-forum, GitHub. Fokusera på pappersbruk/process där MQTT redan är vanligt. |
| Kunder förväntar sig kommersiell support utan att betala | Hög | Låg | Tydlig kommunikation: open source = best effort via GitHub Issues; SLA-support kostar. |

### 13.3 Antaganden

- ExtendSim 10/2024 stödjer `CallExternal` med strängar och referenser i den utsträckning vi behöver. — Verifieras tidigt i utvecklingen.
- Mosquitto eller motsvarande broker finns tillgänglig hos kunden eller kan installeras enkelt.
- Slutanvändare har grundläggande MQTT-förståelse eller kan lära sig via vår dokumentation.
- Visual Studio 2022/2026 finns tillgängligt för alla utvecklare.
- GitHub-baserad distribution är acceptabelt — vi behöver ingen MSI-baserad enterprise-distribution i v1.0.

---

## 14. Utvecklingsplan

### 14.1 Faser och leverabler

| Fas | Namn | Tidsåtgång | Leverabler |
|-----|------|-----------|-----------|
| **0** | Förstudie | 1 vecka | Verifiera CallExternal-mönster med trivial DLL. Strängar in/ut, referenser, returvärden. |
| **1** | DLL kärna | 3 veckor | Connect/Publish/Disconnect via Paho. Testas från konsoll-program (inte ExtendSim). |
| **2** | ModL-block: Connect+Publish | 2 veckor | Hello MQTT-exempel fungerar end-to-end. Calling convention och string marshalling löst. |
| **3** | Subscribe + polling | 3 veckor | MQTT_Subscribe-block fungerar. Sensor-driven ankomstprocess (exempel 2) körbar. |
| **4** | MQTT_Bridge + JSON | 2 veckor | Real-time pacing fungerar. JSON-helpers tillgängliga. PLC-exemplet (exempel 3) körbar. |
| **5** | TLS + auth | 1 vecka | `ssl://` fungerar. Testat mot HiveMQ Cloud och AWS IoT Core. |
| **6** | Robusthet | 2 veckor | Auto-reconnect, LWT, kö-överflöd, edge cases. Stress-tester. |
| **7** | Exempelmodeller | 2 veckor | Alla 5 exempel fungerar. Stödfiler (Python, Node-RED, Grafana) producerade. |
| **8** | Dokumentation | 2 veckor | README, INSTALL, BLOCK_REFERENCE, TOPIC_CONVENTIONS, TROUBLESHOOTING. |
| **9** | Beta-test | 3 veckor | Distribuera till 3-5 betatestare bland Duke-kunder. Samla feedback. |
| **10** | Release v1.0 | 1 vecka | MSI-installer, GitHub release, blogginlägg, kundannons. |

### 14.2 Total tidsåtgång

Cirka 22 veckor från start till v1.0-release vid heltidsutveckling. Realistisk kalendertid med Duke Systems pågående kundprojekt: 6-9 månader.

### 14.3 Repository-struktur

```
ExtendMQTT/
├── src/
│   ├── ExtendMQTT.h
│   ├── ExtendMQTT.cpp
│   ├── Connection.cpp
│   ├── PublishHandler.cpp
│   ├── SubscribeHandler.cpp
│   ├── MessageQueue.cpp
│   ├── JsonHelpers.cpp
│   ├── Logger.cpp
│   └── PahoBridge.cpp
├── third_party/
│   ├── paho.mqtt.c/        (git submodule)
│   └── nlohmann_json/      (header-only)
├── modl/
│   ├── MQTT_Connection.modl
│   ├── MQTT_Publish.modl
│   ├── MQTT_Subscribe.modl
│   └── MQTT_Bridge.modl
├── library/
│   └── ExtendMQTT.lix      (paketerat ExtendSim-bibliotek)
├── examples/
│   ├── 01_HelloMqtt/
│   ├── 02_SensorArrival/
│   ├── 03_PlcProduction/
│   ├── 04_RemoteControl/
│   └── 05_DigitalTwin/
├── test/
│   ├── unit/
│   ├── integration/
│   ├── stress/
│   └── docker-compose.yml
├── docs/
│   ├── README.md
│   ├── INSTALL.md
│   ├── BLOCK_REFERENCE.md
│   ├── TOPIC_CONVENTIONS.md
│   ├── TROUBLESHOOTING.md
│   └── ARCHITECTURE.md
├── installer/
│   └── extendmqtt.wxs      (WiX MSI-konfiguration)
├── .github/workflows/
│   ├── build.yml
│   └── release.yml
├── CMakeLists.txt
├── LICENSE
├── NOTICE
└── CHANGELOG.md
```

---

## 15. Teststrategi

### 15.1 Testpyramid

- **Unit tests (60%):** Köhantering, JSON-parsning, state machine, parameter-validering. Inget MQTT-broker-beroende. Använd Catch2 eller GoogleTest.
- **Integration tests (30%):** Hela DLL:en mot lokal Mosquitto via Docker. Testar publish/subscribe, reconnect, TLS, LWT.
- **End-to-end tests (10%):** Hela exempelmodeller körs i ExtendSim mot riktig broker. Manuell verifiering plus snapshot av output.

### 15.2 Testscenarion

#### 15.2.1 Funktionella tester

- Connect mot lokal Mosquitto utan auth — succé.
- Connect mot Mosquitto med fel password — `MQTT_ERR_CONNECT_FAIL`.
- Connect mot icke-existerande broker — timeout, `MQTT_ERR_CONNECT_FAIL`.
- Publish QoS 0/1/2 verifieras med extern subscriber.
- Subscribe med wildcard — meddelanden från flera matchande topics levereras.
- Subscribe + 10 000 meddelanden i snabb följd — alla levereras eller dropp loggas.
- Disconnect under pågående publish — graceful, ingen krasch.
- LWT publiceras vid abnormal disconnection.

#### 15.2.2 Stress- och prestandatester

- 100 000 publish QoS 0 — mät medianlatens.
- Sustained 5000 msg/s subscribe i 1 timme — kö-overflow får inte uppstå.
- Broker-bortfall i 5 minuter — auto-reconnect återställer.
- Memory leak-test: kör 24h kontinuerligt, RSS får inte växa över baseline+10%.

#### 15.2.3 Säkerhetstester

- TLS 1.2 mot Mosquitto med CA-cert — succé.
- TLS-anslutning till broker med ogiltigt cert utan `verifyServer` — succé (förväntat).
- TLS-anslutning till broker med ogiltigt cert med `verifyServer` — failure (förväntat).
- Lösenord finns inte i någon logg eller dump.

#### 15.2.4 Robusthetstester

- Tom topic, NULL-pekare, jättestora payloads (1 MB+) — graceful handling.
- Kalla Disconnect två gånger — idempotent.
- Ladda om DLL utan att stänga ExtendSim — clean shutdown.
- Multiple Connect-anrop — andra ersätter första.

---

## 16. Dokumentationsplan

### 16.1 Levererade dokument

| Dokument | Innehåll |
|----------|---------|
| **README.md** | Översikt, snabbstart, länk till exempel, badges (build status, license). |
| **INSTALL.md** | Installationsinstruktioner för Windows, ExtendSim-versioner, broker-setup. |
| **BLOCK_REFERENCE.md** | Komplett referens för alla fyra block: dialogfält, in/out connectors, beteende, exempel. |
| **TOPIC_CONVENTIONS.md** | Rekommenderad topic-hierarki, payload-format, QoS-vägledning. |
| **TROUBLESHOOTING.md** | Vanliga fel, hur man tolkar logfilen, hur man kontaktar support. |
| **ARCHITECTURE.md** | För utvecklare. Trådmodell, lifecycle, hur man bygger från källkod. |
| **EXAMPLES/*.md** | En fil per exempelmodell med scenario, instruktioner, screenshots. |
| **CHANGELOG.md** | Semantic versioning, release notes per version. |
| **CONTRIBUTING.md** | Hur externa bidragsgivare kan bidra. Code style, PR-process. |

### 16.2 Marknadsmaterial

- Blogginlägg på Duke Systems hemsida (svenska + engelska).
- LinkedIn-post med korta demovideos.
- Kundmail till befintliga ExtendSim-kunder med annonsering.
- YouTube-video (5–10 min) som visar exempel 3 (PLC-styrd produktionslina).

---

## 17. Öppna frågor

Följande beslut behöver tas innan eller under utveckling:

| Q# | Fråga | Förslag / status |
|----|-------|------------------|
| **Q1** | Ska v1.0 stödja flera samtidiga broker-anslutningar? | Förslag: Nej. Refaktorera till handle-baserat API i v2.0. |
| **Q2** | Ska blocken stödja både svenska och engelska UI-texter? | Förslag: Engelska i v1.0. Svensk lokalisering i v1.1 om efterfrågan finns. |
| **Q3** | Ska MSI-installer eller bara ZIP-distribution? | Förslag: ZIP för v1.0 (snabbare release), MSI i v1.1. |
| **Q4** | Vilken licens? MIT, Apache 2.0 eller GPL? | Förslag: Apache 2.0 — ger patentskydd och tydligare än MIT för kommersiellt bruk. |
| **Q5** | Ska Mosquitto distribueras med installern eller bara länkas till? | Förslag: Bara länka till. Användare som behöver broker installerar via Docker eller standalone. |
| **Q6** | Behöver vi stödja 32-bit ExtendSim? | Förslag: Nej i v1.0. Verifiera med kundbas att alla kör 64-bit. |
| **Q7** | Ska SimulationsMCP integreras med ExtendMQTT på något sätt? | Möjlighet: AI-agent kan lyssna på `extendsim/+/event/+` och styra modellen via MQTT. Utvärderas i v2.0. |
| **Q8** | Ska prestanda-benchmarks publiceras öppet? | Förslag: Ja, ger trovärdighet. Använd som marknadsföringsmaterial. |

---

## 18. Appendix

### 18.1 Begreppsförklaring

| Term | Definition |
|------|-----------|
| **MQTT** | Message Queuing Telemetry Transport. Lättviktig publish/subscribe-protokoll standardiserad som ISO/IEC 20922:2016. |
| **Broker** | Server som distribuerar meddelanden mellan publishers och subscribers. Mosquitto, HiveMQ, EMQX är exempel. |
| **Topic** | Hierarkisk strängadress där meddelanden publiceras. `"sensors/temp/livingroom"`. |
| **QoS** | Quality of Service. MQTT erbjuder 0 (at most once), 1 (at least once), 2 (exactly once). |
| **LWT** | Last Will and Testament. Meddelande som brokern publicerar automatiskt om klienten kopplas ner abnormalt. |
| **Retained message** | Brokern lagrar senast publicerade meddelandet på en topic och levererar omedelbart till nya prenumeranter. |
| **HIL** | Hardware-in-the-Loop. Testmetod där fysisk hårdvara interagerar med simulerad miljö i realtid. |
| **Digital twin** | Digital representation av ett fysiskt system, ofta synkroniserad i realtid med sensorer från det fysiska systemet. |
| **ModL** | ExtendSims inbyggda programmeringsspråk för custom blocks. C-liknande syntax. |
| **CallExternal** | ModL-funktion för att anropa exporterade funktioner i en native DLL. |
| **Paho** | Eclipse Paho — open source MQTT-klientbibliotek tillgängligt i flera språk inklusive C, C++, Java, Python. |

### 18.2 Referenser

- MQTT v3.1.1 specifikation: https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html
- MQTT v5.0 specifikation: https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html
- Eclipse Paho MQTT C: https://github.com/eclipse/paho.mqtt.c
- Eclipse Mosquitto: https://mosquitto.org/
- HiveMQ MQTT essentials: https://www.hivemq.com/mqtt-essentials/
- ExtendSim Developer Reference (intern, kräver licens).
- Duke Systems SimulationsMCP intern dokumentation.

### 18.3 Versionshistorik för detta dokument

| Version | Datum | Ändring |
|---------|-------|--------|
| **v0.1** | 2026-05-04 | Initial draft. Komplett första utgåva som täcker arkitektur, DLL-design, ModL-block, exempel, NFR, plan, risker, öppna frågor. |
