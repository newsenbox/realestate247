# Autonomous Property Engine — Multi-County Real Estate Deal Scraper

A self-generating, background-running deal pipeline that proactively scrapes public delinquent tax records, probate filings, and municipal code violations to identify abandoned or "forgotten" properties.

## Features

- **Multi-County Support**: Miami-Dade, Broward, Orange, Hillsborough, Pinellas — configurable county API endpoints
- **Auto-Scraper Dashboard**: One-click scrape of tax delinquent lists, code violations, and probate filings
- **Manual Search & E-Sign**: Look up any folio, analyze the deal, generate a Florida Assignment Contract with e-signature canvas
- **Deal Analytics**: 6 interactive Plotly charts (MAO distribution, ARV distribution, priority score, tier breakdown, delinquency vs MAO scatter, repairs vs market value scatter), KPI cards, filterable data table with Google Maps links
- **Google Maps Links**: Every property has a 🗺️ link to view on Google Maps
- **Export**: CSV export of filtered leads, top 10 deals, full analytics data
- **Background Pipeline**: Auto-scrape on page load and every 30 minutes (optional)

## Quick Start

```bash
pip install -r requirements.txt
streamlit run property_engine.py
```

Or deploy to Streamlit Cloud:

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Set main file to `property_engine.py`
5. Deploy

## Counties Configured

| County | PA API |
|--------|--------|
| Miami-Dade | https://www.miamidadepa.gov/pa/api/property/{folio} |
| Broward | https://www.browardpa.gov/api/property/{folio} |
| Orange | https://www.ocpau.com/api/property/{folio} |
| Hillsborough | https://www.hcpafl.org/api/property/{folio} |
| Pinellas | https://www.pcpao.org/api/property/{folio} |

## License

© 360 New Beginning LLC
