# Decentralizirana borza Lighter

**Avtor:** Aleks Kavčič

**Orodja:** Python, Linux, Lighter REST API, Lighter Python SDK

## Namen projekta

Cilj je z majhnim Python programom prikazati podatke borze Lighter in razložiti,
kako se program poveže z borzo. Program pridobi trge in order book, izračuna
najboljši bid, najboljši ask ter spread, periodično spremlja cene in prikaže
zgodovinske meritve. Vsebuje tudi možnost limitnega naročila na testnetu.

Javni API in povezava SDK z lastnim testnet API ključem sta bila preverjena.
Dejansko naročilo še ni bilo oddano, zato oddaja, status in preklic naročila
niso potrjeni z izvedenim testnim naročilom.

## Kako je projekt zgrajen

- `orderbook/main.py` prikaže meni in povezuje funkcije.
- `01_test_connection.py` preveri povezavo z Lighter API-jem.
- `02_list_markets.py` pridobi trge in kotacijsko valuto.
- `03_get_orderbook.py` pridobi ter preveri bids in asks.
- `04_calculate_spread.py` poišče najboljši ceni in izračuna spread.
- `05_live_prices.py` ponavlja REST zahteve in shranjuje meritve.
- `06_currency_conversion.py` pridobi in preveri tečaj USD/EUR.
- `07_plot_history.py` prebere CSV in prikaže graf.
- `orders.py` vsebuje pripravo, oddajo, pregled in preklic testnet naročila.
- `test_orderbook_validation.py` vsebuje avtomatske teste.
- `price_history.csv` hrani meritve cen.

`lighter_orderbook.py` je ohranjen kot opozorilo za stari primer. Uporabi glavni
meni z ukazom `python orderbook/main.py`.

## Arhitektura Lighter

Lighter v svojem protokolarnem dokumentu opisuje več glavnih delov. **Sequencer**
sprejema in zaporedno obdeluje operacije, kot so naročila. **Indexer** obdela
podatke o stanju in jih pripravi za poizvedbe. **API strežniki** omogočajo
pošiljanje zahtev in branje podatkov prek REST in WebSocket vmesnikov.
**Prover** pripravi kriptografske dokaze, da so bile spremembe stanja izvedene
po pravilih. Pametne pogodbe na Ethereumu preverijo dokaze in hranijo zavezo
protokola do trenutnega stanja. To je poenostavljen povzetek uradnega opisa;
ta projekt teh komponent ne izvaja sam.

