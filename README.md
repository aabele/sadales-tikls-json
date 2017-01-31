# e-st.lv datu lejuplādētājs

Lejuplādē klienta elektrības patēriņa datus no AS "Sadales tīkls" mājas lapas 
JSON formātā.

## Instalācija

```bash
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

## Lietošana

Skripts ļauj iegūt datus par konkrētu mēnesi, gadu vai dienu. Skaitītāja kodu var noskaidrot www.e-st.lv portālā.

```bash
 python scraper.py \
    --username xxx \
    --password xxx \
    --meter xxx \
    --period day \
    --year 2016 \
    --month 12 \
    --day 04 \
    --outfile data.json
```

Dokumentācija `python scraper.py -h`

Lietojiet paši uz savu atbildību!
