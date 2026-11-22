# Maan op een bol — een virtuele projector

**Bekijk hem hier:** https://gitai47.github.io/maan_bol.html

Een maanfoto, teruggerekend op een bol die je met je muis of vinger om alle kanten kunt draaien. Het is alsof je vanaf de aarde de ruimte in vliegt en de maan van opzij, van boven of van heel dichtbij bekijkt.

Het idee komt van een eenvoudig experiment: projecteer een maanfoto met een beamer op een witte bal en loop eromheen. Je ziet de maan dan ineens als een bol in plaats van als een platte schijf. Deze pagina doet hetzelfde, alleen uitgerekend.

---

## De opname

| | |
|---|---|
| **Fotograaf** | Peter van Haeringen |
| **Locatie** | Monnickendam |
| **Datum** | 20 november 2026 |
| **Telescoop** | 150 mm Newton, f/5 |
| **Camera** | Goedkope USB-camera |
| **Bewerking** | Gestapeld uit een video met eigen software |

Gestapeld betekent dat de scherpste beelden uit een korte video zijn gekozen, op elkaar gelegd en gemiddeld. Zo verdwijnt de ruis en blijft het echte detail over. Dit heet *lucky imaging*.

---

## Het uitgangspunt: niets toevoegen

Alles wat je op de bol ziet, komt uit de foto. Er is niets bij verzonnen: geen AI die details invult, geen kaart van de achterkant van de maan erbij geplakt.

Daardoor zie je een paar dingen die eerlijk laten zien wat er wel en niet in een opname zit:

- **De schaduwen draaien niet mee.** Het zonlicht zit "in" de foto, precies zoals bij de beamer op de bal. Van opzij bekeken staat de schaduwgrens daardoor op een plek waar de zon in werkelijkheid niet zo staat.
- **De rand smeert uit.** Aan de rand van de maanschijf keek de camera heel schuin langs het oppervlak, dus daar vallen veel kilometers in één pixel. Draai de bol 60 tot 90 graden en je ziet hoe weinig informatie daar in de opname zit.
- **De achterkant is een raster.** Die zien we vanaf de aarde nooit, dus daar is geen data.

---

## Bedienen

- **Slepen:** om de maan heen bewegen
- **Scrollwiel of schuifje "Afstand":** dichterbij of verder weg
- **Knoppen:** vaste standpunten, zoals *Vanaf de aarde*, *Van opzij (90°)* of *Boven de noordpool*
- **Draaien ▶:** de maan langzaam laten ronddraaien

Het werkt in elke moderne browser, ook op een telefoon. Het is één bestand en het heeft geen internet nodig: je kunt `maan_bol.html` ook downloaden en lokaal openen.

---

## Zelf een bol maken van je eigen maanfoto

Met `maak_maanbol.py` maak je van je eigen maanfoto zo'n pagina.

**Nodig:** Python 3 met OpenCV en NumPy

```bash
pip install opencv-python numpy
```

**Gebruik:**

```bash
python3 maak_maanbol.py mijn_maan.tif
```

Dit maakt `maan_bol.html` (de pagina) en `controle_cirkel.png`. Open eerst die controle: de rode cirkel moet precies op de verlichte rand van de maan liggen.

**Opties:**

| Optie | Wanneer |
|---|---|
| `-o naam.html` | Andere bestandsnaam |
| `--links` | De verlichte rand zit links (afnemende maan) |
| `--drempel 30` | De maan wordt niet goed gevonden (vaag of donker beeld): probeer een lagere of hogere waarde |
| `--cirkel X Y R` | Middelpunt en straal van de maanschijf zelf opgeven, in pixels |

**Tips voor de foto:**

- Draai hem eerst rechtop, zoals je de maan met het blote oog ziet. Een Newton-telescoop draait het beeld om.
- Hoe meer van de schijf verlicht is, hoe meer bol je krijgt. Rond volle maan is het mooist voor het overzicht, rond halve maan voor het reliëf.

---

## Hoe het werkt

1. **De maanschijf vinden.** Het script zoekt de rand van de verlichte maan en past daar een cirkel op. De schaduwgrens (terminator) doet daarbij niet mee, want die is geen rand van de bol.

2. **Van foto naar bol.** Vanaf de aarde zie je de maan bijna als een orthografische projectie: van zo ver weg dat alle zichtlijnen evenwijdig lopen. Een pixel op afstand (X, Y) van het middelpunt, gedeeld door de straal, ligt op de bol op diepte

   Z = √(1 − X² − Y²)

   Zo krijgt elke pixel een plek op de bol, met een lengte en een breedte.

3. **Een kaart maken.** Die plekken worden opgeslagen als een rechthoekige wereldkaart (2048 × 1024 pixels). De achterkant krijgt een raster.

4. **Terugrekenen in de browser.** Bij elke pixel op je scherm rekent de pagina uit waar een kijkstraal vanuit jouw standpunt de bol raakt. Daarna zoekt hij op welke plek van de kaart dat is (*ray casting*). Dat gebeurt in je eigen browser, dus elke bezoeker rekent zijn eigen maan uit.

---

## Verder kijken

- **Libratie.** De maan wiebelt een beetje, waardoor we vanaf de aarde over de maanden heen zo'n 59% van het oppervlak zien, niet 50%. Combineer opnames van verschillende avonden en het raster wordt kleiner, nog steeds met alleen echte data.
- **Hoogtes meten.** Met de lengte van een schaduw en de hoek van de zon kun je de hoogte van kraterwanden en bergtoppen uitrekenen. Galileo deed dat in 1610 al.
- **Je eigen oog.** Je hersenen doen iets vergelijkbaars: ze voegen losse, schokkerige beelden samen tot één stabiel beeld en vullen je blinde vlek in. Wat je "ziet", is ook altijd een reconstructie.

---

*Gemaakt door Peter van Haeringen, met Claude (Anthropic) als programmeermaatje.*