Izraz *zk* tukaj ne pomeni, da je borza zasebna. Protokolarni dokument opisuje
uporabo zk-SNARK dokazov za preverjanje pravilnosti izvajanja in sprememb
stanja. [Lighterjev protokolarni dokument](https://assets.lighter.xyz/whitepaper.pdf)

## Kako program komunicira z borzo

Za javne podatke program uporablja HTTP zahteve REST API-ju. Pridobi seznam
trgov, nato za izbrani `market_id` pridobi order book. REST vrne odgovor na
posamezno zahtevo.

Možnost spremljanja cen vsake tri sekunde ponovi REST zahtevo. To je
periodično osveževanje, ne WebSocket prenos v realnem času. WebSocket je
primernejši za sprotne dogodke, vendar bi zahteval dodatno upravljanje povezave
in naročnin. V tem študentskem programu je izbran preprostejši REST pristop.

Trenutna rešitev bere javne podatke iz REST API-ja. Podatki o trgih in order
booku se prikazujejo v terminalu. Če so podatki napačni, imajo neveljavne
cene/količine ali je order book prekrižan, program izračuna napako namesto
običajnega spreada.

## Order book in spread

- **Bid** je nakupna ponudba; najboljši bid je najvišja veljavna cena.
- **Ask** je prodajna ponudba; najboljši ask je najnižja veljavna cena.
- **Spread** je najboljši ask minus najboljši bid.
- Odstotni spread je razlika, deljena z best bid in pomnožena s 100.

Program ne predpostavlja, da so vrstice API-ja že v pravilnem vrstnem redu.
Zavrne manjkajoče podatke, napačne tipe ter cene ali količine, ki so nič,
negativne, `NaN` ali neskončne. Če je best bid višji od best ask, označi
prekrižan order book. Prazna stran pomeni, da spreada ni mogoče izračunati.

## Valute in zgodovina

Kotacijsko valuto program pridobi iz podatkov o trgu in pripadajočem sredstvu.
Pretvorbo v EUR in zapis v zgodovino opravi samo, če je kotacijska valuta
potrjeno USD. Za druge valute prikaže izvorne cene in jih ne zapiše v stolpce,
ki so namenjeni EUR meritvam.

CSV je v `orderbook/price_history.csv`. Graf prikaže najboljšo nakupno in
prodajno ceno ter spread v EUR in odstotkih. Neveljavne ali neskončne vrednosti
se pri pripravi grafa preskočijo.

## Primerjava z drugimi borzami

Spodnja primerjava je namenoma omejena na različne načine organizacije
trgovanja. Ne pomeni, da vsi DEX-i ali vse centralizirane borze delujejo enako.

| Lastnost | Lighter | Uniswap | Coinbase Exchange |
|---|---|---|---|
| Vrsta | DEX z order bookom in L2 protokolom | DEX z AMM likvidnostnimi bazeni | Centralizirana borza |
| Kako se določi cena | Ujemanje bid/ask naročil | Cene iz stanja likvidnostnega bazena in pravil AMM | Centralni order book ali dražba |
| Kje se izvrši trgovanje | Sequencer obdela operacije; pravilnost stanja se dokazuje in poravna prek Ethereuma | Zamenjave izvajajo pametne pogodbe na podprtih verigah | Ujema jih upravljana infrastruktura borze |
| Skrbništvo/poravnava | Protokol opisuje sredstva in stanje prek L2 ter pametnih pogodb | Uporabnik pošlje zamenjavo v pametno pogodbo bazena | Uporabnik trguje prek računa pri ponudniku borze |
| Kaj prikazuje ta projekt | Bids, asks, spread in podatke Lighter | Ni vključeno | Ni vključeno |

Uniswap uporablja pametne pogodbe in likvidnostne bazene namesto tradicionalne
knjige naročil. Coinbase za trgovanje z osnovnim stanjem opisuje centralni
limitni order book ali dražbe. Podrobnosti se razlikujejo med produkti in se
lahko sčasoma spremenijo. [Uniswap: kako deluje](https://developers.uniswap.org/docs/get-started/concepts/how-uniswap-works),
[Coinbase: način izvedbe poslov](https://help.coinbase.com/en-in/coinbase/trading-and-funding/pricing-and-fees/fees)

## Metodologija in zasnova

1. Preveriti sem želel, katere tržne podatke je mogoče dobiti prek javnega API-ja.
2. Izbral sem majhne Python module, pri katerih ima vsaka datoteka eno glavno
   nalogo; glavni meni jih povezuje.
3. Za izračun uporabljam `Decimal`, da se cene ne pretvarjajo po nepotrebnem v
   približna binarna decimalna števila.
4. Odgovor API-ja preverim pred uporabo; pri napakah program izpiše sporočilo.
5. Za spremljanje uporabljam REST polling, ker je preprostejši za razlago in
   zagon kot trajna WebSocket povezava.
6. Dodal sem teste z `unittest`, ki preverijo podatke brez klicev na živo borzo.
7. Naročila so ločena od javnega branja podatkov in so omejena na testnet.

## Overjanje in testnet naročilo

Za javne trge in order book program ne potrebuje uporabniškega ključa. Za
naročilo uporablja uradni Python SDK. Program iz okolja prebere API zasebni
ključ, indeks računa in indeks API ključa. SDK ustvari podpisano naročilo in ga
pošlje na testnet. Za zasebne poizvedbe program pridobi kratkoživi žeton.

Uporaba zahteva registriran testnet API ključ. Vrednosti nastavi v lokalni
`.env` datoteki, ki ni namenjena Git repozitoriju. Vzorec je v `.env.example`.
Ključa nikoli ne vnašaj v Python datoteke ali ga pošiljaj drugim. MetaMask
obnovitvene fraze in zasebnega ključa denarnice ne vnašaj v `.env`; Python
program uporablja ločen Lighter API zasebni ključ.

Pred pošiljanjem program pokaže trg, stran, količino, ceno in vrsto naročila.
Odda ga samo po vnosu `ODDAJ`. Naročilo je limitno in post-only. Preklic
zahteva vnos `PREKLICI` in je dovoljen samo, če API potrdi, da je naročilo
odprto. Koda uporablja testnet naslov in ne preklopi na glavno omrežje.

**Rezultat preverjanja 23. 11. 2026:** Lighter SDK `v1.1.4` je z metodo
`check_client()` potrdil, da je lokalni API ključ registriran za testnet račun.
Preverjanje je bilo izvedeno v začasnem Python okolju v `/tmp`; projektne
datoteke zaradi tega niso bile spremenjene. Preverjanje potrdi ujemanje ključa
in računa, ne pa oddaje naročila.

SDK je bil nastavljen na testnet naslov `https://api.testnet.lighter.xyz` in
Lighter chain ID `300`. `check_client()` preveri podpisni ključ in njegovo
registracijo pri navedenem računu. Stanje računa je bilo preverjeno ločeno z
javnim, samo bralnim API klicem; pri tem se zasebni ključ ne uporablja.

Javni testnet API je vrnil podatke za izbrani račun. Vmesnik Lighter je
prikazoval 10.000 USDC in 1.000.000 LIT. API je pri USDC vrnil `balance` kot
0, vrednost 10.000 pa je bila navedena kot `collateral`, `available_balance`
in `margin_balance`. Gre za različna polja v odgovoru, ne za manjkajoči
kolateral.

Uradni SDK in njegovi primeri: [elliottech/lighter-python](https://github.com/elliottech/lighter-python).
REST metode so opisane v uradni [dokumentaciji API-ja za order book](https://docs.lighter.xyz/api/orders/orderbookorders)
in [dokumentaciji SDK za naročila](https://github.com/elliottech/lighter-python/blob/main/docs/OrderApi.md).

## Namestitev in zagon

Potrebuješ Python, internetno povezavo in Linux/macOS ali Windows terminal.

```bash
python -m pip install -r requirements.txt
python orderbook/main.py
```

Za testno naročilo kopiraj vzorec in nastavi spremenljivke okolja:

```bash
cp .env.example .env
chmod 600 .env
set -a
source .env
set +a
python orderbook/main.py
```

Če lokalna `.env` že obstaja, je ne prepiši z ukazom `cp`. V datoteko vpiši
vrednosti samo lokalno in omeji dostop do nje:

```bash
chmod 600 .env
```

`.env` je v `.gitignore`; v GitHub se objavi samo `.env.example` s praznimi
vrednostmi. Pred objavo preveri, da zasebni ključ ni dodan drugi datoteki,
posnetku zaslona ali sporočilu.

V meniju so povezava, seznam trgov, order book in spread, spremljanje cen,
graf, oddaja testnega naročila, pregled njegovega stanja in preklic.

## Testi

Testi ne potrebujejo žive povezave in ne pošiljajo naročil:

```bash
python -m unittest discover -s orderbook -p 'test_*.py' -v
```

Preverjajo order book, izračun spreada, neveljavne vrednosti, menjalne tečaje,
pretvorbo enot naročila in pripravo podatkov za graf.

## Uporabljene knjižnice

- `requests` za HTTP zahteve,
- `matplotlib` za grafe,
- uradni paket `lighter-sdk` za testnet naročila,
- `unittest` iz standardne knjižnice za teste.

`requirements.txt` vsebuje zunanje knjižnice, ki jih projekt uporablja.
Lighter SDK je pripet na različico `v1.1.4`, s katero je bila preverjena
testnet povezava. Različici `requests` in `matplotlib` nista pripeti na točno
številko, zato lahko namestitev pozneje dobi njune novejše različice.

## Ustvarjanje testnet računa in opravljeno preverjanje

Za uporabo testnega okolja je bil opravljen naslednji postopek:

1. V Firefoxu na Linux Mintu je bila nameščena razširitev MetaMask in ustvarjena
   nova denarnica.
2. Odprta je bila uradna aplikacija [Lighter testnet](https://testnet.app.lighter.xyz).
   V aplikacijo Lighter je bila prijava opravljena s povezavo MetaMask denarnice.
3. Po prijavi je bil izbran ukaz **Create Account** in ustvarjen Lighter
   testnet račun.
4. V `Portfolio → Assets` so bila vidna testna sredstva: 10.000 USDC in
   1.000.000 LIT. To so testna sredstva, ne pravi denar.
5. Za Python povezavo so bili v lokalni `.env` nastavljeni indeks računa,
   indeks API ključa in ločen API zasebni ključ. `.env` ima dovoljenja `600`
   in je izključen iz Git sledenja.
6. Uradni Lighter SDK je z `check_client()` uspešno preveril, da se API ključ
   ujema z računom. Dodatno je javni REST API vrnil stanje računa. Nobeno
   naročilo ali transakcija ni bila izvedena.

MetaMask je bil uporabljen za povezavo brskalnika in ustvarjanje računa v
aplikaciji. Python SDK se prijavi z ločenim API ključem, indeksom računa in
indeksom API ključa. MetaMask zasebni ključ ali obnovitvena fraza za ta Python
postopek nista potrebna in ju ne smemo kopirati v projekt.

Uradni viri: [Lighter testnet aplikacija](https://testnet.app.lighter.xyz),
[uradni Python SDK](https://github.com/elliottech/lighter-python) in
[implementacija `check_client()` v SDK](https://github.com/elliottech/lighter-python/blob/v1.1.4/lighter/signer_client.py).
