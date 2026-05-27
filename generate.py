import os, requests
from datetime import datetime, timezone

USERID        = os.getenv("HAAS_USERID")
INTERFACE_KEY = os.getenv("HAAS_INTERFACE_KEY")
BOT_IDS       = [b.strip() for b in os.getenv("HAAS_BOT_IDS", "").split(",") if b.strip()]
BASE           = "https://api.haasbot.com/BotAPI.php"

def fetch_runtime(bot_id):
    r = requests.get(BASE, params={
        "channel": "GET_RUNTIME", "userid": USERID,
        "interfaceKey": INTERFACE_KEY, "botid": bot_id
    }, timeout=15)
    return r.json() if r.ok else None

def usd(v, dec=2):
    if v is None: return "—"
    sign = "−" if v < 0 else ""
    return f"{sign}${abs(v):,.{dec}f}"

def pct(v):
    if v is None: return "—"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"

def pct_color(v):
    return "#3fb950" if v >= 0 else "#f85149"

def spark(vals, n=15):
    b = " ▁▂▃▄▅▆▇█"
    if not vals or max(vals) == min(vals): return "▄" * min(n, len(vals) or n)
    lo, hi = min(vals), max(vals)
    return "".join(b[round((x - lo) / (hi - lo) * 8)] for x in vals[-n:])

def direction_label(d):
    # d=0=Long, d=1=Short in positions
    return ("🟢 Long", "#3fb950") if d == 0 else ("🔴 Short", "#f85149")

def fmt_ts(ts):
    if not ts: return "—"
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    except:
        return "—"

def open_orders_html(orders):
    if not orders:
        return '<div class="no-data">No open orders</div>'
    rows = ""
    for o in orders:
        d = o.get("d", 0)
        label = "Long" if d == 2 else "Short" if d == 4 else "—"
        color = "#3fb950" if d == 2 else "#f85149"
        rows += f"""
        <tr>
          <td><span style="color:{color};font-weight:600">{label}</span> <span class="tag">{o.get('n','')}</span></td>
          <td>{usd(o.get('p',0), 0)}</td>
          <td>{o.get('a',0):.4f} BTC</td>
          <td class="ts">{fmt_ts(o.get('ot'))}</td>
        </tr>"""
    return f"""
    <table class="data-table">
      <thead><tr><th>Side / Name</th><th>Price</th><th>Amount</th><th>Opened</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""

def positions_html(pos_list, sp):
    if not pos_list:
        return '<div class="no-data">No open positions</div>'
    out = ""
    for pos in pos_list:
        d = pos.get("d", 0)
        label, color = direction_label(d)
        ap = pos.get("ap", 0)
        size = pos.get("t", 0)
        up = pos.get("up", 0)
        roi = pos.get("roi", 0)
        entries = pos.get("eno", [])
        num_entries = len(entries)
        pnl_color = pct_color(up)
        out += f"""
        <div class="position-card">
          <div class="pos-header">
            <span class="pos-dir" style="color:{color}">{label}</span>
            <span class="pos-pnl" style="color:{pnl_color}">{usd(up)} &nbsp; ({pct(roi)})</span>
          </div>
          <div class="pos-grid">
            <div class="pos-stat"><div class="ps-label">Size</div><div class="ps-val">{size:.4f} BTC</div></div>
            <div class="pos-stat"><div class="ps-label">Avg Entry</div><div class="ps-val">{usd(ap, 0)}</div></div>
            <div class="pos-stat"><div class="ps-label">Current Price</div><div class="ps-val">{usd(sp, 0)}</div></div>
            <div class="pos-stat"><div class="ps-label">Entries</div><div class="ps-val">{num_entries} orders</div></div>
            <div class="pos-stat"><div class="ps-label">Opened</div><div class="ps-val">{fmt_ts(pos.get('ot'))}</div></div>
            <div class="pos-stat"><div class="ps-label">Fees Paid</div><div class="ps-val">{usd(pos.get('fe'))}</div></div>
          </div>
        </div>"""
    return out

def finished_positions_html(fin_list):
    if not fin_list:
        return '<div class="no-data">No recent closed positions</div>'
    rows = ""
    for pos in fin_list[-10:]:
        d = pos.get("d", 0)
        label = "Long" if d == 0 else "Short"
        color = "#3fb950" if d == 0 else "#f85149"
        rp = pos.get("rp", 0)
        rp_color = pct_color(rp)
        rows += f"""
        <tr>
          <td><span style="color:{color}">{label}</span></td>
          <td>{usd(pos.get('ap',0), 0)}</td>
          <td>{pos.get('t', pos.get('av', 0)):.4f} BTC</td>
          <td style="color:{rp_color};font-weight:600">{usd(rp)}</td>
          <td>{pct(pos.get('roi',0))}</td>
          <td class="ts">{fmt_ts(pos.get('ct'))}</td>
        </tr>"""
    return f"""
    <table class="data-table">
      <thead><tr><th>Side</th><th>Entry</th><th>Size</th><th>P&L</th><th>ROI</th><th>Closed</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""

