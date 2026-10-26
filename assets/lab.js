/* 우주 리서치 실습 공통 도구: 자료 읽기 · SVG 그래프 · 예상 결과 비교 · 연구 노트 저장
   외부 라이브러리 없이 동작한다. 각 실습 페이지는 window.LAB 에 장 번호를 두고 이 파일을 불러 쓴다. */
const Lab = (() => {
  const NS = "http://www.w3.org/2000/svg";

  // ---------- 자료 ----------
  async function csv(url) {
    const t = await (await fetch(url)).text();
    const lines = t.replace(/\r/g, "").split("\n").filter(l => l.trim() && !l.startsWith("#"));
    const head = lines[0].split(",").map(s => s.trim());
    const num = v => (v === "" || isNaN(+v)) ? v : +v;
    return lines.slice(1).map(l => {
      const c = l.split(","), o = {};
      head.forEach((h, i) => (o[h] = num((c[i] ?? "").trim())));
      return o;
    });
  }
  const json = async url => (await fetch(url)).json();
  const fmt = (v, d = 2) => (v == null || isNaN(v)) ? "—" : (+v).toLocaleString("ko-KR", { minimumFractionDigits: d, maximumFractionDigits: d });

  // ---------- 그래프 ----------
  function el(tag, attrs = {}, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function ticks(a, b, n = 6) {
    const span = b - a, step0 = span / n, p = Math.pow(10, Math.floor(Math.log10(step0)));
    const step = [1, 2, 2.5, 5, 10].map(m => m * p).find(s => s >= step0) || p * 10;
    const out = [];
    for (let v = Math.ceil(a / step) * step; v <= b + 1e-9; v += step) out.push(+v.toFixed(10));
    return out;
  }
  /* plot(target, {series:[{x,y,color,width,dash,label,type:'line'|'dots'|'bars'|'steps'}], xmin,xmax,ymin,ymax,
                    xlabel,ylabel, bands:[{x0,x1,label}], vlines:[{x,label,color}], hlines:[{y,label}], height, logy}) */
  function plot(target, o) {
    const W = 900, H = o.height || 380, L = 64, R = 18, T = 26, B = 52;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" });
    const cs = getComputedStyle(document.documentElement);
    const ink = cs.getPropertyValue("--ink").trim() || "#222", hair = cs.getPropertyValue("--hair").trim() || "#ddd";
    const ch = cs.getPropertyValue("--ch").trim() || "#2E8C86";
    const xs = o.series.flatMap(s => s.x), ys = o.series.flatMap(s => s.y);
    const x0 = o.xmin ?? Math.min(...xs), x1 = o.xmax ?? Math.max(...xs);
    let y0 = o.ymin ?? Math.min(0, ...ys), y1 = o.ymax ?? Math.max(...ys) * 1.05;
    const ly = v => o.logy ? Math.log10(Math.max(v, 1e-12)) : v;
    if (o.logy) { y0 = ly(o.ymin ?? Math.min(...ys.filter(v => v > 0))); y1 = ly(o.ymax ?? Math.max(...ys)); }
    const X = v => L + (W - L - R) * (v - x0) / (x1 - x0);
    const Y = v => H - B - (H - T - B) * (ly(v) - y0) / (y1 - y0 || 1);
    (o.bands || []).forEach(b => {
      el("rect", { x: X(b.x0), y: T, width: Math.max(1, X(b.x1) - X(b.x0)), height: H - T - B, fill: ch, "fill-opacity": .12 }, svg);
      if (b.label) el("text", { x: (X(b.x0) + X(b.x1)) / 2, y: T - 8, "text-anchor": "middle", class: "lab", style: `fill:${ch}` }, svg).textContent = b.label;
    });
    for (const t of ticks(x0, x1, o.xticks || 8)) {
      el("line", { x1: X(t), x2: X(t), y1: H - B, y2: H - B + 5, stroke: ink }, svg);
      el("text", { x: X(t), y: H - B + 20, "text-anchor": "middle" }, svg).textContent = o.xfmt ? o.xfmt(t) : t;
    }
    const yt = o.logy ? ticks(Math.ceil(y0), Math.floor(y1), 5).map(v => Math.pow(10, v)) : ticks(y0, y1, 5);
    for (const t of yt) {
      el("line", { x1: L, x2: W - R, y1: Y(t), y2: Y(t), stroke: hair }, svg);
      el("text", { x: L - 8, y: Y(t) + 4, "text-anchor": "end" }, svg).textContent = o.yfmt ? o.yfmt(t) : (+t.toPrecision(4));
    }
    el("line", { x1: L, x2: W - R, y1: H - B, y2: H - B, stroke: ink }, svg);
    (o.hlines || []).forEach(h => {
      el("line", { x1: L, x2: W - R, y1: Y(h.y), y2: Y(h.y), stroke: h.color || ink, "stroke-dasharray": "4 4" }, svg);
      if (h.label) el("text", { x: W - R, y: Y(h.y) - 6, "text-anchor": "end", class: "lab" }, svg).textContent = h.label;
    });
    for (const s of o.series) {
      const col = s.color || ink, sw = s.width || 1.4;
      if (s.type === "dots") {
        s.x.forEach((x, i) => el("circle", { cx: X(x), cy: Y(s.y[i]), r: s.r || 2.4, fill: col, "fill-opacity": s.opacity ?? .8 }, svg));
      } else if (s.type === "bars") {
        const bw = s.barWidth ? (X(x0 + s.barWidth) - X(x0)) : 6;
        s.x.forEach((x, i) => el("rect", { x: X(x) - bw / 2, y: Y(s.y[i]), width: Math.max(1, bw - 1), height: Math.max(0, Y(o.logy ? Math.pow(10, y0) : Math.max(y0, 0)) - Y(s.y[i])), fill: col, "fill-opacity": s.opacity ?? .85 }, svg));
      } else {
        const pts = s.x.map((x, i) => `${X(x).toFixed(1)},${Y(s.y[i]).toFixed(1)}`).join(" ");
        el("polyline", { points: pts, fill: "none", stroke: col, "stroke-width": sw, "stroke-dasharray": s.dash || "", "stroke-linejoin": "round" }, svg);
      }
    }
    (o.vlines || []).forEach(v => {
      el("line", { x1: X(v.x), x2: X(v.x), y1: T, y2: H - B, stroke: v.color || ch, "stroke-width": 1.4, "stroke-dasharray": v.dash || "" }, svg);
      if (v.label) el("text", { x: X(v.x) + 4, y: T + 12, class: "lab", style: `fill:${v.color || ch}` }, svg).textContent = v.label;
    });
    if (o.xlabel) el("text", { x: W - R, y: H - 10, "text-anchor": "end" }, svg).textContent = o.xlabel;
    if (o.ylabel) el("text", { x: L, y: 14 }, svg).textContent = o.ylabel;
    const legend = o.series.filter(s => s.label);
    legend.forEach((s, i) => {
      const lx = L + 10 + i * 170;
      el("rect", { x: lx, y: T + 2, width: 14, height: 4, fill: s.color || ink }, svg);
      el("text", { x: lx + 20, y: T + 8 }, svg).textContent = s.label;
    });
    const box = typeof target === "string" ? document.querySelector(target) : target;
    box.innerHTML = "";
    box.appendChild(svg);
    return svg;
  }

  // ---------- 예상 결과와 비교 ----------
  /* compare(target, rows:[{label, mine, expected, tol, digits, unit}]) */
  function compare(target, rows) {
    const box = typeof target === "string" ? document.querySelector(target) : target;
    let h = '<table class="cmp"><tr><th>항목</th><th>당신의 값</th><th>책의 예상 결과</th><th></th></tr>';
    for (const r of rows) {
      const same = r.mine != null && Math.abs(r.mine - r.expected) <= (r.tol ?? 0);
      h += `<tr><td>${r.label}</td><td class="mono">${fmt(r.mine, r.digits ?? 2)}${r.unit || ""}</td>` +
           `<td class="mono">${fmt(r.expected, r.digits ?? 2)}${r.unit || ""}</td>` +
           `<td class="${same ? "ok" : "diff"}">${same ? "같음" : "다름 — 무엇을 바꿨는지 확인"}</td></tr>`;
    }
    box.innerHTML = h + "</table>";
  }

  // ---------- 연구 노트(이 브라우저에만 저장) ----------
  function notebook(target, labId, template) {
    const box = typeof target === "string" ? document.querySelector(target) : target;
    const key = `wyr-note-${labId}`;
    let saved = "";
    try { saved = localStorage.getItem(key) || ""; } catch (e) {}
    box.innerHTML = `<textarea class="notebox" aria-label="연구 노트">${saved || template}</textarea>
      <p style="display:flex;gap:8px;margin-top:8px"><button class="btn" type="button">노트를 파일로 저장</button>
      <button class="btn ghost" type="button">양식으로 되돌리기</button></p>
      <p class="note">노트는 이 브라우저에만 저장되고 어디로도 보내지지 않는다.</p>`;
    const ta = box.querySelector("textarea");
    ta.addEventListener("input", () => { try { localStorage.setItem(key, ta.value); } catch (e) {} });
    const [save, reset] = box.querySelectorAll("button");
    save.onclick = () => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([ta.value], { type: "text/plain" }));
      a.download = `연구노트_${labId}.txt`;
      a.click();
    };
    reset.onclick = () => { ta.value = template; try { localStorage.removeItem(key); } catch (e) {} };
  }

  const NOTE = (q) => `질문: ${q}\n자료: (파일 이름 · 내려받은 날짜 · SHA256 앞 8자리)\n선택: (구간 · 기준값 · 단위 · 빈칸 처리)\n결과: (숫자만)\n해석: (결과와 분리해서)\n다음: (다음 질문 하나)\n`;

  return { csv, json, fmt, plot, compare, notebook, NOTE };
})();
