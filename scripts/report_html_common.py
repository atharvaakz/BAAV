"""HTML/CSS back end for the report: same helper API as report_common.py (docx), rendered to PDF by Chromium.

Design: formal, minimalist equity-research layout — full-bleed title page, Source Serif 4 body, Inter for headings,
labels and tables, booktabs-style rules, running header/footer, one accent colour.
"""
import json, pathlib, re, html as _h, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
N = json.loads((ROOT / "data/processed/numbers.json").read_text())
CH = ROOT / "reports/charts"
OUTDIR = ROOT / "reports/report_html"
OUT = ROOT / "reports/ProjectBaav_Group27_Report.pdf"
D, G, P = N["DLF"], N["GPL"], N["PML"]
I = N["Inputs"]


def pc(x, d=1):
    return f"{x*100:.{d}f}%"


def cr(x):
    return f"−₹{abs(x):,.0f} cr" if x < 0 else f"₹{x:,.0f} cr"


def rs(x):
    return f"₹{x:,.0f}"


def xx(x, d=1):
    return f"{x:.{d}f}x"


def esc(s):
    return _h.escape(str(s), quote=False)


class _Doc:
    def __init__(self):
        self.parts = []
        self.title_text = "Report"

    def add(self, s):
        self.parts.append(s)

    def add_heading(self, text, level=1):
        text = str(text)
        if level == 1:
            m = re.match(r"^(\d+)\.\s+(.*)$", text) or re.match(r"^(Appendix [A-Z])\s+—\s+(.*)$", text)
            if m:
                self.add(f'<h1><span class="num">{esc(m.group(1))}</span>{esc(m.group(2))}</h1>')
            else:
                self.add(f'<h1 class="plain">{esc(text)}</h1>')
        else:
            self.add(f"<h{min(level + 1, 4)}>{esc(text)}</h{min(level + 1, 4)}>")

    def add_page_break(self):
        self.add('<div class="pb"></div>')

    def save(self, _path=None):
        OUTDIR.mkdir(parents=True, exist_ok=True)
        fu = (ROOT / "assets/fonts").as_uri()
        css = (ROOT / "assets/fonts/source-serif-4.css").read_text().replace("url(ss4_", f"url({fu}/ss4_") + \
              (ROOT / "assets/fonts/inter.css").read_text().replace("url(inter_", f"url({fu}/inter_")
        page = f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>Paying for the Future</title>
<style>{css}\n{CSS}</style></head><body>{''.join(self.parts)}</body></html>"""
        hp = OUTDIR / "ProjectBaav_Group27_Report.html"
        hp.write_text(page)
        js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage();
await p.goto('{hp.as_uri()}',{{waitUntil:'networkidle'}});await p.evaluate(()=>document.fonts.ready);
await p.pdf({{path:'{OUT}',preferCSSPageSize:true,printBackground:true}});await b.close();}})();"""
        subprocess.run(["node", "-e", js], check=True)
        print("saved", OUT)


doc = _Doc()


def para(text, bold_lead=None, italic=False, size=None, after=None):
    cls = []
    if italic:
        cls.append("it")
    if size and size <= 9:
        cls.append("small")
    lead = f"<b>{esc(bold_lead)}</b> " if bold_lead else ""
    t = esc(text)
    # bold run-in heads such as "DLF. ..." or "Risk-free rate. ..." at the start of a paragraph
    m = re.match(r"^([A-Z][A-Za-z' \-/&()]{1,40}\.)\s", t)
    if m and not bold_lead and len(m.group(1)) < 40 and len(m.group(1).split()) <= 4 and not set(m.group(1).lower().rstrip('.').split()) & {'was','is','are','were','has','had','have','fell','rose'} and not re.match(r"^(The|We|Our|In|At|On|For|It|This|With|All|A|An|Its|As)\b", m.group(1)):
        t = f'<span class="runin">{m.group(1)}</span>' + t[len(m.group(1)):]
    doc.add(f'<p class="{" ".join(cls)}">{lead}{t}</p>')


def bullets(items):
    li = []
    for t in items:
        if isinstance(t, tuple):
            li.append(f"<li><b>{esc(t[0])}</b> {esc(t[1])}</li>")
        else:
            li.append(f"<li>{esc(t)}</li>")
    doc.add(f"<ul>{''.join(li)}</ul>")


def module_tag(text):
    doc.add(f'<div class="tag">{esc(text)}</div>')


def bridge(text):
    doc.add(f'<p class="bridge">{esc(text)}</p>')


_NUM = re.compile(r"^[\s₹+\-−(]*[\d.,]")


def _colnum(rows_, ncol):
    out = []
    for j in range(ncol):
        vals = [str(r[j]) for r in rows_ if j < len(r) and str(r[j]).strip() not in ("", "—")]
        k = sum(1 for v in vals if len(v) < 24 and _NUM.match(v))
        out.append(j > 0 and vals and k / len(vals) >= 0.6)
    return out