CSS = """
:root {
  --bg: #0d1117; --surface: #161b22; --surface2: #1c2128;
  --border: #30363d; --green: #3fb950; --red: #f85149;
  --blue: #58a6ff; --text: #e6edf3; --text2: #8b949e; --text3: #484f58;
  --orange: #f0883e;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; }
a { color: var(--blue); text-decoration: none; }
a:hover { text-decoration: underline; }

/* NAV */
.nav { background: var(--surface); border-bottom: 1px solid var(--border);
  padding: 0 1.5rem; display: flex; align-items: center; gap: 1rem; height: 52px; }
.nav-brand { font-weight: 700; font-size: 1rem; color: var(--text); }
.nav-sub { font-size: 12px; color: var(--text2); margin-top: 1px; }
.nav-links { margin-left: auto; display: flex; gap: 1rem; font-size: 13px; }

/* PAGE */
.page { max-width: 960px; margin: 0 auto; padding: 2rem 1rem 5rem; }
h2 { font-size: 1.4rem; font-weight: 700; margin-bottom: 1.5rem; color: var(--text); }
h3 { font-size: 1rem; font-weight: 600; color: var(--text2); text-transform: uppercase;
  letter-spacing: .06em; margin-bottom: 1rem; margin-top: 2rem; }

/* BOT CARD (index) */
.bot-list { display: grid; gap: 1rem; }
.bot-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 1.25rem 1.5rem; display: flex; justify-content: space-between; align-items: center;
  transition: border-color .15s; }
.bot-card:hover { border-color: var(--blue); }
.bot-name { font-weight: 600; font-size: 1rem; color: var(--text); margin-bottom: 4px; }
.bot-market { font-size: 12px; color: var(--text2); font-family: monospace; }
.bot-stats { display: flex; gap: 2rem; align-items: center; }
.bs-item { text-align: right; }
.bs-label { font-size: 11px; color: var(--text3); text-transform: uppercase; letter-spacing: .05em; }
.bs-val { font-size: 1.1rem; font-weight: 600; margin-top: 2px; }
.btn-view { background: var(--blue); color: #fff; border: none; border-radius: 8px;
  padding: 8px 18px; font-size: 13px; font-weight: 600; cursor: pointer; white-space: nowrap; }

/* METRICS GRID */
.metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem; margin-bottom: 1.5rem; }
@media(max-width:640px) { .metrics { grid-template-columns: repeat(2, 1fr); } }
.metric { background: var(--surface2); border-radius: 10px; padding: .9rem 1rem; }
.m-label { font-size: 11px; color: var(--text3); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 4px; }
.m-val { font-size: 1.25rem; font-weight: 600; }
.m-sub { font-size: 11px; color: var(--text3); margin-top: 3px; }

/* SECTION CARD */
.section { background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 1.25rem 1.5rem; margin-bottom: 1rem; }
.section-title { font-size: 13px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .06em; color: var(--text2); margin-bottom: 1rem; }
.divider { height: 1px; background: var(--border); margin: 1rem 0; }

/* SPARKLINE */
.spark-row { display: flex; gap: 2.5rem; flex-wrap: wrap; }
.spark-item .sp-label { font-size: 11px; color: var(--text3); margin-bottom: 3px; }
.spark-item .sp-val { font-family: monospace; font-size: 1.1rem; color: var(--green); letter-spacing: 2px; }

/* POSITION */
.position-card { background: var(--surface2); border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: .75rem; }
.pos-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: .75rem; }
.pos-dir { font-size: 1rem; font-weight: 700; }
.pos-pnl { font-size: 1rem; font-weight: 700; }
.pos-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .5rem; }
@media(max-width:540px) { .pos-grid { grid-template-columns: repeat(2, 1fr); } }
.ps-label { font-size: 11px; color: var(--text3); margin-bottom: 2px; }
.ps-val { font-size: .9rem; font-weight: 500; }

/* TABLE */
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; color: var(--text3); font-size: 11px; text-transform: uppercase;
  letter-spacing: .05em; padding: 6px 10px 8px; border-bottom: 1px solid var(--border); }
.data-table td { padding: 8px 10px; border-bottom: 1px solid #21262d; color: var(--text); }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--surface2); }
.tag { background: var(--surface); border: 1px solid var(--border); border-radius: 4px;
  font-size: 11px; padding: 1px 6px; color: var(--text2); font-family: monospace; }
.ts { color: var(--text3); font-size: 12px; }
.no-data { color: var(--text3); font-size: 13px; padding: .5rem 0; }

/* STATUS */
.status-row { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.pill { font-size: 12px; padding: 3px 10px; border-radius: 20px; border: 1px solid; font-weight: 500; }
.pill-green { background: #1a3726; border-color: var(--green); color: var(--green); }
.pill-gray  { background: #21262d; border-color: var(--border); color: var(--text2); }
.pill-red   { background: #3d1515; border-color: var(--red); color: var(--red); }
.updated { font-size: 12px; color: var(--text3); margin-left: auto; }

/* BOT DETAIL HEADER */
.bot-header { margin-bottom: 2rem; }
.bot-header .bh-name { font-size: 1.5rem; font-weight: 700; margin-bottom: .25rem; }
.bot-header .bh-meta { font-size: 13px; color: var(--text2); }

.footer { text-align: center; color: var(--text3); font-size: 12px; margin-top: 3rem; }
"""

