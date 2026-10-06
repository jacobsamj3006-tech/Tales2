"""Build the HTML version of the analysis from the Markdown source.

Usage: python3 analysis/build/build.py
Reads analysis/Sticky_Situation_Deep_Read.md, writes analysis/Sticky_Situation_Deep_Read.html.
Requires pandoc on PATH.
"""
import pathlib
import re
import subprocess
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "Sticky_Situation_Deep_Read.md"
OUT = ROOT / "Sticky_Situation_Deep_Read.html"

with tempfile.TemporaryDirectory() as tmp:
    tpl = pathlib.Path(tmp) / "split.tpl"
    tpl.write_text("$toc$\n@@@BODY@@@\n$body$\n", encoding="utf-8")
    raw = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html5", "--toc", "--toc-depth=2",
         "-s", f"--template={tpl}", str(SRC)],
        check=True, capture_output=True, text=True,
    ).stdout

toc, body = raw.split("@@@BODY@@@", 1)

# Tables scroll inside their own container.
body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")

# "Score: 9/10." / "Rating: 9/10." / "Overall: 8.5/10." lead-ins become stamps.
def stamp(m):
    label, value, tail = m.group(1), m.group(2), m.group(3)
    big = " big" if label == "Overall" else ""
    tail = tail.strip()
    tail = "" if tail in ("", ".") else " " + tail.lstrip(". ")
    return f'<p class="score{big}"><span class="stamp">{label} {value}</span>{tail}'

body = re.sub(r'<p><strong>(Score|Rating|Overall): ([0-9.]+/10)([^<]*)</strong>', stamp, body)

# Italic-only paragraph right after an h2 is the chapter meta line.
body = re.sub(r'(</h2>\s*)<p><em>(.*?)</em></p>', r'\1<p class="meta"><em>\2</em></p>', body, flags=re.S)

# Chapter numbers like "1.1" or "4.0" at the start of an h2 get a tape label.
body = re.sub(r'(<h2 id="[^"]*">)(\d\.\d{1,2}) ', r'\1<span class="chnum">\2</span> ', body)

# Sidebar and mobile copies of the contents; the mobile copy drops ids to keep them unique.
mobile_toc = re.sub(r'\sid="toc-[^"]*"', "", toc)

css = (HERE / "page.css").read_text(encoding="utf-8")

js = r"""
(function () {
  try {
    var side = document.querySelector('.sidebar .toc');
    if (side) {
      side.querySelectorAll(':scope > ul > li').forEach(function (li) {
        var a = li.querySelector(':scope > a');
        var sub = li.querySelector(':scope > ul');
        var row = document.createElement('div');
        row.className = 'toc-row';
        li.insertBefore(row, a);
        row.appendChild(a);
        if (sub) {
          var b = document.createElement('button');
          b.type = 'button';
          b.className = 'toc-toggle';
          b.setAttribute('aria-label', 'Show or hide ' + a.textContent.trim());
          row.appendChild(b);
          var set = function (open) {
            li.classList.toggle('collapsed', !open);
            b.textContent = open ? '−' : '+';
            b.setAttribute('aria-expanded', open ? 'true' : 'false');
          };
          set(false);
          b.addEventListener('click', function () { set(li.classList.contains('collapsed')); });
          li._set = set;
        }
      });
    }
    var links = {};
    if (side) side.querySelectorAll('a[href^="#"]').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var current = null;
    function activate(id) {
      var a = links[id];
      if (!a || a === current) return;
      if (current) current.classList.remove('active');
      current = a;
      a.classList.add('active');
      var top = a.closest('.toc > ul > li');
      if (top && top._set) top._set(true);
      var rect = a.getBoundingClientRect();
      var bar = side.closest('.sidebar');
      if (bar && (rect.top < 0 || rect.bottom > window.innerHeight)) {
        a.scrollIntoView({ block: 'center' });
      }
    }
    var heads = Array.prototype.slice.call(document.querySelectorAll('.doc h1[id], .doc h2[id]'));
    if ('IntersectionObserver' in window && side) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) activate(e.target.id); });
      }, { rootMargin: '0px 0px -70% 0px' });
      heads.forEach(function (h) { io.observe(h); });
    }
    var mob = document.querySelector('.mobile-toc');
    if (mob) mob.addEventListener('click', function (e) {
      if (e.target.closest('a')) mob.open = false;
    });
  } catch (err) { /* navigation helpers are optional */ }
})();
"""

page = f"""<title>Sticky Situation Deep Read</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=IBM+Plex+Mono:wght@400;600&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,700;1,7..72,400&display=swap">
<style>
{css}
</style>
<a class="skip" href="#main">Skip to the analysis</a>
<div class="shell">
  <aside class="sidebar" aria-label="Contents">
    <div class="side-head">Contents</div>
    <nav class="toc">
{toc}
    </nav>
  </aside>
  <main id="main">
    <header class="masthead">
      <span class="tape">Prologue to S4 Ch6</span>
      <p class="eyebrow">A complete read of</p>
      <p class="book-line">Tales of Being Limitless</p>
      <h1 class="title">Sticky<span class="sub">Situation</span></h1>
      <p class="lede">Every chapter, every character, every callback. What happens, the small details, what works, what I'd push on, and a score for each, followed by character dossiers, themes, a continuity ledger, theories, and craft notes.</p>
      <ul class="stats">
        <li><b>53</b> chapters + Prologue</li>
        <li><b>~104,700</b> words read</li>
        <li><b>4</b> sections</li>
        <li>Overall <b>8.5/10</b></li>
      </ul>
    </header>
    <details class="mobile-toc">
      <summary>Contents</summary>
      <nav class="toc">
{mobile_toc}
      </nav>
    </details>
    <article class="doc">
{body}
    </article>
    <footer class="end">
      <span>End of the analysis. The book continues.</span>
      <a href="#main">Back to top</a>
    </footer>
  </main>
</div>
<script>
{js}
</script>
"""

OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT} ({len(page):,} bytes)")
