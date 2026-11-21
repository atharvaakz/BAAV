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
        fu = (ROOT / "assets/fonts/plex").as_uri()
        faces = []
        for fam, files in [("Plex Serif", [("IBMPlexSerif-Regular", 400, "normal"), ("IBMPlexSerif-Italic", 400, "italic"), ("IBMPlexSerif-Medium", 500, "normal"), ("IBMPlexSerif-SemiBold", 600, "normal")]),
                           ("Plex Sans", [("IBMPlexSans-Regular", 400, "normal"), ("IBMPlexSans-Italic", 400, "italic"), ("IBMPlexSans-Medium", 500, "normal"), ("IBMPlexSans-SemiBold", 600, "normal"), ("IBMPlexSans-Bold", 700, "normal")]),
                           ("Plex Mono", [("IBMPlexMono-Regular", 400, "normal"), ("IBMPlexMono-Medium", 500, "normal"), ("IBMPlexMono-SemiBold", 600, "normal")])]:
            for f, w, st in files:
                faces.append(f"@font-face{{font-family:'{fam}';src:url('{fu}/{f}.ttf') format('truetype');font-weight:{w};font-style:{st}}}")
        css = "\n".join(faces)
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
    t1, t2 = (title.split(" ", 2)[0] + " " + title.split(" ", 2)[1], title.split(" ", 2)[2]) if title.count(" ") >= 2 else (title, "")
    doc.add(f"""<section class="cover">
<div class="cmeta"><span>ECON F355 / Business Analysis &amp; Valuation</span><span>Sector report / 31 October 2026</span></div>
<div class="csq"></div>
<div class="ctitle1">{esc(t1)}<br>{esc(t2)}</div>
<div class="csub">{esc(subtitle)}</div>
<div class="cgrid">
  <div class="clab">At a glance</div>
  <table class="t ctab"><colgroup><col style="width:28%"><col style="width:24%"><col style="width:24%"><col style="width:24%"></colgroup><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>
</div>
<div class="cfoot">
  <div><div class="clab">Authors</div><div class="cauth">{esc(authors.replace("Group 27 · ", ""))}</div><div class="csubm">Group 27</div></div>
  <div><div class="clab">Submitted to</div><div class="csubm">{esc(submitted.replace("Submitted to ", ""))}</div></div>
  <div class="cnote">{esc(note)}</div>
</div>
</section>""")


def references(refs):
    doc.add('<ol class="refs">' + "".join(f"<li>{esc(r)}</li>" for r in refs) + "</ol>")


