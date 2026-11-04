import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf

st.set_page_config(page_title="Terminal multi-actifs", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container{padding-top:1rem}.stSidebar [data-testid="stSidebarContent"]{padding-top:1rem}
.asset-row{display:flex;align-items:center;gap:10px;padding:9px 7px;border-bottom:1px solid rgba(128,128,128,.16);text-decoration:none!important;color:inherit!important}
.asset-row:hover{background:rgba(128,128,128,.12);border-radius:8px}
.asset-row.active{background:rgba(76,134,255,.14);border-radius:8px}
.asset-icon{height:28px;width:28px;object-fit:contain;border-radius:50%;background:white;padding:3px}
.asset-fallback{width:28px;text-align:center;font-size:20px}.asset-title{font-weight:600;font-size:13px}
.asset-price{font-size:12px;opacity:.85}.asset-change{font-size:12px;font-weight:700;white-space:nowrap}
.asset-right{margin-left:auto;text-align:right}.pos{color:#16a34a}.neg{color:#dc2626}.flat{color:#9ca3af}
</style>""",unsafe_allow_html=True)

# Les instruments similaires sont signalés : aucune cotation n'est inventée.
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
FRAMES={'1 min':('1m','5d'),'5 min':('5m','1mo'),'15 min':('15m','1mo'),'30 min':('30m','1mo'),'1 h':('60m','3mo'),'4 h':('60m','2y'),'1 jour':('1d','2y'),'1 semaine':('1wk','5y'),'1 mois':('1mo','10y')}

@st.cache_data(ttl=120,show_spinner=False)
def get_data(symbol,interval='1d',period='5d'):
    try:
        df=yf.download(symbol,period=period,interval=interval,progress=False,auto_adjust=False,threads=False)
        if df is None or df.empty: return pd.DataFrame(), 'Aucune cotation disponible'
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        df=df.rename(columns=str.title)
        if any(c not in df for c in ('Open','High','Low','Close')): return pd.DataFrame(),'OHLC incomplet'
        return df.dropna(subset=['Close']).sort_index(),''
    except Exception as e:
        return pd.DataFrame(),str(e)[:180]

def quote(asset):
    df,err=get_data(asset['symbol'],'1d','7d')
    sym=asset['symbol']; fallback=False
    if df.empty and asset.get('alt'):
        sym=asset['alt'];df,err=get_data(sym,'1d','7d');fallback=True
    if df.empty: return dict(price=None,change=None,error=err,symbol=sym,fallback=fallback,stamp=None)
    last=float(df['Close'].iloc[-1]);prev=float(df['Close'].iloc[-2]) if len(df)>1 else None
    change=(last/prev-1)*100 if prev and prev>0 else None
    return dict(price=last,change=change,error='',symbol=sym,fallback=fallback,stamp=str(df.index[-1]))

@st.cache_data(ttl=120,show_spinner=False)
def quotes_all(): return {a['id']:quote(a) for a in ASSETS}

if st.sidebar.button('↻ Actualiser les cotations',use_container_width=True):
    get_data.clear();quotes_all.clear();st.rerun()
st.sidebar.caption('Yahoo Finance public · cache 2 min · cours potentiellement différés')
quotes=quotes_all()
valid_ids=[a['id'] for a in ASSETS]
try: selected=st.query_params.get('asset','brent')
except Exception: selected='brent'
if selected not in valid_ids: selected='brent'

for a in ASSETS:
    q=quotes[a['id']]
    price='Indisponible' if q['price'] is None else f"{q['price']:,.2f}".replace(',',' ')
    ch=q['change']; cls='flat' if ch is None else ('pos' if ch>0 else 'neg' if ch<0 else 'flat')
    pct='—' if ch is None else f"{ch:+.2f}%"
    icon=(f'<img class="asset-icon" src="https://www.google.com/s2/favicons?domain={a["domain"]}&sz=64" alt="">' if a.get('domain') else f'<span class="asset-fallback">{a["icon"]}</span>')
    active=' active' if selected==a['id'] else ''
    st.sidebar.markdown(f'<a class="asset-row{active}" href="?asset={a["id"]}" target="_self">{icon}<span><span class="asset-title">{a["name"]}</span><br><span class="asset-price">{a["symbol"]}</span></span><span class="asset-right"><span class="asset-price">{price}</span><br><span class="asset-change {cls}">{pct}</span></span></a>',unsafe_allow_html=True)

asset=next(a for a in ASSETS if a['id']==selected);q=quotes[selected]
st.title(asset['name'])
st.caption(f"Ticker : {q['symbol']} · {asset['note']}")
if q['fallback']:st.warning('Le futures or GC=F remplace ici le prix spot XAUUSD ; instruments différents.')
if q['price'] is None:
    st.error(f"Prix indisponible pour {asset['name']}. {q['error']}")
else:
    a,b,c=st.columns([1,1,2])
    a.metric('Dernier cours disponible',f"{q['price']:,.2f} {asset['unit']}",f"{q['change']:+.2f}%" if q['change'] is not None else None)
    b.metric('Variation entre les deux dernières clôtures',f"{q['change']:+.2f}%" if q['change'] is not None else '—')
    c.caption(f"Dernière barre journalière : {q['stamp']}. La variation compare les deux dernières clôtures disponibles, pas nécessairement le dernier prix en séance.")

frame=st.selectbox('Unité de temps',list(FRAMES),index=6)
interval,period=FRAMES[frame]
df,err=get_data(q['symbol'],interval,period)
if df.empty:
    st.warning(f"Historique indisponible pour cette unité de temps : {err}")
else:
    if frame=='4 h':
        # Construit les 4h à partir des bougies 1h, jamais depuis les données quotidiennes.
        agg={'Open':'first','High':'max','Low':'min','Close':'last'}
        if 'Volume' in df: agg['Volume']='sum'
        df=df.resample('4h').agg(agg).dropna(subset=['Close'])
    df=df.copy()
    for n in (20,50,200): df[f'MM{n}']=df['Close'].rolling(n).mean()
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=df.index,open=df.Open,high=df.High,low=df.Low,close=df.Close,name=asset['name']))
    for n in (20,50,200):fig.add_trace(go.Scatter(x=df.index,y=df[f'MM{n}'],name=f'MM{n}',mode='lines'))
    fig.update_layout(height=590,xaxis_rangeslider_visible=False,margin=dict(l=10,r=10,t=30,b=10),legend=dict(orientation='h'))
    st.plotly_chart(fig,use_container_width=True)
    if 'Volume' in df and df['Volume'].notna().any() and df['Volume'].sum()>0:
        vf=go.Figure(go.Bar(x=df.index,y=df.Volume,name='Volume'))
        vf.update_layout(height=190,margin=dict(l=10,r=10,t=10,b=10));st.plotly_chart(vf,use_container_width=True)
    delta=df.Close.diff()
    up=delta.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    down=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    rsi=100-100/(1+up/down.replace(0,np.nan))
    rf=go.Figure(go.Scatter(x=df.index,y=rsi,name='RSI 14'))
    rf.add_hline(y=70,line_dash='dash');rf.add_hline(y=30,line_dash='dash')
    rf.update_layout(height=190,yaxis_range=[0,100],margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(rf,use_container_width=True)

st.info('Yahoo Finance n’est pas un flux officiel garanti en temps réel. Les données peuvent être différées, incomplètes ou indisponibles. BRN1! est représenté par BZ=F, un instrument approchant.')
st.caption('Aucun ordre de bourse n’est envoyé.')
