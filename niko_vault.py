"""
╔══════════════════════════════════════════════════════════════╗
║        NIKO VAULT v2 — Research Management System           ║
║        Run: streamlit run niko_vault.py                     ║
╚══════════════════════════════════════════════════════════════╝

Install dependencies:
    pip install streamlit reportlab

All data saved locally in: niko_vault_data.json
"""

import streamlit as st
import json, uuid, io, base64, calendar
from datetime import datetime, date, timedelta
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                    Spacer, HRFlowable, PageBreak)
    from reportlab.lib.enums import TA_LEFT
    PDF_OK = True
except ImportError:
    PDF_OK = False

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Niko Vault", page_icon="⚗️",
                   layout="wide", initial_sidebar_state="expanded")

# ── Constants ─────────────────────────────────────────────────────────────────
DATA_FILE = Path("niko_vault_data.json")

SECTIONS = {
    "📗 Books":             "books",
    "📝 Notes":             "notes",
    "📄 Research Papers":   "papers",
    "📰 Magazines":         "magazines",
    "💡 Rough Ideas":       "ideas",
    "🧠 Insights":          "insights",
    "🗞 Newspaper":         "newspaper",
    "🔬 Lab Devices":       "labdevices",
    "📖 Novels":            "novels",
    "🗓 Planner":           "planner",
    "⚗️ Molecule Viewer":   "molecule",
}

SEC_COLOR = {
    "books":"#16a34a","notes":"#2563eb","papers":"#7c3aed",
    "magazines":"#db2777","ideas":"#d97706","insights":"#0891b2",
    "newspaper":"#64748b","labdevices":"#059669","novels":"#9333ea",
}
BRANCHES   = ["General","Physical","Inorganic","Organic","Analytical"]
HAS_AUTHOR = {"books","papers","magazines","novels"}
HAS_LINK   = {"papers","magazines","newspaper","labdevices"}
HAS_DEVICE = {"labdevices"}
MONTHS     = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]

MOLECULES = {
    "Water (H2O)":          "O",
    "Ethanol (C2H5OH)":     "CCO",
    "Glucose (C6H12O6)":    "C(C1C(C(C(C(O1)O)O)O)O)O",
    "Benzene (C6H6)":       "c1ccccc1",
    "Acetone":              "CC(=O)C",
    "Caffeine":             "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "Aspirin":              "CC(=O)Oc1ccccc1C(=O)O",
    "Methane (CH4)":        "C",
    "Carbon Dioxide (CO2)": "O=C=O",
    "Ammonia (NH3)":        "N",
    "Penicillin G":         "CC1(C(N2C(S1)C(C2=O)NC(=O)Cc3ccccc3)C(=O)O)C",
}

MOL_INFO = {
    "Water (H2O)":          {"formula":"H₂O",        "mw":"18.02 g/mol", "type":"Inorganic"},
    "Ethanol (C2H5OH)":     {"formula":"C₂H₅OH",     "mw":"46.07 g/mol", "type":"Organic"},
    "Glucose (C6H12O6)":    {"formula":"C₆H₁₂O₆",   "mw":"180.16 g/mol","type":"Organic"},
    "Benzene (C6H6)":       {"formula":"C₆H₆",        "mw":"78.11 g/mol", "type":"Organic"},
    "Acetone":              {"formula":"C₃H₆O",       "mw":"58.08 g/mol", "type":"Organic"},
    "Caffeine":             {"formula":"C₈H₁₀N₄O₂",  "mw":"194.19 g/mol","type":"Organic"},
    "Aspirin":              {"formula":"C₉H₈O₄",      "mw":"180.16 g/mol","type":"Organic"},
    "Methane (CH4)":        {"formula":"CH₄",          "mw":"16.04 g/mol", "type":"Organic"},
    "Carbon Dioxide (CO2)": {"formula":"CO₂",          "mw":"44.01 g/mol", "type":"Inorganic"},
    "Ammonia (NH3)":        {"formula":"NH₃",          "mw":"17.03 g/mol", "type":"Inorganic"},
    "Penicillin G":         {"formula":"C₁₆H₁₈N₂O₄S","mw":"334.39 g/mol","type":"Organic"},
}