CSS = r"""
:root{--ink:#111418;--sig:#D9481C;--navy:#1F3A5F;--mute:#6E737A;--rule:#D6D8DB;--hair:#E6E7E9;--paper:#F4F5F6}
@page{size:A4;margin:21mm 17mm 17mm 17mm;
  @top-left{content:"Paying for the Future";font:500 7.2pt "Plex Mono";color:#111418;vertical-align:bottom;padding-bottom:3mm}
  @top-right{content:"Indian Real Estate / Group 27";font:400 7.2pt "Plex Mono";color:#6E737A;vertical-align:bottom;padding-bottom:3mm}
  @bottom-left{content:"DLF · Godrej Properties · Phoenix Mills";font:400 6.8pt "Plex Sans";color:#8b9096}
  @bottom-right{content:counter(page);font-family:"Plex Mono",monospace;font-size:8pt;font-weight:500;color:#D9481C}}
@page cover{margin:0;@top-left{content:none}@top-right{content:none}@bottom-left{content:none}@bottom-right{content:none}}
html{counter-reset:page -1}
body{margin:0;font-family:"Plex Serif",Georgia,serif;font-size:9.1pt;line-height:1.4;color:var(--ink);hyphens:auto;-webkit-hyphens:auto;font-variant-numeric:lining-nums}
p{margin:0 0 5.5pt;text-align:justify;orphans:3;widows:3}
p.small{font-size:8.5pt;color:#333a40}
p.it{font-style:italic}
.runin{font-family:"Plex Sans",sans-serif;font-weight:600;font-size:9pt;color:var(--ink)}
b,strong{font-weight:600}
h1{font-family:"Plex Sans",sans-serif;font-weight:500;font-size:15pt;letter-spacing:-.005em;color:var(--ink);margin:16pt 0 3pt;padding-top:6pt;border-top:1.5pt solid var(--ink);break-after:avoid;line-height:1.15}
h1 .num{font-family:"Plex Mono",monospace;font-weight:500;color:var(--sig);font-size:11pt;display:block;margin-bottom:3pt}
h3{font-family:"Plex Sans",sans-serif;font-weight:600;font-size:10pt;color:var(--ink);margin:13pt 0 4pt;break-after:avoid}
h3::before{content:"";display:inline-block;width:6pt;height:6pt;background:var(--sig);margin-right:6pt;vertical-align:1pt}
h4{font-family:"Plex Sans",sans-serif;font-weight:600;font-size:9pt;margin:9pt 0 3pt;break-after:avoid}
.tag{font-family:"Plex Mono",monospace;font-size:7pt;color:var(--mute);margin:0 0 8pt;break-after:avoid}
.bridge{font-family:"Plex Sans",sans-serif;font-size:8.8pt;line-height:1.45;color:#2b3137;margin:0 0 10pt;padding:5pt 0 6pt;border-top:.5pt solid var(--rule);border-bottom:.5pt solid var(--rule);text-align:left;break-after:avoid}
.bridge::before{content:"Approach — ";font-family:"Plex Mono",monospace;font-size:7.5pt;color:var(--sig)}
ul{margin:2pt 0 8pt;padding-left:12pt;list-style:none}
ul li{margin:0 0 4pt;text-align:justify;position:relative}
ul li::before{content:"";position:absolute;left:-11pt;top:5pt;width:5pt;height:1.2pt;background:var(--ink)}
.tbl{margin:7pt 0 11pt;break-inside:avoid}
.tbl.long{break-inside:auto}
table.t thead{display:table-header-group}
table.t tr{break-inside:avoid}
table.t{width:100%;border-collapse:collapse;font-family:"Plex Sans",sans-serif;font-size:7.6pt;line-height:1.32;font-variant-numeric:tabular-nums lining-nums;border-top:1.5pt solid var(--ink);border-bottom:.8pt solid var(--ink)}
table.t.sm{font-size:7.1pt}
table.t th{font-family:"Plex Mono",monospace;font-weight:500;font-size:6.8pt;color:var(--mute);text-align:left;padding:4pt 5pt 4pt;border-bottom:.5pt solid var(--ink);vertical-align:bottom}
table.t th.n{text-align:right}
table.t td{padding:3pt 5pt;border-bottom:.3pt solid var(--hair);vertical-align:top;text-align:left}
table.t td:first-child{font-weight:500}
table.t td.n{text-align:right;white-space:nowrap}
table.t tbody tr:last-child td{border-bottom:none}
.tnote{font-family:"Plex Sans",sans-serif;font-size:6.8pt;color:var(--mute);margin-top:3pt;line-height:1.35}
figure{margin:7pt 0 9pt;break-inside:avoid}
figure img{display:block;margin:0 auto 5pt}
figcaption{font-family:"Plex Sans",sans-serif;font-size:7.2pt;color:#3b4248;text-align:left;line-height:1.38}
figcaption b{font-family:"Plex Mono",monospace;font-weight:500;color:var(--sig)}
.callout{border-top:1.5pt solid var(--ink);border-bottom:.5pt solid var(--ink);padding:7pt 0 3pt;margin:9pt 0 13pt;break-inside:avoid}
.callout .ctitle{font-family:"Plex Mono",monospace;font-weight:500;font-size:7.5pt;color:var(--sig);margin-bottom:5pt}
.callout p{font-family:"Plex Sans",sans-serif;font-size:9pt;margin:0 0 4pt;text-align:left}
ol.refs{font-family:"Plex Sans",sans-serif;font-size:7.6pt;line-height:1.4;padding-left:18pt;color:#2b3137}
ol.refs li{margin-bottom:3pt}
ol.refs li::marker{font-family:"Plex Mono",monospace;color:var(--sig)}
.pb{break-after:page}
/* ---------- title page: Swiss grid ---------- */
section.cover{page:cover;position:relative;height:297mm;width:210mm;box-sizing:border-box;break-after:page;overflow:hidden;font-family:"Plex Sans",sans-serif}
.cmeta{position:absolute;left:20mm;right:20mm;top:16mm;display:flex;justify-content:space-between;font-family:"Plex Mono",monospace;font-size:7.6pt;color:var(--ink);border-bottom:1.2pt solid var(--ink);padding-bottom:3mm}
.csq{position:absolute;left:20mm;top:52mm;width:11mm;height:11mm;background:var(--sig)}
.ctitle1{position:absolute;left:20mm;right:20mm;top:70mm;font-family:"Plex Sans",sans-serif;font-weight:500;font-size:60pt;line-height:.98;letter-spacing:-.025em;color:var(--ink)}
.csub{position:absolute;left:20mm;width:125mm;top:128mm;font-family:"Plex Serif",serif;font-size:14.5pt;line-height:1.35;color:var(--ink)}
.cgrid{position:absolute;left:20mm;right:20mm;top:160mm}
.clab{font-family:"Plex Mono",monospace;font-size:7.2pt;color:var(--sig);margin-bottom:2.5mm}
table.ctab{font-size:7.8pt}
table.ctab td{padding:3.6pt 5pt}
.cfoot{position:absolute;left:20mm;right:20mm;bottom:16mm;border-top:.6pt solid var(--ink);padding-top:4mm;display:grid;grid-template-columns:1fr 1fr 1.6fr;gap:7mm}
.cauth{font-size:9pt;font-weight:600;color:var(--ink);margin-bottom:1mm}
.csubm{font-size:8pt;color:#2b3137;line-height:1.4}
.cnote{font-size:6.8pt;color:var(--mute);line-height:1.45;padding-top:4.5mm}
"""
