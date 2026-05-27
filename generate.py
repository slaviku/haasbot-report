import os, json, requests
from datetime import datetime, timezone

USERID        = os.getenv("HAAS_USERID")
INTERFACE_KEY = os.getenv("HAAS_INTERFACE_KEY")
BOT_IDS       = os.getenv("HAAS_BOT_IDS", "").split(",")

def fetch(bot_id):
    r = requests.get("https://api.haasbot.com/BotAPI.php", params={
        "channel": "GET_RUNTIME_REPORT",
        "userid": USERID, "interfaceKey": INTERFACE_KEY, "botId": bot_id
    }, timeout=15)
    d = r.json()
    if not d.get("Success"): return None
    return next(iter(d["Data"].values()))

def usd(v): return f"{'−' if v<0 else ''}${abs(v):,.2f}"
def pct(v): return f"{'+' if v>=0 else ''}{v:.2f}%"
def spark(vals, n=12):
    b=" ▁▂▃▄▅▆▇█"
    if not vals or max(vals)==min(vals): return "▄"*n
    lo,hi=min(vals),max(vals)
    return "".join(b[round((v-lo)/(hi-lo)*8)] for v in vals[-n:])

def card_html(bot_id, d):
    pr=d.get("PR",{}); p=d.get("P",{}); t=d.get("T",{}); o=d.get("O",{})
    rp=pr.get("RP",0); roi=pr.get("ROI",0)
    color="#3fb950" if rp>=0 else "#f85149"
    wt=p.get("W",0); ct=p.get("C",1)
    win=wt/ct*100
    now=datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    return f"""
    <div class="card" id="{bot_id}">
      <div class="card-top">
        <div><span class="market">{d.get('M','—')}</span></div>
        <span class="updated">Updated {now}</span>
      </div>
      <div class="metrics">
        <div class="metric"><div class="mlabel">Realized Profit</div>
          <div class="mval" style="color:{color}">{usd(rp)}</div></div>
        <div class="metric"><div class="mlabel">ROI</div>
          <div class="mval" style="color:{color}">{pct(roi)}</div></div>
        <div class="metric"><div class="mlabel">Win Rate</div>
          <div class="mval">{win:.1f}%</div></div>
        <div class="metric"><div class="mlabel">Avg Monthly</div>
          <div class="mval">{usd(pr.get('RM',0))}</div></div>
        <div class="metric"><div class="mlabel">Best Trade</div>
          <div class="mval">{usd(p.get('BW',0))}</div></div>
        <div class="metric"><div class="mlabel">Runtime</div>
          <div class="mval">{t.get('TM',0):.0f}h</div></div>
      </div>
      <div class="spark-row">
        <div><div class="slabel">ROI trend</div>
          <div class="spark">{spark(pr.get('ROIH',[]))}</div></div>
        <div><div class="slabel">Profit trend</div>
          <div class="spark">{spark(pr.get('RPH',[]))}</div></div>
      </div>
      <div class="extra">
        Closed trades: <b>{o.get('C',0):,}</b> &nbsp;·&nbsp;
        Winning: <b>{wt}/{ct}</b> &nbsp;·&nbsp;
        Fees: <b>{usd(d.get('F',{}).get('TFC',0))}</b> &nbsp;·&nbsp;
        Unrealized P&L: <b>{usd(pr.get('UP',0))}</b>
      </div>
    </div>"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HaasBot Live Report</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#e6edf3;font-family:'Inter',sans-serif;padding:2rem 1rem 4rem}}
h1{{font-size:1.5rem;font-weight:700;margin-bottom:.25rem}}
.sub{{color:#8b949e;font-size:.9rem;margin-bottom:2rem}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:1.5rem;margin-bottom:1.5rem;max-width:860px;margin-left:auto;margin-right:auto}}
.card-top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:1.25rem}}
.market{{font-family:'IBM Plex Mono',monospace;font-size:.85rem;background:#1c2128;border:1px solid #388bfd44;color:#58a6ff;padding:4px 12px;border-radius:20px}}
.updated{{font-size:.75rem;color:#484f58}}
.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-bottom:1.25rem}}
@media(max-width:500px){{.metrics{{grid-template-columns:repeat(2,1fr)}}}}
.metric{{background:#0d1117;border-radius:8px;padding:.75rem 1rem}}
.mlabel{{font-size:.72rem;color:#8b949e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.25rem}}
.mval{{font-size:1.3rem;font-weight:600}}
.spark-row{{display:flex;gap:2rem;margin-bottom:1rem}}
.slabel{{font-size:.72rem;color:#8b949e;margin-bottom:2px}}
.spark{{font-family:'IBM Plex Mono',monospace;font-size:1.2rem;color:#3fb950;letter-spacing:2px}}
.extra{{font-size:.8rem;color:#8b949e;border-top:1px solid #21262d;padding-top:.75rem;margin-top:.25rem}}
.extra b{{color:#e6edf3}}
.footer{{text-align:center;color:#484f58;font-size:.75rem;margin-top:2rem}}
</style></head><body>
<div style="max-width:860px;margin:0 auto">
<h1>📊 HaasBot Live Report</h1>
<div class="sub">Auto-updated every 2 minutes via GitHub Actions</div>
{cards}
<div class="footer">Last build: {build_time} · Powered by HaasBot + GitHub Pages</div>
</div></body></html>"""

cards = []
for bot_id in BOT_IDS:
    bot_id = bot_id.strip()
    if not bot_id: continue
    data = fetch(bot_id)
    if data: cards.append(card_html(bot_id, data))
    else: cards.append(f'<div class="card">❌ Failed to load bot {bot_id}</div>')

now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
html = HTML_TEMPLATE.format(cards="\n".join(cards), build_time=now)

with open("index.html", "w") as f:
    f.write(html)
print(f"✅ Generated index.html with {len(cards)} bot(s)")