# ── Persistence ───────────────────────────────────────────────────────────────
def load_data():
    if DATA_FILE.exists():
        try: return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except: pass
    return {"entries":{}, "plans":{}}

def save_data(d): DATA_FILE.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding="utf-8")

# ── Session state ─────────────────────────────────────────────────────────────
for k,v in [("data",None),("section","books"),("view","list"),
            ("selected_id",None),("edit_mode",False),("dark_mode",False),
            ("cal_year",date.today().year),("cal_month",date.today().month)]:
    if k not in st.session_state:
        st.session_state[k] = load_data() if k=="data" else v

# ── Theme ─────────────────────────────────────────────────────────────────────
DM = st.session_state.dark_mode
T  = {"bg":"#0a0e17","card":"#0f1623","border":"#1a2744","text":"#e2e8f0",
      "muted":"#64748b","heading":"#f1f5f9"} if DM else \
     {"bg":"#f8f7f4","card":"#ffffff","border":"#f1ede8","text":"#374151",
      "muted":"#94a3b8","heading":"#1e293b"}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;700&family=Lato:wght@400;700&family=JetBrains+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{{font-family:'Lato',sans-serif;background:{T['bg']} !important;color:{T['text']} !important;}}
.stApp{{background:{T['bg']} !important;}}
section[data-testid="stSidebar"]{{background:{T['card']} !important;border-right:1.5px solid {T['border']} !important;}}
.main-title{{font-family:'Cormorant Garamond',serif;font-size:1.9rem;font-weight:700;color:{T['heading']};}}
.sec-title{{font-family:'Cormorant Garamond',serif;font-size:1.3rem;font-weight:700;color:{T['heading']};}}
.entry-card{{background:{T['card']};border:1.5px solid {T['border']};border-radius:12px;padding:1rem 1.2rem;margin-bottom:0.7rem;}}
.entry-title{{font-family:'Cormorant Garamond',serif;font-size:1.05rem;font-weight:700;color:{T['heading']};}}
.entry-meta{{font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:{T['muted']};margin-top:2px;}}
.branch-badge{{font-family:'JetBrains Mono',monospace;font-size:0.57rem;padding:2px 8px;border-radius:20px;font-weight:700;letter-spacing:0.08em;}}
.tag-pill{{display:inline-block;background:{'#0d1220' if DM else '#f8f7f4'};border:1px solid {T['border']};border-radius:20px;padding:1px 8px;font-size:0.62rem;color:{T['muted']};font-family:'JetBrains Mono',monospace;margin-right:4px;}}
.mono-lbl{{font-family:'JetBrains Mono',monospace;font-size:0.6rem;letter-spacing:0.15em;text-transform:uppercase;color:{T['muted']};}}
.stat-card{{background:{T['card']};border:1.5px solid {T['border']};border-radius:10px;padding:0.65rem 0.8rem;text-align:center;}}
</style>""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_entries(s): return st.session_state.data["entries"].get(s,[])
def get_plans():    return st.session_state.data.get("plans",{})
def fmt(iso):
    try: return datetime.fromisoformat(iso).strftime("%d %b %Y · %I:%M %p")
    except: return iso
def total(): return sum(len(v) for v in st.session_state.data["entries"].values())
def go(sec):
    st.session_state.section=sec; st.session_state.view="list"
    st.session_state.selected_id=None; st.session_state.edit_mode=False
def sv(v,eid=None,edit=False):
    st.session_state.view=v; st.session_state.selected_id=eid; st.session_state.edit_mode=edit