def bot_detail_html(bot_id, data, now_str):
    runtime = data.get("Reports", {})
    rep = next(iter(runtime.values()), {}) if runtime else {}
    pr  = rep.get("PR", {})
    p   = rep.get("P",  {})
    t   = rep.get("T",  {})
    o   = rep.get("O",  {})
    f   = rep.get("F",  {})

    bot_name  = data.get("BotName", bot_id)
    market    = data.get("PriceMarket", rep.get("M", "—"))
    activated = data.get("Activated", False)
    paused    = data.get("Paused", False)
    sp        = pr.get("SP", 0)
    rp        = pr.get("RP", 0)
    roi       = pr.get("ROI", 0)
    up        = pr.get("UP", 0)
    monthly   = pr.get("RM", 0)
    gp        = pr.get("GP", 0)
    wt        = p.get("W", 0)
    ct        = p.get("C", 1)
    win_pct   = wt / ct * 100 if ct else 0

    status_pill = ('<span class="pill pill-green">● Active</span>' if activated and not paused
                   else '<span class="pill pill-red">⏸ Paused</span>' if paused
                   else '<span class="pill pill-gray">○ Inactive</span>')

    open_pos   = data.get("UnmanagedPositions", [])
    fin_pos    = data.get("FinishedPositions", [])
    open_ords  = data.get("OpenOrders", [])

    custom     = data.get("CustomReport", {})
    custom_html = ""
    for section, fields in custom.items():
        rows = ""
        for k, v in fields.items():
            rows += f'<div class="pos-stat"><div class="ps-label">{k}</div><div class="ps-val">{v}</div></div>'
        custom_html += f'<div class="section"><div class="section-title">{section}</div><div class="pos-grid">{rows}</div></div>'

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{bot_name} — HaasBot Report</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head><body>
<nav class="nav">
  <div>
    <div class="nav-brand">📊 HaasBot Reports</div>
    <div class="nav-sub">Auto-updated every 2 minutes</div>
  </div>
  <div class="nav-links">
    <a href="index.html">← All Bots</a>
  </div>
