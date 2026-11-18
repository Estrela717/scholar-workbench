import React, { useState, useEffect, useRef } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

const request = async (path, body, method = "POST") => {
  const r = await fetch(
    "/api" + path,
    body === undefined
      ? {}
      : {
          method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  const d = await r.json();
  if (!r.ok) throw new Error(d.detail || "请求失败");
  return d;
};
const download = (name, text, type = "text/plain") => {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};

export function FormulaCard({ formula, locate, notify }) {
  const [latex, setLatex] = useState(""),
    [busy, setBusy] = useState(false),
    [reviewed, setReviewed] = useState(false);
  useEffect(() => {
    let live = true;
    request("/formulas/" + formula.id)
      .then((r) => {
        if (live && r) {
          setLatex(r.latex);
          setReviewed(!!r.reviewed);
        }
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [formula.id]);
  const render = () => {
    try {
      return katex.renderToString(
        latex.replace(/^\$\$?|\$\$?$/g, "").replace(/^\\\[|\\\]$/g, ""),
        {
          displayMode: true,
          throwOnError: true,
          trust: false,
          strict: "error",
          maxExpand: 1000,
        },
      );
    } catch {
      return null;
    }
  };
  const html = latex ? render() : null;
  return (
    <div className="card formula-editor">
      <button className="text-button" onClick={locate}>
        定位原始公式 ↗
      </button>
      <pre>{formula.text}</pre>
      <button
        className="button secondary small"
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          try {
            const r = await request("/formulas/" + formula.id, {});
            setLatex(r.latex);
            setReviewed(!!r.reviewed);
          } catch (e) {
            notify(e.message, true);
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "正在识别原图…" : "原图转 LaTeX"}
      </button>
      {latex && (
        <>
          <textarea
            aria-label="公式 LaTeX"
            value={latex}
            onChange={(e) => {
              setLatex(e.target.value);
              setReviewed(false);
            }}
          />
          {html ? (
            <div
              className="formula-render"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          ) : (
            <p>表达式尚不能渲染，请对照原图修正。</p>
          )}
          <div className="button-row">
            <button
              className="button secondary small"
              onClick={async () => {
                try {
                  await request("/formulas/" + formula.id, { latex }, "PUT");
                  setReviewed(true);
                  notify("已保存校对结果");
                } catch (e) {
                  notify(e.message, true);
                }
              }}
            >
              保存校对结果
            </button>
            <button
              className="text-button"
              onClick={() => download("formula.tex", latex)}
            >
              导出 LaTeX
            </button>
          </div>
          <small>
            {reviewed ? "用户已校对" : "自动识别待核对；可渲染不等于转写正确"}
          </small>
        </>
      )}
    </div>
  );
}

export function TrackingPanel({ query, onResults, notify }) {
  const [state, setState] = useState({ topics: [], results: [] }),
    [hours, setHours] = useState(24);
  const refresh = () =>
    request("/tracking")
      .then(setState)
      .catch((e) => notify(e.message, true));
  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 15000);
    return () => clearInterval(t);
  }, []);
  const set = async (topic, enabled = true, interval_hours = hours) => {
    try {
      await request("/tracking", { topic, enabled, interval_hours }, "PUT");
      await refresh();
    } catch (e) {
      notify(e.message, true);
    }
  };
  return (
    <section className="card tracking-panel">
      <div className="panel-top">
        <h3>定期追踪与更新收件箱</h3>
        <span>{state.results.filter((x) => x.is_new).length} 条未读</span>
      </div>
      <div className="button-row">
        <label>
          刷新间隔{" "}
          <select
            aria-label="追踪间隔"
            value={hours}
            onChange={(e) => setHours(+e.target.value)}
          >
            {[1, 6, 12, 24, 48, 168].map((v) => (
              <option key={v} value={v}>
                {v} 小时
              </option>
            ))}
          </select>
        </label>
        <button
          className="button secondary small"
          disabled={query.trim().length < 2}
          onClick={() => set(query.trim())}
        >
          定期追踪当前主题
        </button>
        <button
          className="text-button"
          onClick={async () => {
            try {
              await request("/tracking/refresh", {});
              notify("后台刷新已启动");
            } catch (e) {
              notify(e.message, true);
            }
          }}
        >
          立即检查更新
        </button>
        <button
          className="text-button"
          onClick={() => {
            onResults(state.results);
            request("/tracking/read", {})
              .then(refresh)
              .catch((e) => notify(e.message, true));
          }}
        >
          查看更新结果
        </button>
      </div>
      {state.topics.map((t) => (
        <div className="tracking-topic" key={t.topic}>
          <b>{t.topic}</b>
          <span>
            每 {t.interval_hours} 小时 ·{" "}
            {t.last_run
              ? new Date(t.last_run).toLocaleString()
              : "等待首次检查"}
          </span>
          <button
            className="text-button"
            onClick={() => set(t.topic, !t.enabled, t.interval_hours)}
          >
            {t.enabled ? "暂停" : "恢复"}
          </button>
          {t.error && (
            <small className="error-text">
              上次失败，15 分钟后重试：{t.error}
            </small>
          )}
        </div>
      ))}
      <small>
        服务运行时自动检查，关闭浏览器后仍继续。服务关闭时暂停，重启后补查到期主题；结果去重保存在本机。
      </small>
    </section>
  );
}

export function Diagram({ text }) {
  const el = useRef(),
    [error, setError] = useState("");
  useEffect(() => {
    let live = true;
    setError("");
    (async () => {
      try {
        const { default: m } = await import("mermaid");
        m.initialize({
          startOnLoad: false,
          securityLevel: "strict",
          theme: "neutral",
        });
        const code = text.replace(/^```(?:mermaid)?\s*|\s*```$/g, "").trim();
        const result = await m.render(
          "diagram" + Math.random().toString(36).slice(2),
          code,
        );
        if (live && el.current) el.current.innerHTML = result.svg;
      } catch {
        if (live) setError("结构图语法未通过渲染，请在下方修改代码。");
      }
    })();
    return () => {
      live = false;
    };
  }, [text]);
  return (
    <>
      <div ref={el} className="diagram-preview" />
      {error && <p>{error}</p>}
      <button
        className="text-button"
        onClick={() => {
          const svg = el.current?.querySelector("svg");
          if (svg) download("diagram.svg", svg.outerHTML, "image/svg+xml");
        }}
      >
        导出结构图 SVG
      </button>
    </>
  );
}

export function AdvancedChart({ notify }) {
  const [data, setData] = useState(null),
    [x, setX] = useState(""),
    [y, setY] = useState(""),
    [z, setZ] = useState(""),
    [type, setType] = useState("bar"),
    [title, setTitle] = useState("实验结果对比"),
    [busy, setBusy] = useState(false);
  const input = useRef(),
    plot = useRef(),
    plotly = useRef();
  const rows = data?.rows || [];
  const valid =
    data && y && (type !== "scatter3d" || (data.numeric.includes(x) && z));
  useEffect(() => {
    let live = true;
    if (!valid) return;
    setBusy(true);
    (async () => {
      try {
        const { default: p } = await import("plotly.js-dist-min");
        if (!live) return;
        plotly.current = p;
        const a = rows.map((r) => r[x]),
          b = rows.map((r) => +r[y]);
        let trace;
        if (type === "radar")
          trace = {
            type: "scatterpolar",
            theta: [...a, a[0]],
            r: [...b, b[0]],
            fill: "toself",
            line: { color: "#247b6b" },
          };
        else if (type === "scatter3d")
          trace = {
            type: "scatter3d",
            x: a.map(Number),
            y: b,
            z: rows.map((r) => +r[z]),
            mode: "markers",
            marker: { color: b, colorscale: "Viridis", size: 5 },
          };
        else
          trace = {
            type: type === "bar" ? "bar" : "scatter",
            x: a,
            y: b,
            mode: type === "scatter" ? "markers" : "lines+markers",
            marker: { color: "#247b6b" },
          };
        await p.react(
          plot.current,
          [trace],
          {
            title: { text: title },
            xaxis: { title: { text: x } },
            yaxis: { title: { text: y } },
            scene: {
              xaxis: { title: { text: x } },
              yaxis: { title: { text: y } },
              zaxis: { title: { text: z } },
            },
            margin: { t: 70, l: 65, r: 30, b: 70 },
            paper_bgcolor: "#fff",
            font: { family: "Microsoft YaHei", color: "#23464a" },
            autosize: true,
          },
          { responsive: true, displaylogo: false },
        );
      } catch (e) {
        if (live) notify("图表渲染失败：" + e.message, true);
      } finally {
        if (live) setBusy(false);
      }
    })();
    return () => {
      live = false;
    };
  }, [data, x, y, z, type, title]);
  useEffect(
    () => () => {
      if (plotly.current && plot.current) plotly.current.purge(plot.current);
    },
    [],
  );
  const code = `import pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\ndf = pd.read_csv('your-data.csv')\n${type === "radar" ? `fig = go.Figure(go.Scatterpolar(theta=df[${JSON.stringify(x)}], r=df[${JSON.stringify(y)}], fill='toself'))` : `fig = px.${type === "line" ? "line" : type === "scatter3d" ? "scatter_3d" : type}(df, x=${JSON.stringify(x)}, y=${JSON.stringify(y)}${type === "scatter3d" ? ", z=" + JSON.stringify(z) : ""})`}\nfig.update_layout(title=${JSON.stringify(title)})\nfig.write_html('figure.html')\nfig.show()\n`;
  const tikz = `% Requires pgfplots; uploaded numeric data only\n\\begin{tikzpicture}\n\\begin{axis}[${type === "bar" ? "ybar," : ""}xlabel={X},ylabel={Y}${type === "scatter3d" ? ",zlabel={Z}" : ""}]\n\\addplot${type === "scatter3d" ? "3" : ""} coordinates {${rows.map((r, i) => (type === "scatter3d" ? `(${+r[x]},${+r[y]},${+r[z]})` : `(${data?.numeric.includes(x) ? +r[x] : i + 1},${+r[y]})`)).join(" ")}};\n\\end{axis}\n\\end{tikzpicture}`;
  return (
    <div className="chart-layout">
      <div className="card chart-controls">
        <h3>从数据到图表</h3>
        <input
          ref={input}
          hidden
          type="file"
          accept=".csv"
          onChange={async (e) => {
            if (!e.target.files[0]) return;
            try {
              const b = new FormData();
              b.append("file", e.target.files[0]);
              const r = await fetch("/api/csv", { method: "POST", body: b });
              const d = await r.json();
              if (!r.ok) throw new Error(d.detail);
              setData(d);
              setX(d.columns[0]);
              setY(
                d.numeric.find((c) => c !== d.columns[0]) || d.numeric[0] || "",
              );
              setZ(d.numeric[2] || d.numeric[0] || "");
            } catch (e) {
              notify(e.message, true);
            }
          }}
        />
        <button
          className="button secondary"
          onClick={() => input.current.click()}
        >
          上传 CSV
        </button>
        <small>最多 2000 行，使用全部有效数据。三维图须有三个数值轴。</small>
        {data && (
          <>
            <p>
              已读取 {data.count} 行、{data.columns.length} 列。
            </p>
            <label>
              图表标题
              <input
                aria-label="图表标题"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </label>
            {[
              ["X 轴", x, setX, data.columns],
              ["Y 轴", y, setY, data.numeric],
              ...(type === "scatter3d"
                ? [["Z 轴", z, setZ, data.numeric]]
                : []),
            ].map(([l, v, s, cols]) => (
              <label key={l}>
                {l}
                <select
                  aria-label={l}
                  value={v}
                  onChange={(e) => s(e.target.value)}
                >
                  {cols.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </label>
            ))}
            <label>
              图表类型
              <select
                aria-label="图表类型"
                value={type}
                onChange={(e) => setType(e.target.value)}
              >
                {[
                  ["bar", "柱状图"],
                  ["line", "折线图"],
                  ["scatter", "散点图"],
                  ["radar", "雷达图"],
                  ["scatter3d", "三维散点图"],
                ].map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}
        <button
          className="text-button"
          onClick={() =>
            download("sample.csv", "X,Y,Z\n1,72,180\n2,81,220\n3,86,240\n")
          }
        >
          下载 CSV 格式示例
        </button>
      </div>
      <div className="card chart-output">
        <div ref={plot} className="advanced-plot" />
        {!valid && <p>请上传 CSV 并选择有效数值轴。</p>}
        {busy && <p>正在渲染…</p>}
        {valid && (
          <>
            <div className="button-row">
              {["png", ...(type === "scatter3d" ? [] : ["svg"])].map(
                (format) => (
                  <button
                    className="text-button"
                    key={format}
                    onClick={() =>
                      plotly.current
                        ?.downloadImage(plot.current, {
                          format,
                          filename: "figure",
                          width: 1600,
                          height: 1000,
                        })
                        .catch((e) => notify(e.message, true))
                    }
                  >
                    导出 {format.toUpperCase()}
                  </button>
                ),
              )}
              <button
                className="text-button"
                onClick={() => download("plot.py", code)}
              >
                下载 Python 代码
              </button>
              {type !== "radar" && (
                <button
                  className="text-button"
                  onClick={() => download("figure.tex", tikz)}
                >
                  导出 TikZ
                </button>
              )}
            </div>
            <p>
              图表包含上传数据的 {rows.length}{" "}
              条记录；未推断统计显著性。雷达图不自动归一化，比较前应统一量纲。
            </p>
            <details>
              <summary>可复现代码</summary>
              <pre>{code}</pre>
            </details>
          </>
        )}
      </div>
    </div>
  );
}
