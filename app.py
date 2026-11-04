import time
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Terminal multi-actifs", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container{padding-top:0.8rem;padding-bottom:2rem}
/* Discrete fixed quote header: no dark card or rounded background. */
.st-key-market_header {
    position: fixed !important;
    top: 3.65rem;
    left: calc(21rem + 2.5rem);
    right: 2.5rem;
    width: auto !important;
    z-index: 1000;
    color: #111827 !important;
    background: rgba(255,255,255,.97) !important;
    border: 0 !important;
    border-bottom: 1px solid rgba(148,163,184,.24) !important;
    border-radius: 0 !important;
    padding: .55rem .2rem .8rem;
    box-shadow: none !important;
    backdrop-filter: blur(12px);
}
.market-header-top {display:flex;align-items:center;gap:.75rem;margin-bottom:.35rem}
.market-header-logo {width:39px;height:39px;object-fit:contain;flex-shrink:0;border-radius:50%}
.market-header-fallback {width:39px;height:39px;display:none;align-items:center;justify-content:center;font-size:25px}
.st-key-market_header .market-header-title {
    font-size:1.5rem;font-weight:750;line-height:1.25;
    margin:0;color:#111827 !important;
}
.st-key-market_header .market-header-label {
    font-size:.75rem;color:#64748b !important;
}
.st-key-market_header .market-header-number {
    font-size:1.38rem;font-weight:750;line-height:1.35;
    color:#111827 !important;font-variant-numeric:tabular-nums;
}
.st-key-market_header .market-header-number.pos {color:#15803d !important}
.st-key-market_header .market-header-number.neg {color:#dc2626 !important}
.st-key-market_header .market-header-number.flat {color:#64748b !important}
.market-header-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}
.market-header-spacer {height:145px}
body:has(section[data-testid="stSidebar"][aria-expanded="false"]) .st-key-market_header {
    left: 2rem;
}
@media(max-width:900px) {
    .st-key-market_header {left:1rem !important;right:1rem;top:3.25rem;padding:.45rem .2rem .6rem}
    .st-key-market_header .market-header-title {font-size:1.2rem}
    .st-key-market_header .market-header-number {font-size:1.1rem}
    .st-key-market_header .market-header-label {font-size:.7rem}
    .market-header-logo,.market-header-fallback{width:31px;height:31px}
    .market-header-spacer {height:130px}
}

section[data-testid="stSidebar"]{min-width:315px}
.asset-row{display:flex;align-items:center;gap:8px;padding:8px 6px;border-bottom:1px solid rgba(128,128,128,.15);color:inherit!important;text-decoration:none!important}
.asset-row:hover{background:rgba(128,128,128,.11);border-radius:7px}
.asset-row.active{background:rgba(46,125,245,.15);border-radius:7px}
.asset-icon{height:27px;width:27px;object-fit:contain;border-radius:50%;background:white;padding:3px}
.asset-fallback{width:27px;text-align:center;font-size:19px}
.asset-title{font-weight:650;font-size:13px}
.asset-symbol{opacity:.65;font-size:11px}
.asset-price{font-size:12px;font-variant-numeric:tabular-nums;white-space:nowrap}
.asset-change{font-size:12px;font-weight:750;font-variant-numeric:tabular-nums}
.asset-right{margin-left:auto;text-align:right}
.pos{color:#21b56f}.neg{color:#ee5757}.flat{color:#999}
@keyframes priceUp{0%{background:rgba(25,175,90,.45)}100%{background:transparent}}
@keyframes priceDown{0%{background:rgba(220,50,50,.45)}100%{background:transparent}}
.flash-up{animation:priceUp 2.4s ease-out;border-radius:6px}
.flash-down{animation:priceDown 2.4s ease-out;border-radius:6px}
</style>""",unsafe_allow_html=True)

# Les prix sont publics et potentiellement différés. Aucun flux de marché sous licence n'est inclus.
ASSETS=[
 dict(id='xau',name='XAUUSD',symbol='XAUUSD=X',alt='GC=F',icon='🥇',unit='USD/oz',note='Or spot XAU/USD si disponible ; sinon futures or GC=F (proxy, non identique).'),
 dict(id='btc',name='BTCUSD',symbol='BTC-USD',icon='₿',unit='USD',note='Bitcoin/USD, marché 24 h/24.'),
 dict(id='brent',name='BRN1! · Brent',symbol='BZ=F',icon='🛢️',unit='USD/baril',note='BZ=F : Brent front-month Yahoo ; pas la série continue BRN1! de TradingView.'),
 dict(id='vix',name='VIX CBOE',symbol='^VIX',icon='📊',unit='points',note='Indice de volatilité CBOE VIX.'),
 dict(id='cac',name='CAC 40',symbol='^FCHI',icon='🇫🇷',unit='points',note='Indice CAC 40.'),
 dict(id='dax',name='DEU 40 · DAX',symbol='^GDAXI',icon='🇩🇪',unit='points',note='Indice DAX, approximation de DEU40.'),
 dict(id='spx',name='SPX · S&P 500',symbol='^GSPC',icon='🇺🇸',unit='points',note='Indice S&P 500.'),
 dict(id='ndq',name='NDQ · Nasdaq 100',symbol='^NDX',icon='💻',unit='points',note='Nasdaq 100.'),
 dict(id='smi',name='SMI',symbol='^SSMI',icon='🇨🇭',unit='points',note='Swiss Market Index.'),
 dict(id='sg',name='Saint-Gobain',symbol='SGO.PA',domain='saint-gobain.com',unit='EUR',note='Action Euronext Paris.'),
 dict(id='ai',name='Air Liquide',symbol='AI.PA',domain='airliquide.com',unit='EUR',note='Action Euronext Paris.'),
 dict(id='saf',name='Safran',symbol='SAF.PA',domain='safran-group.com',unit='EUR',note='Action Euronext Paris.'),
 dict(id='airbus',name='Airbus',symbol='AIR.PA',domain='airbus.com',unit='EUR',note='Action Euronext Paris.'),
 dict(id='thales',name='Thales',symbol='HO.PA',domain='thalesgroup.com',unit='EUR',note='Action Euronext Paris.'),
 dict(id='dassault',name='Dassault Aviation',symbol='AM.PA',domain='dassault-aviation.com',unit='EUR',note='Dassault Aviation, non Dassault Systèmes.'),
 dict(id='schneider',name='Schneider Electric',symbol='SU.PA',domain='se.com',unit='EUR',note='Action Euronext Paris.'),
 dict(id='lvmh',name='LVMH',symbol='MC.PA',domain='lvmh.com',unit='EUR',note='Action Euronext Paris.'),
]
FRAMES = {
    "1 min": ("1m", "5d", 100),
    "5 min": ("5m", "1mo", 110),
    "15 min": ("15m", "1mo", 110),
    "30 min": ("30m", "1mo", 100),
    "1 h": ("60m", "3mo", 120),
    "4 h": ("60m", "60d", 100),
    "1 jour": ("1d", "2y", 120),
    "1 semaine": ("1wk", "5y", 100),
    "1 mois": ("1mo", "10y", 72),
}

@st.cache_data(ttl=25, show_spinner=False)
def get_data(symbol, interval, period):
    try:
        df = yf.download(symbol, period=period, interval=interval,
                         auto_adjust=False, progress=False, threads=False)
        if df is None or df.empty:
            return pd.DataFrame(), "Pas de données fournies"
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.rename(columns=str.title).sort_index()
        if any(k not in df.columns for k in ("Open", "High", "Low", "Close")):
            return pd.DataFrame(), "Données OHLC incomplètes"
        return df.dropna(subset=["Open", "High", "Low", "Close"]), ""
    except Exception as ex:
        return pd.DataFrame(), str(ex)[:160]

def last_session_pct(df):
    if df.empty:
        return None
    # Retour de la dernière session par rapport à la dernière clôture précédente.
    local_dates = pd.Index(df.index.date)
    current_day = local_dates[-1]
    previous = df.loc[local_dates < current_day, "Close"]
    if previous.empty:
        return None
    base = float(previous.iloc[-1])
    return (float(df["Close"].iloc[-1]) / base - 1) * 100 if base else None

def quote(asset):
    sym = asset["symbol"]
    df, err = get_data(sym, "5m", "5d")
    fallback = False
    if df.empty and asset.get("alt"):
        sym = asset["alt"]
        df, err = get_data(sym, "5m", "5d")
        fallback = not df.empty
    if df.empty:
        df, err = get_data(sym, "1d", "7d")
    if df.empty:
        return dict(price=None, pct=None, stamp=None, symbol=sym, error=err, fallback=fallback)
    price = float(df["Close"].iloc[-1])
    pct = last_session_pct(df)
    if pct is None and len(df) > 1:
        prev = float(df["Close"].iloc[-2])
        pct = (price / prev - 1) * 100 if prev else None
    return dict(price=price, pct=pct, stamp=str(df.index[-1]), symbol=sym,
                error="", fallback=fallback)

@st.cache_data(ttl=25, show_spinner=False)
def all_quotes():
    return {a["id"]: quote(a) for a in ASSETS}

def format_price(p):
    if p is None:
        return "—"
    dp = 4 if p < 2 else 2
    return f"{p:,.{dp}f}".replace(",", " ")

with st.sidebar:
    st.subheader("Marchés")
    st.caption("Actualisation automatique toutes les 30 s · cours publics potentiellement différés")

# The 25s cache expires between two 30s refreshes, preventing stale repeat results.
# The external data provider may publish a new price less frequently.
st_autorefresh(interval=30_000, limit=None, key="quotes_poll")

quotes = all_quotes()
previous_prices = st.session_state.get("previous_prices", {})
next_prices = {}
valid_ids = [a["id"] for a in ASSETS]
try:
    selected = st.query_params.get("asset", "brent")
except Exception:
    selected = "brent"
if selected not in valid_ids:
    selected = "brent"

for asset in ASSETS:
    ident = asset["id"]
    q = quotes[ident]
    price = q["price"]
    next_prices[ident] = price
    old_price = previous_prices.get(ident)
    direction = ""
    if price is not None and old_price is not None:
        if price > old_price:
            direction = "flash-up"
        elif price < old_price:
            direction = "flash-down"
    pct = q["pct"]
    change_class = "flat" if pct is None else ("pos" if pct > 0 else "neg" if pct < 0 else "flat")
    pct_label = "—" if pct is None else f"{pct:+.2f}%"
    if asset.get("domain"):
        icon = (f'<img class="asset-icon" src="https://www.google.com/s2/favicons?domain={asset["domain"]}&sz=64" alt="">')
    else:
        icon = f'<span class="asset-fallback">{asset["icon"]}</span>'
    selected_class = " active" if ident == selected else ""
    st.sidebar.markdown(
        f'<a class="asset-row{selected_class} {direction}" href="?asset={ident}" target="_self">'
        f'{icon}<span><span class="asset-title">{asset["name"]}</span><br>'
        f'<span class="asset-symbol">{q["symbol"]}</span></span>'
        f'<span class="asset-right"><span class="asset-price">{format_price(price)}</span><br>'
        f'<span class="asset-change {change_class}">{pct_label}</span></span></a>',
        unsafe_allow_html=True)
st.session_state["previous_prices"] = next_prices

asset = next(a for a in ASSETS if a["id"] == selected)
q = quotes[selected]
pct=q["pct"]
pct_class="flat" if pct is None else ("pos" if pct>0 else "neg" if pct<0 else "flat")
pct_label="—" if pct is None else f"{pct:+.2f}%"

# TradingView symbol: ICEEUR:BRN1! . The CDN icon is attempted first;
# if unavailable, the oil pictogram is displayed instead of a broken image.
brent_logo_url = "https://s3-symbol-logo.tradingview.com/commodity/brent-crude-oil--big.svg"
logo_html = (
    '<a href="https://fr.tradingview.com/symbols/ICEEUR-BRN1%21/" '
    'target="_blank" rel="noopener noreferrer" title="Brent sur TradingView">'
    f'<img class="market-header-logo" src="{brent_logo_url}" alt="Brent" '
    'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'inline-flex\';">'
    '<span class="market-header-fallback" aria-hidden="true">🛢️</span></a>'
    if selected == "brent" else ""
)
with st.container(key="market_header"):
    st.markdown(
        f'<div class="market-header-top">{logo_html}'
        f'<div class="market-header-title">{asset["name"]}</div></div>'
        f'<div class="market-header-grid">'
        f'<div><div class="market-header-label">Dernier cours disponible</div>'
        f'<div class="market-header-number">{format_price(q["price"])} {asset["unit"]}</div></div>'
        f'<div><div class="market-header-label">Variation de session (estimée)</div>'
        f'<div class="market-header-number {pct_class}">{pct_label}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
# Reserve vertical space so that the fixed quote bar does not cover timeframe controls.
st.markdown('<div class="market-header-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
if q["price"] is None:
    st.error(f'Cours indisponible : {q["error"]}')

st.divider()
frame = st.segmented_control("Unité de temps", options=list(FRAMES),
                             default="1 jour", key=f'frame_{selected}')
if not frame:
    frame = "1 jour"
interval, period, default_candles = FRAMES[frame]
df, error = get_data(q["symbol"], interval, period)

if df.empty:
    st.warning(f"Impossible de charger les bougies {frame} : {error}")
else:
    if frame == "4 h":
        # 4h constituées de 4 barres 1h ; pas d'upsampling artificiel.
        agg = {"Open":"first", "High":"max", "Low":"min", "Close":"last"}
        if "Volume" in df.columns:
            agg["Volume"] = "sum"
        df = df.resample("4h").agg(agg).dropna(subset=["Open","High","Low","Close"])
    df = df.copy()
    for n in (20, 50, 200):
        df[f"SMA{n}"] = df.Close.rolling(n).mean()
    delta = df.Close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - 100 / (1 + rs)
    has_volume = "Volume" in df and df.Volume.notna().any() and df.Volume.sum()>0

    with st.expander("Réglages du graphique et des axes", expanded=True):
        x1,x2,x3=st.columns([1.3,1.3,1])
        max_bars=len(df)
        visible_bars=x1.slider("Nombre de bougies visibles (axe X)", min_value=min(15,max_bars),
                               max_value=max_bars, value=min(default_candles,max_bars),
                               key=f'bars_{selected}_{frame}')
        end_pos=x2.slider("Déplacement dans l'historique", min_value=min(visible_bars-1,max_bars-1),
                          max_value=max_bars-1,value=max_bars-1,
                          key=f'end_{selected}_{frame}')
        height=x3.slider("Hauteur du graphique",400,900,650,step=50,key=f'height_{selected}')
        auto_y=st.checkbox("Axe des prix automatique (zone visible)",value=True,
                           key=f'autoy_{selected}_{frame}')
        manual_min=manual_max=None
        if not auto_y:
            y1,y2=st.columns(2)
            manual_min=y1.number_input("Prix minimum (axe Y)",value=float(df.Low.min()),
                                       format="%.4f",key=f'ymin_{selected}_{frame}')
            manual_max=y2.number_input("Prix maximum (axe Y)",value=float(df.High.max()),
                                       format="%.4f",key=f'ymax_{selected}_{frame}')
            if manual_max<=manual_min:
                st.warning("Le maximum doit être supérieur au minimum.")
                manual_min=manual_max=None
        show_sma=st.multiselect("Moyennes mobiles",options=[20,50,200],default=[20,50,200],
                                key=f'mas_{selected}_{frame}')
        st.caption("Molette : zoom · glisser : déplacer · double-clic : réinitialiser · bouton caméra : sauvegarder l'image")

    start_pos=max(0,end_pos-visible_bars+1)
    shown=df.iloc[start_pos:end_pos+1]
    labels=[v.strftime("%d/%m %H:%M") if frame in ("1 min","5 min","15 min","30 min","1 h","4 h")
            else v.strftime("%d/%m/%Y") for v in df.index]
    # Catégories ordinales : les week-ends et nuits non cotées ne dilatent pas le graphique.
    inds=list(range(len(df)))
    candle_colors=dict(increasing_line_color="#19b979",decreasing_line_color="#ec5860",
                       increasing_fillcolor="#19b979",decreasing_fillcolor="#ec5860")
    row_heights=[0.70,0.15,0.15] if has_volume else [0.79,0.21]
    rows=len(row_heights)
    fig=make_subplots(rows=rows,cols=1,shared_xaxes=True,vertical_spacing=.035,row_heights=row_heights)
    fig.add_trace(go.Candlestick(x=inds,open=df.Open,high=df.High,low=df.Low,close=df.Close,
                                 name="Bougies",**candle_colors),row=1,col=1)
    colors={20:"#e3a34d",50:"#599be8",200:"#b490dd"}
    for n in show_sma:
        fig.add_trace(go.Scatter(x=inds,y=df[f"SMA{n}"],name=f"SMA {n}",
                                 line=dict(width=1.4,color=colors[n])),row=1,col=1)
    vol_row=2 if has_volume else None
    rsi_row=3 if has_volume else 2
    if has_volume:
        vol_colors=np.where(df.Close>=df.Open,"#19b979","#ec5860")
        fig.add_trace(go.Bar(x=inds,y=df.Volume,name="Volume",marker_color=vol_colors,
                             showlegend=False),row=vol_row,col=1)
    fig.add_trace(go.Scatter(x=inds,y=df.RSI,name="RSI 14",line=dict(color="#a889f7",width=1.5)),
                  row=rsi_row,col=1)
    fig.add_hline(y=70,line_dash="dot",line_color="#b78888",row=rsi_row,col=1)
    fig.add_hline(y=30,line_dash="dot",line_color="#7eac93",row=rsi_row,col=1)
    fig.update_yaxes(range=[0,100],row=rsi_row,col=1)
    if manual_min is not None:
        yrange=[manual_min,manual_max]
    else:
        low=float(shown.Low.min());high=float(shown.High.max())
        pad=max((high-low)*.06,abs(high)*.0005,.001)
        yrange=[low-pad,high+pad]
    fig.update_yaxes(range=yrange,side="right",row=1,col=1)
    tickstep=max(1,visible_bars//9)
    tickvals=list(range(start_pos,end_pos+1,tickstep))
    if end_pos not in tickvals:tickvals.append(end_pos)
    for row in range(1,rows+1):
        fig.update_xaxes(range=[start_pos-.8,end_pos+1.0],tickmode="array",
                         tickvals=tickvals,ticktext=[labels[i] for i in tickvals],
                         showgrid=True,gridcolor="rgba(130,130,130,.12)",row=row,col=1)
        fig.update_yaxes(showgrid=True,gridcolor="rgba(130,130,130,.12)",row=row,col=1)
    fig.update_layout(height=height,xaxis_rangeslider_visible=False,
                      margin=dict(l=12,r=55,t=30,b=18),
                      legend=dict(orientation="h",x=0,y=1.05),
                      hovermode="x unified",dragmode="pan",
                      uirevision=f'{selected}:{frame}:{start_pos}:{end_pos}:{auto_y}:{manual_min}:{manual_max}',
                      showlegend=True)
    st.plotly_chart(fig,use_container_width=True,
                    config={"scrollZoom":True,"displaylogo":False,
                            "modeBarButtonsToAdd":["drawline","eraseshape"],"responsive":True})
    st.caption(f'{len(shown)} bougies à l’écran sur {len(df)} disponibles · période visible : {df.index[start_pos]} à {df.index[end_pos]}')