# ── PDF builder ───────────────────────────────────────────────────────────────
def make_pdf(entries, label):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf,pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=2*cm,bottomMargin=2*cm)
    sty = getSampleStyleSheet()
    S   = lambda name,**kw: ParagraphStyle(name,**kw)
    tit = S("T",fontName="Helvetica-Bold",fontSize=22,textColor=colors.HexColor("#1e293b"),spaceAfter=4)
    sub = S("S",fontName="Helvetica",fontSize=9,textColor=colors.HexColor("#94a3b8"),spaceAfter=16)
    hd  = S("H",fontName="Helvetica-Bold",fontSize=13,textColor=colors.HexColor("#1e293b"),spaceBefore=14,spaceAfter=3)
    bd  = S("B",fontName="Helvetica",fontSize=9,textColor=colors.HexColor("#374151"),leading=14,spaceAfter=6)
    mt  = S("M",fontName="Helvetica",fontSize=7.5,textColor=colors.HexColor("#94a3b8"),spaceAfter=4)
    story=[Paragraph("Niko Vault",tit),
           Paragraph(f"{label}  ·  {len(entries)} entries  ·  {date.today():%d %b %Y}",sub),
           HRFlowable(width="100%",thickness=1.5,color=colors.HexColor("#e8e4df")),Spacer(1,12)]
    for i,e in enumerate(entries):
        story+=[Paragraph(e.get("title","Untitled"),hd),
                Paragraph(f"Branch: {e.get('branch','General')}   Created: {fmt(e.get('created_at',''))}",mt)]
        if e.get("author"):      story.append(Paragraph(f"Author: {e['author']}",mt))
        if e.get("device_type"): story.append(Paragraph(f"Device: {e['device_type']}",mt))
        if e.get("link"):        story.append(Paragraph(f"Link: {e['link']}",mt))
        if e.get("content"):
            safe=e["content"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br/>")
            story.append(Paragraph(safe,bd))
        if e.get("tags"):        story.append(Paragraph("Tags: "+"  ".join(f"#{t}" for t in e["tags"]),mt))
        story.append(HRFlowable(width="100%",thickness=0.5,color=colors.HexColor("#f1ede8")))
        story.append(Spacer(1,6))
        if i>0 and i%7==0: story.append(PageBreak())
    doc.build(story)
    return buf.getvalue()

def pdf_link(pdf_bytes, filename, label="📥 Download PDF"):
    b64=base64.b64encode(pdf_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="display:inline-block;background:#1e293b;color:#fff;padding:0.45rem 1rem;border-radius:8px;font-size:0.72rem;font-family:\'JetBrains Mono\',monospace;text-decoration:none">{label}</a>'

# ── Molecule viewer ───────────────────────────────────────────────────────────
def mol_html(smiles):
    bg = "#0f1623" if DM else "white"
    return f"""<!DOCTYPE html><html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<script src="https://3dmol.org/build/3Dmol-min.js"></script>
<style>body{{margin:0;background:{bg};}} #v{{width:100%;height:380px;position:relative;}}</style>
</head><body><div id="v"></div>
<script>$(function(){{
  var viewer=$3Dmol.createViewer("v",{{backgroundColor:"{bg}"}});
  var sm={json.dumps(smiles)};
  $.get("https://cactus.nci.nih.gov/chemical/structure/"+encodeURIComponent(sm)+"/file?format=sdf&get3coords=True",
    function(data){{
      viewer.addModel(data,"sdf");
      viewer.setStyle({{}},{{stick:{{radius:0.15}},sphere:{{scale:0.28}}}});
      viewer.zoomTo(); viewer.render(); viewer.spin("y",0.5);
    }}).fail(function(){{
      viewer.addModel(sm,"smi");
      viewer.setStyle({{}},{{stick:{{}}}});
      viewer.zoomTo(); viewer.render();
    }});
}});</script></body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    lc, tc = st.columns([3,1])
    with lc:
        st.markdown(f"""<div style='display:flex;align-items:center;gap:0.5rem;padding-bottom:0.3rem'>
        <div style='width:34px;height:34px;background:#1e293b;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1rem'>⚗️</div>
        <div><div style='font-family:"Cormorant Garamond",serif;font-size:1.05rem;font-weight:700;color:{T["heading"]};line-height:1'>Niko Vault</div>
        <div style='font-family:"JetBrains Mono",monospace;font-size:0.46rem;color:{T["muted"]};letter-spacing:0.15em'>RESEARCH SYSTEM v2</div></div></div>""",
        unsafe_allow_html=True)
    with tc:
        st.markdown("<div style='padding-top:0.4rem'></div>",unsafe_allow_html=True)
        dark = st.toggle("🌙", value=DM, key="dm", help="Dark / Light mode")
        if dark != DM:
            st.session_state.dark_mode = dark; st.rerun()

    st.divider()
    for label, sid in SECTIONS.items():
        cnt   = len(get_entries(sid)) if sid not in ("planner","molecule") else ""
        badge = f" `{cnt}`" if cnt!="" else ""
        act   = st.session_state.section == sid
        if st.button(f"{label}{badge}", key=f"nav_{sid}", use_container_width=True,
                     type="primary" if act else "secondary"):
            go(sid); st.rerun()

    st.divider()
    st.markdown(f"<div style='font-family:\"JetBrains Mono\",monospace;font-size:0.56rem;color:{T['muted']};text-align:center;letter-spacing:0.1em'>{total()} TOTAL ENTRIES<br><span style='font-size:0.48rem'>saved · niko_vault_data.json</span></div>",
    unsafe_allow_html=True)

sec = st.session_state.section

# ══════════════════════════════════════════════════════════════════════════════
# MOLECULE VIEWER
# ══════════════════════════════════════════════════════════════════════════════
if sec == "molecule":
    st.markdown("<div class='main-title'>⚗️ Molecule Viewer</div>", unsafe_allow_html=True)
    st.caption("Interactive 3D molecular structures — drag to rotate, scroll to zoom.")
    st.divider()

    left, right = st.columns([1,2], gap="large")
    with left:
        st.markdown("<div class='mono-lbl'>SELECT MOLECULE</div>", unsafe_allow_html=True)
        choice = st.selectbox("Molecule", ["Custom SMILES"]+list(MOLECULES.keys()), label_visibility="collapsed")
        if choice=="Custom SMILES":
            smiles = st.text_input("SMILES string", placeholder="e.g. CCO for ethanol")
            mname  = "Custom Molecule"
        else:
            smiles = MOLECULES[choice]
            mname  = choice

        st.divider()
        if choice in MOL_INFO:
            info = MOL_INFO[choice]
            for lbl,val in [("Formula",info["formula"]),("Mol. Weight",info["mw"]),("Type",info["type"]+" Chemistry")]:
                st.markdown(f"<div class='stat-card' style='text-align:left;margin-bottom:0.5rem'><div class='mono-lbl'>{lbl}</div><div style='font-family:\"JetBrains Mono\",monospace;font-size:0.88rem;font-weight:700;color:{T[\"heading\"]};margin-top:2px'>{val}</div></div>",
                unsafe_allow_html=True)
        st.divider()
        st.markdown(f"<div class='mono-lbl'>SMILES</div><div style='font-family:\"JetBrains Mono\",monospace;font-size:0.7rem;color:#7c3aed;background:{'#1a0a2e' if DM else '#faf5ff'};border:1px solid #e9d5ff;border-radius:6px;padding:0.45rem 0.7rem;word-break:break-all;margin-top:0.3rem'>{smiles or '—'}</div>",
        unsafe_allow_html=True)

    with right:
        if smiles:
            st.markdown(f"<div class='sec-title'>{mname}</div>", unsafe_allow_html=True)
            st.caption("🖱 Drag = rotate  ·  Scroll = zoom  ·  Right-click = pan")
            st.components.v1.html(mol_html(smiles), height=400, scrolling=False)
            st.markdown(f"<div style='font-family:\"JetBrains Mono\",monospace;font-size:0.58rem;color:{T['muted']};margin-top:0.4rem'>3D via NCI CACTUS · Rendered with 3Dmol.js</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='height:400px;display:flex;align-items:center;justify-content:center;background:{T['card']};border:1.5px dashed {T['border']};border-radius:12px;flex-direction:column;gap:1rem'><div style='font-size:3rem'>⚗️</div><div style='font-family:\"JetBrains Mono\",monospace;font-size:0.7rem;color:{T[\"muted\"]};letter-spacing:0.1em'>SELECT A MOLECULE OR ENTER SMILES</div></div>",
            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PLANNER
# ══════════════════════════════════════════════════════════════════════════════
elif sec == "planner":
    st.markdown("<div class='main-title'>🗓 Planner</div>", unsafe_allow_html=True)
    st.caption("Organize your research time — daily, weekly, monthly.")
    st.divider()

    pcol, ccol = st.columns([3,2], gap="large")
    with pcol:
        ptab = st.radio("", ["Daily","Weekly","Monthly"], horizontal=True, label_visibility="collapsed")
        if ptab=="Daily":
            pk  = str(st.date_input("Date", value=date.today(), label_visibility="collapsed"))
            plbl= datetime.fromisoformat(pk).strftime("%A, %d %B %Y")
        elif ptab=="Weekly":
            td  = date.today(); ws=td-timedelta(days=td.weekday())
            pw  = st.date_input("Week start", value=ws, label_visibility="collapsed")
            pk  = f"week-{pw}"; plbl=f"Week of {pw:%d %B %Y}"
        else:
            cy2,cm2=st.columns(2)
            with cy2: py=st.selectbox("Year",range(2020,2036),index=list(range(2020,2036)).index(date.today().year))
            with cm2: pm=st.selectbox("Month",MONTHS,index=date.today().month-1)
            pk=f"month-{py}-{MONTHS.index(pm)+1}"; plbl=f"{pm} {py}"

        st.markdown(f"<div class='sec-title' style='margin:0.4rem 0'>{plbl}</div>", unsafe_allow_html=True)
        ptxt = st.text_area("Plan",value=get_plans().get(pk,""),placeholder="Write your plan...",height=280,label_visibility="collapsed")
        if st.button("💾 Save Plan",type="primary"):
            st.session_state.data["plans"][pk]=ptxt
            save_data(st.session_state.data); st.success("Saved ✓")
        st.info("🎙 Win+H (Windows) · Fn+Globe (Mac) to dictate while text box is focused.")

    with ccol:
        st.markdown("<div class='mono-lbl' style='margin-bottom:0.5rem'>📅 CALENDAR</div>", unsafe_allow_html=True)
        nav1,nav2,nav3=st.columns([1,3,1])
        with nav1:
            if st.button("‹",key="cp"):
                if st.session_state.cal_month==1: st.session_state.cal_month=12; st.session_state.cal_year-=1
                else: st.session_state.cal_month-=1
                st.rerun()
        with nav2: st.markdown(f"<div style='text-align:center;font-family:\"Cormorant Garamond\",serif;font-weight:700;font-size:1rem;color:{T[\"heading\"]}'>{MONTHS[st.session_state.cal_month-1]} {st.session_state.cal_year}</div>",unsafe_allow_html=True)
        with nav3:
            if st.button("›",key="cn"):
                if st.session_state.cal_month==12: st.session_state.cal_month=1; st.session_state.cal_year+=1
                else: st.session_state.cal_month+=1
                st.rerun()

        plans_d = get_plans(); td2=date.today()
        mat=calendar.monthcalendar(st.session_state.cal_year,st.session_state.cal_month)
        hdr="<div style='display:grid;grid-template-columns:repeat(7,1fr);gap:2px;margin-top:0.4rem'>"
        for h in ["Mo","Tu","We","Th","Fr","Sa","Su"]:
            hdr+=f"<div style='text-align:center;font-family:\"JetBrains Mono\",monospace;font-size:0.54rem;color:{T[\"muted\"]};padding:3px'>{h}</div>"
        hdr+="</div>"
        st.markdown(hdr,unsafe_allow_html=True)

        grid="<div style='display:grid;grid-template-columns:repeat(7,1fr);gap:2px'>"
        for week in mat:
            for d2 in week:
                if d2==0: grid+="<div></div>"
                else:
                    ds=f"{st.session_state.cal_year}-{st.session_state.cal_month:02d}-{d2:02d}"
                    hp=ds in plans_d and plans_d[ds].strip()
                    it=(d2==td2.day and st.session_state.cal_month==td2.month and st.session_state.cal_year==td2.year)
                    bg="#1e293b" if it else ("#f0fdf4" if hp else T["card"])
                    cl="#fff" if it else ("#16a34a" if hp else T["muted"])
                    fw="700" if (it or hp) else "400"
                    grid+=f"<div style='text-align:center;background:{bg};color:{cl};font-weight:{fw};border-radius:6px;padding:5px 2px;font-family:\"JetBrains Mono\",monospace;font-size:0.7rem'>{d2}</div>"
        grid+="</div>"
        st.markdown(grid,unsafe_allow_html=True)
        st.markdown(f"<div style='margin-top:0.6rem;font-family:\"JetBrains Mono\",monospace;font-size:0.54rem;color:{T[\"muted\"]}'>🟢 has plan &nbsp; ⬛ today</div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONTENT SECTIONS
# ══════════════════════════════════════════════════════════════════════════════
else:
    slabel   = next(k for k,v in SECTIONS.items() if v==sec)
    scolor   = SEC_COLOR.get(sec,"#1e293b")
    all_ents = get_entries(sec)

    # ── Header ────────────────────────────────────────────────────────────────
    h1,h2,h3 = st.columns([4,1,1])
    with h1:
        st.markdown(f"<div class='main-title'>{slabel}</div>",unsafe_allow_html=True)
        st.caption(f"{len(all_ents)} {'entry' if len(all_ents)==1 else 'entries'} saved")
    with h2:
        if st.session_state.view=="list":
            if st.button("➕ New Entry",type="primary",use_container_width=True): sv("form"); st.rerun()
        else:
            if st.button("← Back",use_container_width=True): sv("list"); st.rerun()
    with h3:
        if st.session_state.view=="list" and PDF_OK:
            if st.button("📥 Export PDF",use_container_width=True):
                pdf=make_pdf(all_ents,slabel)
                st.markdown(pdf_link(pdf,f"niko_{sec}_{date.today()}.pdf"),unsafe_allow_html=True)
        elif not PDF_OK:
            st.caption("`pip install reportlab`")

    st.divider()

    # ── FORM ──────────────────────────────────────────────────────────────────
    if st.session_state.view=="form":
        editing=st.session_state.edit_mode
        ex=next((e for e in all_ents if e["id"]==st.session_state.selected_id),{}) if editing else {}
        st.markdown(f"### {'✏️ Edit' if editing else '➕ New Entry'}")

        with st.form("ef"):
            c1,c2=st.columns(2)
            with c1: title =st.text_input("Title *",value=ex.get("title",""),placeholder="Clear title...")
            with c2: branch=st.selectbox("Branch",BRANCHES,index=BRANCHES.index(ex.get("branch","General")))
            author     =st.text_input("Author / Source",value=ex.get("author",""))      if sec in HAS_AUTHOR else ""
            device_type=st.text_input("Device / Equipment",value=ex.get("device_type",""),placeholder="e.g. NMR, HPLC...") if sec in HAS_DEVICE else ""
            link       =st.text_input("URL / Reference",value=ex.get("link",""),placeholder="https://...")  if sec in HAS_LINK   else ""
            content    =st.text_area("Notes / Content",value=ex.get("content",""),
                                     placeholder="Write notes or dictate with Win+H / Fn+Globe...",height=240)
            tags_raw   =st.text_input("Tags (comma separated)",value=", ".join(ex.get("tags",[])),
                                      placeholder="e.g. NMR, hypothesis, organic")
            if st.form_submit_button("💾 Save Entry",type="primary"):
                if not title.strip(): st.error("Title required!")
                else:
                    tags   =[t.strip() for t in tags_raw.split(",") if t.strip()]
                    payload={"title":title.strip(),"branch":branch,"content":content.strip(),
                             "author":author.strip() if isinstance(author,str) else "",
                             "device_type":device_type.strip() if isinstance(device_type,str) else "",
                             "link":link.strip() if isinstance(link,str) else "","tags":tags}
                    el=get_entries(sec)
                    if editing:
                        up=[{**e,**payload,"updated_at":datetime.now().isoformat()} if e["id"]==st.session_state.selected_id else e for e in el]
                    else:
                        up=[{"id":str(uuid.uuid4()),"created_at":datetime.now().isoformat(),"updated_at":datetime.now().isoformat(),**payload}]+el
                    st.session_state.data["entries"][sec]=up
                    save_data(st.session_state.data); sv("list"); st.success("Saved ✓"); st.rerun()

        with st.expander("🎙 Voice Dictation Help"):
            st.markdown("""| Platform | Shortcut |\n|---|---|\n| 🪟 Windows | `Win + H` |\n| 🍎 Mac | `Fn + Globe` |\n| 📱 Mobile | Mic on keyboard |\n\nClick the Notes box first, then use your shortcut.""")

    # ── DETAIL ────────────────────────────────────────────────────────────────
    elif st.session_state.view=="detail":
        entry=next((e for e in all_ents if e["id"]==st.session_state.selected_id),None)
        if not entry: sv("list"); st.rerun()
        else:
            st.markdown(f"<span class='branch-badge' style='background:{scolor}18;color:{scolor}'>{entry.get('branch','General')}</span>",unsafe_allow_html=True)
            st.markdown(f"<div style='font-family:\"Cormorant Garamond\",serif;font-size:1.8rem;font-weight:700;color:{T[\"heading\"]};margin:0.4rem 0'>{entry['title']}</div>",unsafe_allow_html=True)
            st.markdown(f"<div class='entry-meta'>Created: {fmt(entry.get('created_at',''))}</div>",unsafe_allow_html=True)
            if entry.get("author"):      st.markdown(f"<div class='entry-meta'>✍️ {entry['author']}</div>",unsafe_allow_html=True)
            st.divider()
            if entry.get("device_type"): st.info(f"🔬 **Device:** {entry['device_type']}")
            if entry.get("link"):        st.markdown(f"🔗 [{entry['link']}]({entry['link']})")
            if entry.get("content"):     st.markdown(entry["content"])
            if entry.get("tags"):        st.markdown(" ".join(f"<span class='tag-pill'>#{t}</span>" for t in entry["tags"]),unsafe_allow_html=True)
            st.divider()
            ce,cd,cx=st.columns([1,1,3])
            with ce:
                if st.button("✏️ Edit",type="primary",use_container_width=True): sv("form",eid=entry["id"],edit=True); st.rerun()
            with cd:
                if st.button("🗑 Delete",use_container_width=True):
                    st.session_state.data["entries"][sec]=[e for e in all_ents if e["id"]!=entry["id"]]
                    save_data(st.session_state.data); sv("list"); st.rerun()
            with cx:
                if PDF_OK:
                    pdf=make_pdf([entry],slabel)
                    fname=f"niko_{entry['title'][:25].replace(' ','_')}_{date.today()}.pdf"
                    st.markdown(pdf_link(pdf,fname,"📥 Export This Entry"),unsafe_allow_html=True)

    # ── LIST ──────────────────────────────────────────────────────────────────
    else:
        bc={b:sum(1 for e in all_ents if e.get("branch")==b) for b in BRANCHES}
        cs=st.columns(len(BRANCHES))
        for i,b in enumerate(BRANCHES):
            with cs[i]: st.markdown(f"<div class='stat-card'><div style='font-family:\"JetBrains Mono\",monospace;font-size:1.1rem;font-weight:700;color:{scolor}'>{bc[b]}</div><div style='font-family:\"JetBrains Mono\",monospace;font-size:0.5rem;color:{T[\"muted\"]};text-transform:uppercase;letter-spacing:0.08em;margin-top:2px'>{b}</div></div>",unsafe_allow_html=True)

        st.markdown("<div style='margin-top:0.9rem'></div>",unsafe_allow_html=True)
        fs,ff=st.columns([3,2])
        with fs: srch=st.text_input("🔍",placeholder="Search titles, content, tags...",label_visibility="collapsed")
        with ff: bf  =st.selectbox("Branch",["All Branches"]+BRANCHES,label_visibility="collapsed")

        fil=all_ents
        if bf!="All Branches": fil=[e for e in fil if e.get("branch")==bf]
        if srch:
            q=srch.lower()
            fil=[e for e in fil if q in e.get("title","").lower() or q in e.get("content","").lower()
                 or any(q in t.lower() for t in e.get("tags",[])) or q in e.get("author","").lower()]
        fil=sorted(fil,key=lambda e:e.get("created_at",""),reverse=True)

        if not fil:
            st.markdown(f"<div style='text-align:center;padding:4rem 1rem;color:{T[\"muted\"]}'><div style='font-size:2.5rem;margin-bottom:1rem'>📭</div><div style='font-family:\"JetBrains Mono\",monospace;font-size:0.72rem;letter-spacing:0.1em'>{'No entries yet — hit + New Entry!' if not all_ents else 'No entries match.'}</div></div>",unsafe_allow_html=True)
        else:
            grps={}
            for e in fil:
                try: k=datetime.fromisoformat(e["created_at"]).strftime("%A, %d %B %Y")
                except: k="Unknown"
                grps.setdefault(k,[]).append(e)

            for dlbl,des in grps.items():
                st.markdown(f"<div style='font-family:\"JetBrains Mono\",monospace;font-size:0.56rem;letter-spacing:0.18em;color:{T[\"muted\"]};text-transform:uppercase;border-bottom:1.5px solid {T[\"border\"]};padding-bottom:4px;margin:1.2rem 0 0.6rem'>{dlbl}</div>",unsafe_allow_html=True)
                for e in des:
                    ec1,ec2=st.columns([6,1])
                    with ec1:
                        prev=e.get("content","")[:130]+("..." if len(e.get("content",""))>130 else "")
                        tg=" ".join(f"<span class='tag-pill'>#{t}</span>" for t in e.get("tags",[]))
                        st.markdown(f"""<div class='entry-card' style='border-left:3px solid {scolor}44'>
                        <span class='branch-badge' style='background:{scolor}18;color:{scolor}'>{e.get('branch','General')}</span>
                        {"<span class='entry-meta' style='margin-left:8px'>✍️ "+e['author']+"</span>" if e.get('author') else ""}
                        <div class='entry-title' style='margin-top:4px'>{e['title']}</div>
                        {"<div style='font-size:0.77rem;color:"+T["muted"]+";margin-top:4px;line-height:1.5'>"+prev+"</div>" if prev else ""}
                        {"<div style='margin-top:6px'>"+tg+"</div>" if e.get("tags") else ""}
                        <div class='entry-meta' style='margin-top:6px'>{fmt(e.get('created_at',''))}</div></div>""",
                        unsafe_allow_html=True)
                    with ec2:
                        if st.button("Open →",key=f"o_{e['id']}",use_container_width=True):
                            sv("detail",eid=e["id"]); st.rerun()