</nav>
<div class="page">

  <div class="bot-header">
    <div class="bh-name">{bot_name}</div>
    <div class="bh-meta">Market: <strong>{market}</strong> &nbsp;·&nbsp; Bot ID: <code style="font-size:11px;color:var(--text2)">{bot_id}</code></div>
  </div>

  <div class="status-row">
    {status_pill}
    <span class="pill pill-gray">Script: {data.get('ScriptName','—')}</span>
    <span class="pill pill-gray">Leverage: {data.get('Leverage', rep.get('O',{{}}).get('BW','—'))}x</span>
    <span class="updated">Updated: {now_str}</span>
  </div>

  <!-- Performance metrics -->
  <div class="metrics">
    <div class="metric">
      <div class="m-label">Realized Profit</div>
      <div class="m-val" style="color:{pct_color(rp)}">{usd(rp)}</div>
    </div>
    <div class="metric">
      <div class="m-label">ROI</div>
      <div class="m-val" style="color:{pct_color(roi)}">{pct(roi)}</div>
    </div>
    <div class="metric">
      <div class="m-label">Unrealized P&L</div>
      <div class="m-val" style="color:{pct_color(up)}">{usd(up)}</div>
    </div>
    <div class="metric">
      <div class="m-label">Avg Monthly</div>
      <div class="m-val">{usd(monthly)}</div>
    </div>
    <div class="metric">
      <div class="m-label">Gross Profit</div>
      <div class="m-val">{usd(gp)}</div>
    </div>
    <div class="metric">
      <div class="m-label">Fees Paid</div>
      <div class="m-val">{usd(f.get('TFC',0))}</div>
    </div>
    <div class="metric">
      <div class="m-label">Win Rate</div>
      <div class="m-val">{win_pct:.1f}%</div>
      <div class="m-sub">{wt} / {ct} trades</div>
    </div>
    <div class="metric">
      <div class="m-label">Current Price</div>
      <div class="m-val">{usd(sp, 0)}</div>
    </div>
  </div>

  <!-- Sparklines -->
  <div class="section">
    <div class="section-title">Trend</div>
    <div class="spark-row">
      <div class="spark-item">
        <div class="sp-label">ROI trend</div>
        <div class="sp-val">{spark(pr.get('ROIH',[]))}</div>
      </div>
      <div class="spark-item">
        <div class="sp-label">Profit trend</div>
        <div class="sp-val">{spark(pr.get('RPH',[]))}</div>
      </div>
    </div>
  </div>

  <!-- Trade stats -->
  <div class="section">
    <div class="section-title">Trade Statistics</div>
    <div class="pos-grid">
      <div class="pos-stat"><div class="ps-label">Closed Trades</div><div class="ps-val">{o.get('C',0):,}</div></div>
      <div class="pos-stat"><div class="ps-label">Best Trade</div><div class="ps-val" style="color:var(--green)">{usd(p.get('BW',0))}</div></div>
      <div class="pos-stat"><div class="ps-label">Avg Profit/Trade</div><div class="ps-val">{usd(p.get('AP',0))}</div></div>
      <div class="pos-stat"><div class="ps-label">Profit Factor</div><div class="ps-val">{"∞" if t.get('PF',0) >= 999 else f"{t.get('PF',0):.2f}"}</div></div>
      <div class="pos-stat"><div class="ps-label">Peak Profit</div><div class="ps-val">{usd(t.get('HP',0))}</div></div>
      <div class="pos-stat"><div class="ps-label">Lowest Profit</div><div class="ps-val">{usd(t.get('LP',0))}</div></div>
      <div class="pos-stat"><div class="ps-label">Runtime</div><div class="ps-val">{t.get('TM',0):.0f}h</div></div>
      <div class="pos-stat"><div class="ps-label">Orders Issued</div><div class="ps-val">{o.get('A',0):,}</div></div>
      <div class="pos-stat"><div class="ps-label">Buy %</div><div class="ps-val">{o.get('BW',0):.1f}%</div></div>
    </div>
  </div>

  <!-- Open Positions -->
  <h3>📍 Open Positions ({len(open_pos)})</h3>
  <div class="section">
    {positions_html(open_pos, sp)}
  </div>

  <!-- Open Orders -->
  <h3>📋 Open Orders ({len(open_ords)})</h3>
  <div class="section">
    {open_orders_html(open_ords)}
  </div>

  <!-- Closed Positions -->
  <h3>✅ Last 10 Closed Positions</h3>
  <div class="section">
    {finished_positions_html(fin_pos)}
  </div>

  <!-- Custom Report -->
  {custom_html}