def table(headers, rows_, widths=None, note=None, size=8.5):
    tot = sum(widths) if widths else None
    cg = "".join(f'<col style="width:{w / tot * 100:.1f}%">' for w in widths) if widths else ""
    isn = _colnum(rows_, len(headers))
    th = "".join(f'<th class="{"n" if isn[i] else ""}">{esc(h)}</th>' for i, h in enumerate(headers))
    body = []
    for row in rows_:
        tds = "".join(f'<td class="{"n" if isn[i] else ""}">{esc(v)}</td>' for i, v in enumerate(row))
        body.append(f"<tr>{tds}</tr>")
    small = " sm" if size and size < 8.5 else ""
    nt = f'<div class="tnote">{esc(note)}</div>' if note else ""
    longc = " long" if len(rows_) > 10 else ""
    doc.add(f'<div class="tbl{longc}"><table class="t{small}"><colgroup>{cg}</colgroup><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table>{nt}</div>')


def fig(name, caption, width=16.5):
    m = re.match(r"^(Figure \d+)\s+—\s+(.*)$", caption)
    cap = f"<b>{esc(m.group(1))}.</b> {esc(m.group(2))}" if m else esc(caption)
    w = min(100, width / 16.6 * 100)
    doc.add(f'<figure><img src="{(CH / (name + ".png")).as_uri()}" style="width:{w:.0f}%"><figcaption>{cap}</figcaption></figure>')


def callout(title, lines, fill=None):
    items = "".join(f"<p>{esc(l)}</p>" for l in lines)
    doc.add(f'<div class="callout"><div class="ctitle">{esc(title)}</div>{items}</div>')


def cover(title, subtitle, kicker, headers, rows, authors, submitted, note):
    th = "".join(f'<th class="{"n" if i else ""}">{esc(h)}</th>' for i, h in enumerate(headers))
    tr = "".join("<tr>" + "".join(f'<td class="{"n" if i else ""}">{esc(v)}</td>' for i, v in enumerate(r)) + "</tr>" for r in rows)
    doc.add(f"""<section class="cover">
<div class="cbar"></div>
<div class="ctop"><span>ECON F355 · Business Analysis &amp; Valuation</span><span>Sector report · November 2026</span></div>
<div class="cmain">
  <div class="ckicker">DLF · Godrej Properties · Phoenix Mills</div>
  <div class="ctitle1">{esc(title)}</div>
  <div class="csub">{esc(subtitle)}</div>
  <div class="crule"></div>
  <table class="t ctab"><colgroup><col style="width:25%"><col style="width:25%"><col style="width:25%"><col style="width:25%"></colgroup><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>
</div>
<div class="cfoot">
  <div class="cauth">{esc(authors)}</div>
  <div class="csubm">{esc(submitted)}</div>
  <div class="cnote">{esc(note)}</div>
</div>
</section>""")


def references(refs):
    doc.add('<ol class="refs">' + "".join(f"<li>{esc(r)}</li>" for r in refs) + "</ol>")


