# SC Kolín – automatický odebíraný kalendář

Neoficiální fanouškovský kalendář A-týmu. Zdroj: https://sckolin.cz/matches/MUZ

## Zprovoznění (GitHub Pages)
1. Vytvořte **veřejný** GitHub repozitář, například `sc-kolin-kalendar`.
2. Nahrajte **obsah této složky** do kořene repozitáře včetně `.github/workflows/update.yml` (při nahrávání ZIP nejprve rozbalte).
3. V **Settings → Pages → Build and deployment → Source** zvolte **GitHub Actions**.
4. V **Actions** otevřete workflow `Aktualizace kalendare SC Kolin` a spusťte **Run workflow** (nebo jej spustí push).
5. Po úspěšném běhu bude soubor na adrese `https://UZIVATEL.github.io/sc-kolin-kalendar/kalendar.ics` (u jiného názvu repozitáře jej upravte).
6. V iPhonu: **Nastavení → Aplikace → Kalendář → Kalendářové účty → Přidat účet → Jiný → Přidat odebíraný kalendář**. Vložte URL s `https://` (případně `webcal://`), potvrďte.

Aktualizace na GitHubu jsou plánovány každých 6 hodin; GitHub Actions se může opozdit a Apple si odebíraný kalendář obnovuje vlastním tempem.

**Pozor:** Při změně struktury klubového webu může být nutné upravit parser. Workflow při neúspěšném načtení nepřepíše publikovaný soubor. Čas konce zápasu je orientačně +2 h 30 min. Názvy zápasů jsou převzaty z webu. Kalendář neověřuje stav utkání (odloženo/zrušeno); termín zobrazený na webu je převzat i u odloženého utkání. Upozornění před zápasem závisí na podpoře odebíraných alarmů v Apple Kalendáři.

Bez oficiálního API jde o nezávislé čtení veřejné webové stránky, nikoli klubem garantovanou službu.