</div>
<div class="footer">Last build: {now_str} · HaasBot + GitHub Pages</div>
</body></html>"""

def index_html(bots_data, now_str):
    cards = ""
    for bot_id, info in bots_data.items():
        data   = info["data"]
        rep    = info["rep"]
        pr     = rep.get("PR", {})
        p      = rep.get("P",  {})
        rp     = pr.get("RP", 0)
        roi    = pr.get("ROI", 0)
        wt     = p.get("W", 0)
        ct     = p.get("C", 1)
        win    = wt / ct * 100 if ct else 0
        name   = data.get("BotName", bot_id)
        market = data.get("PriceMarket", "—")
        active = data.get("Activated", False)
        dot    = "🟢" if active else "⚫"
        cards += f"""
        <a href="bot_{bot_id}.html" style="display:block;text-decoration:none">
          <div class="bot-card">
            <div>
              <div class="bot-name">{dot} {name}</div>
              <div class="bot-market">{market}</div>
            </div>
            <div class="bot-stats">
              <div class="bs-item">
                <div class="bs-label">Profit</div>
                <div class="bs-val" style="color:{pct_color(rp)}">{usd(rp)}</div>
              </div>
              <div class="bs-item">
                <div class="bs-label">ROI</div>
                <div class="bs-val" style="color:{pct_color(roi)}">{pct(roi)}</div>
              </div>
              <div class="bs-item">
                <div class="bs-label">Win Rate</div>
                <div class="bs-val">{win:.0f}%</div>
              </div>
              <div class="btn-view">View →</div>
            </div>
          </div>
        </a>"""

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HaasBot Live Reports</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head><body>
<nav class="nav">
  <div>
    <div class="nav-brand">📊 HaasBot Reports</div>
    <div class="nav-sub">Auto-updated every 2 minutes</div>
  </div>
  <div class="nav-links">
    <span style="color:var(--text2);font-size:12px">{now_str}</span>
  </div>
</nav>
<div class="page">
  <h2>All Bots ({len(bots_data)})</h2>
  <div class="bot-list">{cards}</div>
</div>
<div class="footer">Last build: {now_str} · HaasBot + GitHub Pages</div>
</body></html>"""

# ── Main ──────────────────────────────────────────────────────────────────────
now_str   = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
bots_data = {}

for bot_id in BOT_IDS:
    print(f"  Fetching {bot_id} ...")
    raw = fetch_runtime(bot_id)
    if not raw or not raw.get("Success"):
        print(f"  ✗ Failed: {raw}")
        continue
    data = raw.get("Data", {})
    reports = data.get("Reports", {})
    rep = next(iter(reports.values()), {}) if reports else {}
    bots_data[bot_id] = {"data": data, "rep": rep}

    # Write per-bot page
    html = bot_detail_html(bot_id, data, now_str)
    fname = f"bot_{bot_id}.html"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ {fname}")

# Write index
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html(bots_data, now_str))

print(f"✅ Done — {len(bots_data)} bot(s), index.html + {len(bots_data)} detail pages")
