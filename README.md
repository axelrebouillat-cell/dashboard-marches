# Dashboard Marchés

Terminal Streamlit avec 17 actifs, cotations publiques Yahoo Finance et 9 unités de temps.

## Lancer en local
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Héberger sur Streamlit Community Cloud
Créer une app depuis le dépôt `axelrebouillat-cell/dashboard-marches`, branche `main`, chemin `app.py`.

## Avertissements
Données publiques Yahoo Finance : latence, disponibilité et mise à jour non garanties. Le pourcentage affiché compare deux clôtures journalières disponibles. Les futures Brent BZ=F ne sont pas le continu TradingView BRN1!. Le tableau de bord n'exécute pas d'ordres.
