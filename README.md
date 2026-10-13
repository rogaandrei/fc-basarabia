# Site FC Basarabia (cu actualizare automată)

Site-ul se actualizează singur: la fiecare 3 ore, GitHub citește clasamentul, programul și lotul de pe
site-ul ligii (alborzminifotbal.ro), actualizează datele și republică site-ul. Nu trebuie să faci nimic.

Ce se schimbă automat: clasamentul, golurile marcate/primite, scorurile și programul din **Meciuri**,
golurile jucătorilor, „Victorii consecutive”, jucătorii noi din lot, antrenorul/delegații.

---

## Instalare (o singură dată, ~10 minute, gratuit)

### 1. Cont și repository pe GitHub
1. Intră pe https://github.com și fă-ți un cont (dacă nu ai).
2. Apasă **+ → New repository**. Nume: `fc-basarabia`. Alege **Public** (Pages gratuit cere repository public).
   Nu bifa „Add a README”. Apasă **Create repository**.

### 2. Încarcă fișierele
1. Dezarhivează `fc-basarabia-site.zip`.
2. În repository apasă **uploading an existing file**.
3. Trage în pagină **tot conținutul folderului** (index.html, style.css, script.js, data.js, data.json,
   config.json, requirements.txt, README.md și folderele `img`, `scripts`, `tests`, `.github`).
   - Atenție: folderul `.github` este ascuns pe unele calculatoare (pe Windows: Vizualizare → Elemente ascunse;
     pe Mac: Cmd+Shift+. în Finder). Fără el nu merge actualizarea automată.
4. Jos apasă **Commit changes**.

### 3. Pornește publicarea
1. În repository: **Settings → Pages**.
2. La **Source** alege **GitHub Actions**.
3. Mergi la fila **Actions**. Dacă apare un buton verde de activare a workflow-urilor, apasă-l.
4. Alege workflow-ul **„Actualizează și publică site-ul”** → **Run workflow** → **Run workflow**.
5. După 1-2 minute apare bifa verde. Adresa site-ului este:
   `https://NUMELE-TAU.github.io/fc-basarabia/` (o vezi și în Settings → Pages).

De acum rulează singur, la fiecare 3 ore.

---

## Cum modifici lucruri

| Ce vrei | Ce faci |
|---|---|
| Actualizare imediată | Actions → „Actualizează și publică site-ul” → **Run workflow** |
| Poză jucător | Pune poza în `img/players/` cu numele jucătorului scris cu litere mici și cratime, fără diacritice: `andronic-sergiu.jpg`. Apare la următoarea rulare. |
| Poze noi în galerie | Pune-le în `img/gallery/` (ex: `16.jpg`, `17.jpg`). Apar în ordinea numelor fișierelor. |
| Poziția unui jucător nou | Editează `config.json` → `pozitii` (P portar, A apărător, M mijlocaș, T atacant). Până atunci apare la „Alți jucători”. |
| Diacritice la un nume | `config.json` → `diacritice` (pagina ligii nu are diacritice). |
| Text, culori, linkuri | `index.html` și `style.css` |

Încărcare fișier nou: în repository apasă **Add file → Upload files**, apoi **Commit changes**.

---

## Ce faci dacă ceva nu merge

- **Rularea apare cu ❌ în fila Actions:** deschide rularea și pasul „Citește datele de pe site-ul ligii”.
  Mesajul spune ce pagină nu a putut fi citită. Site-ul rămâne cu datele vechi (nu se strică), iar restul paginilor
  care s-au citit bine se actualizează.
- **Liga a schimbat aspectul paginilor:** scriptul `scripts/update.py` trebuie ajustat. Salvează paginile
  (clasament, program, lot) ca `clasament.html`, `program.html`, `lot.html` în `tests/fixtures/`,
  rulează `python tests/test_parse.py` și trimite-mi rezultatul.
- **Repository fără activitate 60 de zile:** GitHub poate opri rulările programate. Dacă se întâmplă, apasă
  **Enable workflow** în fila Actions. Pe durata sezonului, actualizările din Actions numără ca activitate.
- **Orele** rulărilor sunt în UTC (în România = UTC+2/+3), iar GitHub poate întârzia o rulare cu câteva minute.
- Datele sunt citite doar din 3 pagini publice ale ligii, de 8 ori pe zi. Dacă liga preferă să nu fie citite
  automat, șterge `.github/workflows/update.yml` și datele rămân cele de la ultima rulare.

---

## Rulare locală (opțional)

```bash
pip install -r requirements.txt
python scripts/update.py            # citește paginile ligii și scrie data.json + data.js
python tests/test_parse.py          # verifică parserul pe paginile din tests/fixtures
```

Deschide `index.html` în browser. Site-ul citește datele din `data.js`, deci merge și deschis direct din folder.
Fonturile (Barlow) se încarcă de pe Google Fonts, deci au nevoie de internet.

## Structura

```
index.html  style.css  script.js     site-ul
data.js  data.json                   datele (scrise de scripts/update.py, nu le edita manual)
config.json                          pozițiile jucătorilor și diacriticele
img/                                 sigla, poza de grup, img/players/, img/gallery/
scripts/update.py                    citește paginile ligii
.github/workflows/update.yml         rularea automată + publicarea
tests/                               teste pentru parser
```