CSS = r"""
:root{--ink:#1d262c;--acc:#24545a;--acc2:#3d7177;--mute:#6b767d;--rule:#c9cfd2;--hair:#e4e7e8;--tint:#f2f5f4}
@page{size:A4;margin:24mm 21mm 20mm 21mm;
  @top-left{content:"Paying for the Future";font:600 7pt InterW;color:#6b767d;letter-spacing:.08em;text-transform:uppercase;vertical-align:bottom;padding-bottom:3mm}
  @top-right{content:"ECON F355 · Group 27";font:500 7pt InterW;color:#6b767d;letter-spacing:.06em;vertical-align:bottom;padding-bottom:3mm}
  @bottom-left{content:"Indian Real Estate · DLF · Godrej Properties · Phoenix Mills";font:400 6.8pt InterW;color:#8a949a}
  @bottom-right{content:counter(page);font:600 7.5pt InterW;color:#1d262c}}
@page cover{margin:0;@top-left{content:none;border:none}@top-right{content:none;border:none}@bottom-left{content:none}@bottom-right{content:none}}
html{counter-reset:page -1}
body{margin:0;font-family:"Source Serif 4",Georgia,serif;font-size:9.8pt;line-height:1.45;color:var(--ink);font-optical-sizing:auto;
  text-rendering:optimizeLegibility;font-variant-numeric:lining-nums proportional-nums;hyphens:auto;-webkit-hyphens:auto}
p{margin:0 0 6pt;text-align:justify;orphans:3;widows:3}
p.small{font-size:8.6pt;color:#3c474e}
p.it{font-style:italic}
.runin{font-family:InterW,sans-serif;font-weight:600;font-size:8.6pt;letter-spacing:.01em;color:var(--acc)}
b,strong{font-weight:600}
h1{font-family:InterW,sans-serif;font-weight:600;font-size:14.5pt;letter-spacing:-.01em;color:var(--ink);margin:20pt 0 3pt;padding-top:7pt;
  border-top:1.1pt solid var(--ink);break-after:avoid;page-break-after:avoid;line-height:1.2}
h1 .num{color:var(--acc);margin-right:9pt;font-weight:700}
h1.plain{font-size:14.5pt}
h3{font-family:InterW,sans-serif;font-weight:600;font-size:10pt;color:var(--acc);margin:12pt 0 4pt;break-after:avoid;page-break-after:avoid}
h4{font-family:InterW,sans-serif;font-weight:600;font-size:9pt;margin:9pt 0 3pt;break-after:avoid}
.tag{font-family:InterW,sans-serif;font-size:6.6pt;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--mute);margin:0 0 7pt;break-after:avoid}
.bridge{font-style:italic;font-size:9.3pt;color:#33444a;border-left:2pt solid var(--acc2);padding:1pt 0 1pt 9pt;margin:0 0 9pt;text-align:left;break-after:avoid}
ul{margin:2pt 0 8pt;padding-left:13pt}
ul li{margin:0 0 3.5pt;text-align:justify;padding-left:2pt}
ul li::marker{color:var(--acc);content:"▪  ";font-size:8pt}
.tbl{margin:6pt 0 10pt;break-inside:avoid;page-break-inside:avoid}
.tbl.long{break-inside:auto;page-break-inside:auto}
table.t thead{display:table-header-group}
table.t tr{break-inside:avoid}
table.t{width:100%;border-collapse:collapse;font-family:InterW,sans-serif;font-size:7.7pt;line-height:1.3;font-variant-numeric:tabular-nums lining-nums;
  border-top:1.1pt solid var(--ink);border-bottom:1.1pt solid var(--ink)}
table.t.sm{font-size:7.2pt}
table.t th{font-weight:600;font-size:6.9pt;letter-spacing:.04em;text-transform:uppercase;color:var(--mute);text-align:left;padding:4pt 5pt 3.5pt;border-bottom:.6pt solid var(--ink);vertical-align:bottom}
table.t th.n{text-align:right}
table.t td{letter-spacing:-.006em;padding:3pt 5pt;border-bottom:.35pt solid var(--hair);vertical-align:top;text-align:left}
table.t td:first-child{font-weight:500;color:#26323a}
table.t td.n{text-align:right;white-space:nowrap}
table.t tbody tr:last-child td{border-bottom:none}
.tnote{font-family:InterW,sans-serif;font-size:6.8pt;color:var(--mute);margin-top:3pt;line-height:1.35}
figure{margin:8pt 0 11pt;text-align:center;break-inside:avoid;page-break-inside:avoid}
figure img{display:block;margin:0 auto 4pt}
figcaption{font-family:InterW,sans-serif;font-size:7.2pt;color:var(--mute);text-align:left;line-height:1.35;border-top:.35pt solid var(--hair);padding-top:3pt}
figcaption b{color:var(--ink)}
.callout{background:var(--tint);border-left:2.5pt solid var(--acc);padding:8pt 11pt 4pt;margin:8pt 0 12pt;break-inside:avoid}
.callout .ctitle{font-family:InterW,sans-serif;font-weight:700;font-size:7.4pt;letter-spacing:.12em;text-transform:uppercase;color:var(--acc);margin-bottom:5pt}
.callout p{font-size:9.3pt;margin:0 0 4pt;text-align:left}
ol.refs{font-size:8pt;line-height:1.38;padding-left:16pt;color:#2c373e}
ol.refs li{margin-bottom:3pt}
.pb{break-after:page;page-break-after:always}
/* ---------- title page ---------- */
section.cover{page:cover;position:relative;height:297mm;width:210mm;box-sizing:border-box;padding:0;break-after:page;overflow:hidden}
.cbar{position:absolute;left:0;top:0;bottom:0;width:13mm;background:var(--acc)}
.ctop{position:absolute;left:27mm;right:20mm;top:20mm;display:flex;justify-content:space-between;font-family:InterW,sans-serif;font-size:7pt;font-weight:600;
  letter-spacing:.14em;text-transform:uppercase;color:var(--mute);border-bottom:.5pt solid var(--rule);padding-bottom:4mm}
.cmain{position:absolute;left:27mm;right:20mm;top:68mm}
.ckicker{font-family:InterW,sans-serif;font-size:8pt;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--acc);margin-bottom:7mm}
.ctitle1{font-family:"Source Serif 4",serif;font-weight:600;font-size:48pt;line-height:1.02;letter-spacing:-.015em;color:var(--ink);font-optical-sizing:auto}
.csub{font-family:"Source Serif 4",serif;font-style:italic;font-size:15pt;line-height:1.3;color:#3b4a51;margin-top:6mm;max-width:150mm}
.crule{width:22mm;height:1.6pt;background:var(--acc);margin:14mm 0 9mm}
table.ctab{font-size:8pt}
table.ctab td{padding:4pt 5pt}
.cfoot{position:absolute;left:27mm;right:20mm;bottom:20mm;border-top:.5pt solid var(--rule);padding-top:5mm;font-family:InterW,sans-serif}
.cauth{font-size:9.5pt;font-weight:600;color:var(--ink);margin-bottom:1.5mm}
.csubm{font-size:8.5pt;color:#3b4a51;margin-bottom:4mm}
.cnote{font-size:7pt;color:var(--mute);line-height:1.4;max-width:150mm}
"""
