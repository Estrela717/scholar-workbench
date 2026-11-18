import React, { useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import {
  BookOpen,
  Library,
  MessagesSquare,
  Compass,
  Network,
  PenLine,
  Settings,
  Plus,
  Search,
  ArrowUpRight,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Upload,
  FileText,
  Star,
  MoreHorizontal,
  Check,
  CheckCircle2,
  AlertCircle,
  Loader2,
  X,
  Trash2,
  Download,
  ExternalLink,
  Quote,
  Sparkles,
  Send,
  Languages,
  PanelLeftClose,
  RefreshCw,
  Link2,
  BarChart3,
  Database,
  FolderOpen,
  Clock,
  Command,
  Layers,
  ScanText,
  ShieldCheck,
  Copy,
  Menu,
} from "lucide-react";
import "./style.css";
import {
  FormulaCard,
  TrackingPanel,
  Diagram,
  AdvancedChart,
} from "./research-tools.jsx";

async function api(path, options = {}) {
  const response = await fetch("/api" + path, options);
  if (!response.ok) {
    let message;
    try {
      message = (await response.json()).detail;
    } catch {
      message = response.statusText;
    }
    throw new Error(
      typeof message === "string" ? message : JSON.stringify(message),
    );
  }
  return response.json();
}
const post = (path, data) =>
  api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
const labels = {
  library: "文献库",
  reader: "沉浸阅读",
  ask: "文献问答",
  discover: "发现论文",
  graph: "引用图谱",
  write: "写作工坊",
  settings: "工作台设置",
};
const modes = {
  hybrid: "混合检索",
  keyword: "关键词检索",
  keyword_fallback: "关键词检索",
  representative: "代表性段落",
  extractive: "原文摘录",
  citation_rejected: "引用待核验",
  no_evidence: "暂无证据",
};
const nav = [
  ["library", Library],
  ["reader", BookOpen],
  ["ask", MessagesSquare],
  ["discover", Compass],
  ["graph", Network],
  ["write", PenLine],
];
const statusName = {
  ready: "已就绪",
  queued: "等待解析",
  parsing: "解析中",
  indexing: "索引中",
  error: "解析失败",
  interrupted: "已中断",
};
const short = (value, length = 70) =>
  value?.length > length ? value.slice(0, length) + "…" : value;
function saveFile(name, text, type = "text/plain;charset=utf-8") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function App() {
  const [tab, setTab] = useState("library"),
    [docs, setDocs] = useState([]),
    [stats, setStats] = useState(null),
    [query, setQuery] = useState("");
  const [active, setActive] = useState(null),
    [page, setPage] = useState(1),
    [highlight, setHighlight] = useState(null),
    [toast, setToast] = useState(null),
    [uploading, setUploading] = useState(false),
    [uploadOpen, setUploadOpen] = useState(false),
    [mobile, setMobile] = useState(false);
  const uploadRef = useRef();
  const notify = (message, error = false) =>
    setToast({ message, error, id: Date.now() });
  async function refresh() {
    try {
      const d = await api("/documents");
      setDocs(d);
      setStats(await api("/status"));
    } catch (error) {
      notify("无法连接本地服务：" + error.message, true);
    }
  }
  useEffect(() => {
    refresh();
    const timer = setInterval(() => {
      api("/documents")
        .then(setDocs)
        .catch(() => {});
    }, 3500);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 6500);
      return () => clearTimeout(timer);
    }
  }, [toast]);
  function openSource(source) {
    setActive(source.doc_id);
    setPage(source.page || 1);
    setHighlight(source.id || null);
    setTab("reader");
  }
  async function upload(files) {
    setUploading(true);
    for (const file of Array.from(files)) {
      try {
        const body = new FormData();
        body.append("file", file);
        const r = await api("/documents", { method: "POST", body });
        notify(
          r.duplicate
            ? "这份文件已在文献库中"
            : "已导入 " + file.name + "，正在后台解析",
        );
        setActive(r.document.id);
      } catch (e) {
        notify(e.message, true);
      }
    }
    setUploading(false);
    setUploadOpen(false);
    refresh();
  }
  const selected = docs.find((d) => d.id === active);
  const ready = docs.filter((d) => d.status === "ready");
  const context = {
    docs,
    ready,
    active,
    setActive,
    page,
    setPage,
    highlight,
    setHighlight,
    openSource,
    notify,
    refresh,
    stats,
  };
  return (
    <div className="app-shell">
      <aside className={"sidebar " + (mobile ? "show" : "")}>
        <div className="brand">
          <div className="brand-mark">
            <Layers size={23} />
          </div>
          <div>
            <strong>
              知研<span> WORKSPACE</span>
            </strong>
            <small>让每个洞察，都有出处</small>
          </div>
        </div>
        <button className="workspace-switch">
          <span className="workspace-avatar">研</span>
          <div>
            <b>我的研究空间</b>
            <small>本地工作台</small>
          </div>
          <ChevronDown size={15} />
        </button>
        <div className="nav-label">研究工作流</div>
        <nav>
          {nav.map(([key, Icon]) => (
            <button
              key={key}
              className={tab === key ? "active" : ""}
              onClick={() => {
                setTab(key);
                setMobile(false);
              }}
            >
              <Icon size={19} />
              <span>{labels[key]}</span>
              {key === "library" && <em>{docs.length}</em>}
              {key === tab && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <div className="orbit">
            <Network size={30} />
          </div>
          <b>从一篇论文，到一个洞察</b>
          <p>
            连接文献、证据与灵感，
            <br />
            在自己的电脑上展开研究。
          </p>
          <span>
            <ShieldCheck size={13} /> 文献默认保存在本机
          </span>
        </div>
        <div className="sidebar-bottom">
          <button
            onClick={() => setTab("settings")}
            className={tab === "settings" ? "active" : ""}
          >
            <Settings size={18} />
            工作台设置
          </button>
          <div className="profile">
            <div className="profile-avatar">R</div>
            <div>
              <b>独立研究者</b>
              <small>LOCAL WORKSPACE</small>
            </div>
            <span className="online-dot" />
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="mobile-menu icon-btn"
              onClick={() => setMobile(!mobile)}
            >
              <Menu size={20} />
            </button>
            <span>研究空间</span>
            <ChevronRight size={13} />
            <b>{labels[tab]}</b>
          </div>
          <div className="top-actions">
            <span className="local-chip">
              <span
                className={
                  stats?.model.available ? "online-dot" : "offline-dot"
                }
              />
              {stats?.model.available ? "本地模型已连接" : "检查模型连接"}
            </span>
            <button className="icon-btn" title="刷新状态" onClick={refresh}>
              <RefreshCw size={16} />
            </button>
            <div className="avatar-small">研</div>
          </div>
        </header>
        <main
          className={tab === "reader" ? "content reading-content" : "content"}
        >
          {tab === "library" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">YOUR RESEARCH, CONNECTED</div>
                  <h1>把文献，变成知识。</h1>
                  <p>收集值得读的论文，找到有据可循的答案。</p>
                </div>
                <button
                  className="button primary"
                  onClick={() => setUploadOpen(true)}
                >
                  <Plus size={18} />
                  导入文献
                </button>
              </div>
              <div className="welcome-grid">
                <div className="research-banner">
                  <div className="banner-copy">
                    <span className="pill">LOCAL-FIRST RESEARCH</span>
                    <h2>
                      下一次发现，
                      <br />
                      从一个好问题开始。
                    </h2>
                    <p>跨文献检索与原文溯源，让研究思路连起来。</p>
                    <button onClick={() => setTab("ask")}>
                      开始文献问答 <ArrowRight size={16} />
                    </button>
                  </div>
                  <div className="banner-art" aria-hidden="true">
                    <div className="ring ring-one" />
                    <div className="ring ring-two" />
                    <div className="art-paper paper-back">
                      <div />
                      <div />
                      <div />
                    </div>
                    <div className="art-paper paper-front">
                      <span>
                        <Quote size={21} />
                      </span>
                      <div />
                      <div />
                      <div className="art-chart">
                        <i />
                        <i />
                        <i />
                        <i />
                        <i />
                      </div>
                      <b>
                        EVERY INSIGHT.
                        <br />A SOURCE.
                      </b>
                    </div>
                    <div className="floating-node node-a">
                      <Network size={19} />
                    </div>
                    <div className="floating-node node-b">
                      <Sparkles size={18} />
                    </div>
                  </div>
                </div>
                <div className="stats-card">
                  <div className="section-kicker">
                    研究积累 <Database size={15} />
                  </div>
                  <div className="stat-main">
                    <strong>{docs.length.toString().padStart(2, "0")}</strong>
                    <span>篇文献已收集</span>
                  </div>
                  <div className="stat-row">
                    <span>已解析页数</span>
                    <b>{docs.reduce((a, d) => a + d.page_count, 0)}</b>
                  </div>
                  <div className="stat-row">
                    <span>可检索内容块</span>
                    <b>{docs.reduce((a, d) => a + d.chunk_count, 0)}</b>
                  </div>
                  <div className="stats-footer">
                    <span className="online-dot" />
                    数据仅存储在本地
                  </div>
                </div>
              </div>
              <div className="library-heading">
                <div className="tab-underline">
                  <b>
                    全部文献 <span>{docs.length}</span>
                  </b>
                </div>
                <div className="search-box">
                  <Search size={16} />
                  <input
                    placeholder="搜索标题、作者或文件名"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                  {query && (
                    <button className="icon-btn" onClick={() => setQuery("")}>
                      <X size={14} />
                    </button>
                  )}
                </div>
              </div>
              <LibraryTable
                {...context}
                query={query}
                onImport={() => setUploadOpen(true)}
              />
              <div className="quick-links">
                <button onClick={() => setTab("discover")}>
                  <div className="quick-icon sage">
                    <Compass size={21} />
                  </div>
                  <div>
                    <b>发现研究前沿</b>
                    <p>检索 arXiv，连接新的研究线索</p>
                  </div>
                  <ArrowUpRight size={18} />
                </button>
                <button onClick={() => setTab("graph")}>
                  <div className="quick-icon lavender">
                    <Network size={21} />
                  </div>
                  <div>
                    <b>看见文献间的联系</b>
                    <p>从引用关系中识别关键论文</p>
                  </div>
                  <ArrowUpRight size={18} />
                </button>
              </div>
            </>
          )}
          {tab === "reader" && <Reader {...context} />}
          {tab === "ask" && <QuestionSpace {...context} />}
          {tab === "discover" && <Discover {...context} />}
          {tab === "graph" && <GraphSpace {...context} />}
          {tab === "write" && <WritingSpace {...context} />}
          {tab === "settings" && <SettingsSpace {...context} />}
          <footer className="page-footer">
            <span>知研 · Scholar Workbench</span>
            <span>阅读有方向 · 回答有依据</span>
          </footer>
        </main>
      </div>
      <input
        ref={uploadRef}
        type="file"
        accept="application/pdf,.pdf"
        multiple
        hidden
        onChange={(e) => {
          upload(e.target.files);
          e.target.value = "";
        }}
      />
      {uploadOpen && (
        <div
          className="modal-backdrop"
          onClick={() => !uploading && setUploadOpen(false)}
        >
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">
              <h2>添加到文献库</h2>
              <button
                className="icon-btn"
                disabled={uploading}
                onClick={() => setUploadOpen(false)}
              >
                <X />
              </button>
            </div>
            <p className="muted">
              支持论文、扫描件与长篇文档。文件保存在你的电脑上。
            </p>
            <div
              className="dropzone"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                upload(e.dataTransfer.files);
              }}
              onClick={() => !uploading && uploadRef.current.click()}
            >
              {uploading ? (
                <Loader2 className="spin" size={35} />
              ) : (
                <Upload size={35} />
              )}
              <b>
                {uploading ? "正在导入文献…" : "拖放 PDF 到这里，或点击选择"}
              </b>
              <span>支持批量上传 · 单个文件最大 60 MB</span>
            </div>
            <div className="info-line">
              <ShieldCheck size={16} />
              原文位置会随解析保留，回答可以直接回溯证据。
            </div>
          </div>
        </div>
      )}
      {toast && (
        <div role="status" className={"toast " + (toast.error ? "error" : "")}>
          {toast.error ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)}>
            <X size={15} />
          </button>
        </div>
      )}
    </div>
  );
}

function Empty({ icon: Icon = FileText, title, description, action }) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <Icon size={30} />
      </div>
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}
function PageTitle({ eyebrow, title, description, children }) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {children}
    </div>
  );
}
function Busy({ text = "正在处理，请稍候…" }) {
  return (
    <div className="busy">
      <Loader2 size={20} className="spin" />
      <span>{text}</span>
    </div>
  );
}
function LibraryTable({ docs, query, openSource, notify, refresh, onImport }) {
  const filtered = docs.filter((d) =>
    (d.title + " " + d.authors + " " + d.filename)
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  async function remove(d) {
    if (!window.confirm("删除《" + d.title + "》及其本地解析数据？")) return;
    try {
      await api("/documents/" + d.id, { method: "DELETE" });
      refresh();
    } catch (e) {
      notify(e.message, true);
    }
  }
  return (
    <div className="library-panel">
      {!filtered.length ? (
        <Empty
          icon={Library}
          title={docs.length ? "没有匹配的文献" : "你的研究，从第一篇文献开始"}
          description={
            docs.length
              ? "换一个标题、作者或文件名试试。"
              : "导入 PDF 后，即可阅读、检索和连接文献。"
          }
          action={
            !docs.length && (
              <button className="button secondary" onClick={onImport}>
                <Plus size={16} />
                导入第一篇文献
              </button>
            )
          }
        />
      ) : (
        <table className="document-table">
          <thead>
            <tr>
              <th>文献信息</th>
              <th>页数</th>
              <th>处理状态</th>
              <th>添加日期</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {filtered.map((d) => (
              <tr key={d.id}>
                <td>
                  <div className="doc-cell">
                    <div className="pdf-icon">
                      <FileText size={22} />
                      <span>PDF</span>
                    </div>
                    <button
                      className="doc-title"
                      onClick={() => openSource({ doc_id: d.id, page: 1 })}
                    >
                      <b>{d.title}</b>
                      <small>
                        {d.authors ? short(d.authors, 80) : d.filename}
                      </small>
                      {d.arxiv_id && (
                        <span className="metadata-tag">arXiv:{d.arxiv_id}</span>
                      )}
                    </button>
                  </div>
                </td>
                <td>{d.page_count || "—"}</td>
                <td>
                  <span className={"status-badge " + d.status}>
                    {["queued", "parsing", "indexing"].includes(d.status) ? (
                      <Loader2 className="spin" size={12} />
                    ) : d.status === "ready" ? (
                      <Check size={12} />
                    ) : (
                      <AlertCircle size={12} />
                    )}{" "}
                    {statusName[d.status] || d.status}
                    {["parsing", "indexing"].includes(d.status) &&
                      " " + d.progress + "%"}
                  </span>
                  {d.error && (
                    <small className="row-error" title={d.error}>
                      {short(d.error, 32)}
                    </small>
                  )}
                </td>
                <td>
                  {new Date(d.created_at).toLocaleDateString("zh-CN", {
                    month: "2-digit",
                    day: "2-digit",
                  })}
                </td>
                <td>
                  <div className="row-actions">
                    <button
                      className={"icon-btn " + (d.starred ? "starred" : "")}
                      title="收藏文献"
                      onClick={async () => {
                        await post("/documents/" + d.id + "/star", {});
                        refresh();
                      }}
                    >
                      <Star
                        size={16}
                        fill={d.starred ? "currentColor" : "none"}
                      />
                    </button>
                    <button
                      className="icon-btn"
                      title="删除文献"
                      onClick={() => remove(d)}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function DocSelector({ docs, value, onChange, multiple = false }) {
  return (
    <div className="doc-selector">
      {multiple ? (
        <div className="doc-chips">
          {docs.map((d) => (
            <button
              key={d.id}
              className={value.includes(d.id) ? "selected" : ""}
              onClick={() =>
                onChange(
                  value.includes(d.id)
                    ? value.filter((x) => x !== d.id)
                    : [...value, d.id],
                )
              }
            >
              {value.includes(d.id) ? (
                <Check size={13} />
              ) : (
                <FileText size={13} />
              )}{" "}
              {short(d.title, 36)}
            </button>
          ))}
          {!docs.length && <span className="muted">请先导入并解析文献</span>}
        </div>
      ) : (
        <select value={value || ""} onChange={(e) => onChange(e.target.value)}>
          <option value="">选择一篇文献</option>
          {docs.map((d) => (
            <option key={d.id} value={d.id}>
              {d.title}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}

function Reader({
  docs,
  active,
  setActive,
  page,
  setPage,
  highlight,
  setHighlight,
  notify,
  refresh,
}) {
  const [detail, setDetail] = useState(null),
    [data, setData] = useState(null),
    [loading, setLoading] = useState(false),
    [translating, setTranslating] = useState(null),
    [view, setView] = useState("translation"),
    [selectedText, setSelectedText] = useState(""),
    [textResult, setTextResult] = useState(""),
    [structures, setStructures] = useState(null),
    [returnSpot, setReturnSpot] = useState(null),
    [fullTranslation, setFullTranslation] = useState(null);
  useEffect(() => {
    if (!active) return;
    let live = true;
    const load = () =>
      api(`/documents/${active}/translation`)
        .then((job) => live && setFullTranslation(job))
        .catch(() => {});
    load();
    const timer = setInterval(load, 4000);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [active]);
  const translationRef = useRef(),
    imageRef = useRef(),
    syncGuard = useRef(0);
  useEffect(() => {
    setStructures(null);
    if (view === "structures" && active && detail?.page_count) {
      api(`/documents/${active}/pages/${page}/structures`)
        .then(setStructures)
        .catch((e) => notify(e.message, true));
    }
  }, [view, active, page, detail?.page_count]);
  useEffect(() => {
    if (!active && docs.length) setActive(docs[0].id);
  }, [active, docs]);
  useEffect(() => {
    let valid = true;
    setDetail(null);
    if (active)
      api("/documents/" + active)
        .then((value) => valid && setDetail(value))
        .catch((e) => notify(e.message, true));
    return () => {
      valid = false;
    };
  }, [active, docs.find((d) => d.id === active)?.status]);
  useEffect(() => {
    let valid = true;
    setData(null);
    setTextResult("");
    if (active && detail?.page_count) {
      setLoading(true);
      api(`/documents/${active}/pages/${page}`)
        .then((value) => valid && setData(value))
        .catch((e) => notify(e.message, true))
        .finally(() => valid && setLoading(false));
    }
    return () => {
      valid = false;
    };
  }, [active, page, detail?.page_count]);
  useEffect(() => {
    if (highlight && data) {
      document
        .getElementById("chunk-" + highlight)
        ?.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }, [data, highlight]);
  async function translate(chunk) {
    setTranslating(chunk.id);
    try {
      const r = await post("/translate", { chunk_id: chunk.id });
      setData((prev) =>
        prev?.chunks
          ? {
              ...prev,
              chunks: prev.chunks.map((c) =>
                c.id === chunk.id ? { ...c, translation: r.text } : c,
              ),
            }
          : prev,
      );
    } catch (e) {
      notify(e.message, true);
    } finally {
      setTranslating(null);
    }
  }
  async function translatePage() {
    if (!data) return;
    for (const chunk of data.chunks.filter((c) => !c.translation)) {
      setTranslating(chunk.id);
      try {
        const r = await post("/translate", { chunk_id: chunk.id });
        setData((prev) =>
          prev?.chunks
            ? {
                ...prev,
                chunks: prev.chunks.map((c) =>
                  c.id === chunk.id ? { ...c, translation: r.text } : c,
                ),
              }
            : prev,
        );
      } catch (e) {
        notify(e.message, true);
        break;
      }
    }
    setTranslating(null);
  }
  async function translateSelection() {
    setTranslating("selection");
    try {
      setTextResult((await post("/translate", { text: selectedText })).text);
    } catch (e) {
      notify(e.message, true);
    } finally {
      setTranslating(null);
    }
  }
  function jump(p, id) {
    setPage(p);
    setHighlight(id || null);
  }
  function syncScroll(from, to) {
    if (
      view !== "translation" ||
      Date.now() < syncGuard.current ||
      !from ||
      !to ||
      from.scrollHeight <= from.clientHeight
    )
      return;
    syncGuard.current = Date.now() + 80;
    to.scrollTop =
      (from.scrollTop / (from.scrollHeight - from.clientHeight)) *
      Math.max(0, to.scrollHeight - to.clientHeight);
  }
  if (!docs.length)
    return (
      <>
        <PageTitle
          eyebrow="READ WITH CONTEXT"
          title="把注意力，留给内容。"
          description="对照原文、追踪引用，让阅读更深入。"
        />
        <Empty
          icon={BookOpen}
          title="还没有可阅读的文献"
          description="在文献库中导入 PDF，即可开始阅读。"
        />
      </>
    );
  return (
    <>
      <div className="reader-title">
        <div>
          <span className="eyebrow">IMMERSIVE READING</span>
          <h2>{short(detail?.title || "选择文献", 95)}</h2>
        </div>
        <a
          className="button secondary small"
          href={active ? "/api/documents/" + active + "/file" : "#"}
          target="_blank"
          rel="noreferrer"
        >
          <ExternalLink size={15} />
          原始 PDF
        </a>
        <a
          className="button secondary small"
          href={
            active ? "/api/documents/" + active + "/translation/export" : "#"
          }
        >
          导出译文 Markdown
        </a>
      </div>
      <div className="reader-controls">
        <DocSelector
          docs={docs}
          value={active}
          onChange={(id) => {
            setActive(id);
            setPage(1);
            setHighlight(null);
          }}
        />
        <div className="pagination">
          <button
            className="icon-btn"
            disabled={page <= 1}
            onClick={() => jump(page - 1)}
          >
            <ChevronLeft size={17} />
          </button>
          <input
            aria-label="页码"
            type="number"
            min="1"
            max={detail?.page_count || 1}
            value={page}
            onChange={(e) =>
              jump(
                Math.max(
                  1,
                  Math.min(
                    detail?.page_count || 1,
                    Number(e.target.value) || 1,
                  ),
                ),
              )
            }
          />
          <span>/ {detail?.page_count || "—"}</span>
          <button
            className="icon-btn"
            disabled={page >= (detail?.page_count || 1)}
            onClick={() => jump(page + 1)}
          >
            <ChevronRight size={17} />
          </button>
        </div>
        <div className="segmented">
          <button
            className={view === "translation" ? "selected" : ""}
            onClick={() => setView("translation")}
          >
            <Languages size={14} />
            对照阅读
          </button>
          <button
            className={view === "references" ? "selected" : ""}
            onClick={() => setView("references")}
          >
            <Link2 size={14} />
            参考文献
          </button>
          <button
            className={view === "outline" ? "selected" : ""}
            onClick={() => setView("outline")}
          >
            目录
          </button>
          <button
            className={view === "structures" ? "selected" : ""}
            onClick={() => setView("structures")}
          >
            图表与公式
          </button>
        </div>
      </div>
      {detail?.duplicates?.length > 0 && (
        <div className="warning-inline">
          <AlertCircle size={16} />
          发现可能的文献版本：
          {detail.duplicates
            .map((d) => d.title + "（" + d.reason + "）")
            .join("、")}
          。
          {detail.duplicates
            .filter((d) => !detail.metadata?.kept_versions?.includes(d.id))
            .map((d) => (
              <span className="duplicate-actions" key={d.id}>
                <button
                  className="text-button"
                  onClick={async () => {
                    try {
                      await post(`/documents/${active}/resolve-duplicate`, {
                        other_id: d.id,
                        action: "keep",
                      });
                      setDetail(await api("/documents/" + active));
                      notify("已选择保留两个版本");
                    } catch (e) {
                      notify(e.message, true);
                    }
                  }}
                >
                  保留两个版本
                </button>
                <button
                  className="text-button"
                  onClick={async () => {
                    if (
                      !window.confirm(
                        "用当前文献替代另一个版本？这会删除另一个版本及其解析数据。",
                      )
                    )
                      return;
                    try {
                      await post(`/documents/${active}/resolve-duplicate`, {
                        other_id: d.id,
                        action: "replace",
                      });
                      setDetail(await api("/documents/" + active));
                      refresh();
                    } catch (e) {
                      notify(e.message, true);
                    }
                  }}
                >
                  保留当前，移除另一版本
                </button>
              </span>
            ))}
        </div>
      )}
      {detail?.status !== "ready" && detail?.status !== "indexing" ? (
        <Empty
          icon={ScanText}
          title={statusName[detail?.status] || "正在加载文献"}
          description={detail?.error || "文献解析完成后即可阅读。"}
          action={
            ["error", "interrupted"].includes(detail?.status) && (
              <button
                className="button secondary"
                onClick={async () => {
                  await post("/documents/" + active + "/parse", {});
                  refresh();
                }}
              >
                重新解析
              </button>
            )
          }
        />
      ) : (
        <div className="reader-panels">
          <div className="original-panel">
            <div className="panel-top">
              <span>
                <FileText size={15} />
                原文 · 第 {page} 页
              </span>
              <span className="muted">点击高亮块定位段落</span>
            </div>
            <div
              className="pdf-scroll"
              ref={imageRef}
              onScroll={() =>
                syncScroll(imageRef.current, translationRef.current)
              }
            >
              {loading ? (
                <Busy text="正在加载这一页…" />
              ) : (
                data && (
                  <div
                    className="pdf-page"
                    style={{ aspectRatio: data.size[0] + "/" + data.size[1] }}
                  >
                    <img
                      src={`/api/documents/${active}/pages/${page}/image`}
                      alt={"论文原文第 " + page + " 页"}
                    />
                    {data.chunks.map((c) => (
                      <button
                        key={c.id}
                        title={short(c.text, 100)}
                        aria-label={"定位段落 " + c.id}
                        className={
                          "pdf-region " +
                          (highlight === c.id ? "highlighted" : "")
                        }
                        style={{
                          left: (c.bbox[0] / data.size[0]) * 100 + "%",
                          top: (c.bbox[1] / data.size[1]) * 100 + "%",
                          width:
                            ((c.bbox[2] - c.bbox[0]) / data.size[0]) * 100 +
                            "%",
                          height:
                            ((c.bbox[3] - c.bbox[1]) / data.size[1]) * 100 +
                            "%",
                        }}
                        onClick={() => {
                          setHighlight(c.id);
                          setView("translation");
                          setTimeout(
                            () =>
                              document
                                .getElementById("chunk-" + c.id)
                                ?.scrollIntoView({
                                  block: "center",
                                  behavior: "smooth",
                                }),
                            0,
                          );
                        }}
                      />
                    ))}
                  </div>
                )
              )}
            </div>
          </div>
          <div className="translation-panel">
            {view === "translation" && (
              <div className="full-translation-bar">
                <span>
                  {fullTranslation && fullTranslation.status !== "none"
                    ? `全文翻译 ${fullTranslation.completed}/${fullTranslation.total} · ${{ queued: "等待中", running: "进行中", done: "已完成", cancelled: "已停止", error: "出错", interrupted: "可继续" }[fullTranslation.status] || fullTranslation.status}`
                    : "译文逐段缓存，可随时继续"}
                </span>
                {["queued", "running"].includes(fullTranslation?.status) ? (
                  <button
                    className="text-button"
                    onClick={async () => {
                      await post(`/documents/${active}/translation/cancel`, {});
                      notify("将于当前段落完成后停止");
                    }}
                  >
                    停止
                  </button>
                ) : (
                  <button
                    className="text-button"
                    onClick={async () => {
                      try {
                        await post(`/documents/${active}/translation`, {});
                        setFullTranslation(
                          await api(`/documents/${active}/translation`),
                        );
                        notify(
                          "全文翻译已启动；长文档可能耗时较久，可停止后继续",
                        );
                      } catch (e) {
                        notify(e.message, true);
                      }
                    }}
                  >
                    全文翻译 / 继续
                  </button>
                )}
              </div>
            )}
            <div className="panel-top">
              <span>
                {view === "translation" ? (
                  <>
                    <Languages size={15} />
                    原文段落与译文
                  </>
                ) : view === "references" ? (
                  <>
                    <Quote size={15} />
                    参考文献
                  </>
                ) : view === "structures" ? (
                  <>图表与公式候选</>
                ) : (
                  <>文献目录</>
                )}
              </span>
              {view === "translation" && (
                <button
                  className="text-button"
                  disabled={!!translating}
                  onClick={translatePage}
                >
                  {translating ? (
                    <>
                      <Loader2 size={13} className="spin" />
                      翻译中
                    </>
                  ) : (
                    <>
                      翻译本页 <ArrowRight size={13} />
                    </>
                  )}
                </button>
              )}
            </div>
            <div
              className="translation-scroll"
              ref={translationRef}
              onScroll={() =>
                syncScroll(translationRef.current, imageRef.current)
              }
              onMouseUp={() =>
                setSelectedText(
                  window.getSelection()?.toString().slice(0, 5000) || "",
                )
              }
            >
              {returnSpot && (
                <button
                  className="text-button back-reference"
                  onClick={() => {
                    jump(returnSpot.page, returnSpot.id);
                    setReturnSpot(null);
                  }}
                >
                  <ChevronLeft size={14} />
                  返回正文引用位置
                </button>
              )}
              {view === "structures" &&
                (!structures ? (
                  <Busy text="正在识别本页结构…" />
                ) : (
                  <div className="structures">
                    <p className="helper-text">{structures.note}</p>
                    <h3>表格（{structures.tables.length}）</h3>
                    {structures.tables.map((table, i) => (
                      <div className="extracted-table" key={i}>
                        <div className="table-scroll">
                          <table>
                            <tbody>
                              {table.rows.map((row, j) => (
                                <tr key={j}>
                                  {row.map((cell, k) => (
                                    <td key={k}>{cell || "—"}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <button
                          className="text-button"
                          onClick={() =>
                            saveFile(
                              `table-page${page}-${i + 1}.csv`,
                              table.rows
                                .map((row) =>
                                  row
                                    .map(
                                      (cell) =>
                                        '"' +
                                        String(cell || "").replaceAll(
                                          '"',
                                          '""',
                                        ) +
                                        '"',
                                    )
                                    .join(","),
                                )
                                .join("\n"),
                              "text/csv;charset=utf-8",
                            )
                          }
                        >
                          <Download size={13} />
                          导出此表 CSV
                        </button>
                      </div>
                    ))}
                    {!structures.tables.length && (
                      <p className="muted">
                        没有自动识别到结构化表格，原始版式仍保留在左侧。
                      </p>
                    )}
                    <h3>公式候选（{structures.formula_candidates.length}）</h3>
                    {structures.formula_candidates.map((f) => (
                      <FormulaCard
                        key={f.id}
                        formula={f}
                        notify={notify}
                        locate={() => {
                          setHighlight(f.id);
                          setView("translation");
                        }}
                      />
                    ))}
                    <h3>嵌入图像（{structures.figures.length}）</h3>
                    <p className="muted">
                      图像保留在原始页面；矢量绘图不一定计为嵌入图像。
                    </p>
                  </div>
                ))}
              {view === "translation" && (
                <>
                  {selectedText && (
                    <div className="selection-bar">
                      <span>已选中 {selectedText.length} 字</span>
                      <button
                        disabled={!!translating}
                        className="text-button"
                        onClick={translateSelection}
                      >
                        翻译选中内容
                      </button>
                    </div>
                  )}
                  {textResult && (
                    <div className="translation-result">{textResult}</div>
                  )}
                  {data?.chunks.map((c) => (
                    <div
                      id={"chunk-" + c.id}
                      key={c.id}
                      className={
                        "chunk " + (highlight === c.id ? "focused" : "")
                      }
                      onClick={() => setHighlight(c.id)}
                    >
                      <div className="chunk-meta">
                        <span>
                          {c.kind === "heading"
                            ? "标题"
                            : c.kind === "reference"
                              ? "参考文献"
                              : c.kind === "ocr"
                                ? "OCR 识别"
                                : c.kind === "caption"
                                  ? "图表说明"
                                  : "原文段落"}
                        </span>
                        <button
                          className="icon-btn"
                          title="定位原文"
                          onClick={() => {
                            setHighlight(c.id);
                            imageRef.current
                              ?.querySelectorAll(".pdf-region")
                              [data.chunks.indexOf(c)]?.scrollIntoView({
                                block: "center",
                                behavior: "smooth",
                              });
                          }}
                        >
                          <ScanText size={14} />
                        </button>
                      </div>
                      <p className="chunk-original">{c.text}</p>
                      {c.translation ? (
                        <p className="chunk-translation">{c.translation}</p>
                      ) : (
                        <button
                          className="translate-button"
                          disabled={!!translating}
                          onClick={() => translate(c)}
                        >
                          {translating === c.id ? (
                            <Loader2 size={13} className="spin" />
                          ) : (
                            <Languages size={13} />
                          )}
                          翻译此段
                        </button>
                      )}
                      {/\[\d+\]/.test(c.text) && (
                        <div className="inline-refs">
                          {[...new Set(c.text.match(/\[(\d+)\]/g))]
                            .slice(0, 12)
                            .map((label) => {
                              const ref = detail.references?.find(
                                (r) => r.label === label.slice(1, -1),
                              );
                              return (
                                ref && (
                                  <button
                                    key={label}
                                    title={ref.text}
                                    onClick={() => {
                                      setReturnSpot({ page, id: c.id });
                                      jump(ref.page, ref.chunk_id);
                                    }}
                                  >
                                    参考文献 {label}
                                    <ArrowUpRight size={11} />
                                  </button>
                                )
                              );
                            })}
                        </div>
                      )}
                    </div>
                  ))}
                </>
              )}
              {view === "outline" &&
                (detail?.metadata?.headings?.length ? (
                  detail.metadata.headings.map((h, i) => (
                    <button
                      className="outline-item"
                      key={i}
                      onClick={() => jump(h.page)}
                    >
                      <span>{h.title}</span>
                      <em>{h.page}</em>
                    </button>
                  ))
                ) : (
                  <p className="muted">未识别到标题层级。</p>
                ))}
              {view === "references" &&
                (detail?.references?.length ? (
                  detail.references.map((r) => (
                    <div className="reference-item" key={r.id}>
                      <b>[{r.label}]</b>
                      <p>{r.text}</p>
                      <button
                        className="text-button"
                        onClick={() => jump(r.page, r.chunk_id)}
                      >
                        查看原文出处 <ArrowUpRight size={13} />
                      </button>
                      {r.target_doc_id && (
                        <button
                          className="text-button"
                          onClick={() => {
                            setActive(r.target_doc_id);
                            setPage(1);
                          }}
                        >
                          打开库中论文 <BookOpen size={13} />
                        </button>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="muted">
                    尚未识别参考文献列表；可在原始 PDF 中核对。
                  </p>
                ))}
            </div>
          </div>
        </div>
      )}
      {detail?.warnings?.length > 0 && (
        <details className="parse-warnings">
          <summary>解析提示（{detail.warnings.length}）</summary>
          {detail.warnings.map((w, i) => (
            <p key={i}>{w}</p>
          ))}
        </details>
      )}
    </>
  );
}

function AnswerText({ text, sources, onSource }) {
  return (
    <div className="answer-text">
      {text.split("\n").map((line, i) => (
        <p key={i}>
          {line.split(/(\[\d+\])/g).map((part, j) => {
            const match = part.match(/^\[(\d+)\]$/);
            return match && sources[+match[1] - 1] ? (
              <button
                className="citation"
                key={j}
                onClick={() => onSource(sources[+match[1] - 1])}
              >
                {match[1]}
              </button>
            ) : (
              <React.Fragment key={j}>
                {part.replace(/^#{1,4}\s/, "").replace(/\*\*/g, "")}
              </React.Fragment>
            );
          })}
        </p>
      ))}
    </div>
  );
}
function Sources({ sources, openSource }) {
  return (
    <div className="source-list">
      {sources.map((s, i) => (
        <button key={s.id || i} onClick={() => openSource(s)}>
          <span className="source-number">{i + 1}</span>
          <div>
            <b>{short(s.title, 65)}</b>
            <small>
              第 {s.page} 页 · {short(s.text.replace(/\s+/g, " "), 90)}
            </small>
          </div>
          <ArrowUpRight size={15} />
        </button>
      ))}
    </div>
  );
}

function QuestionSpace({ ready, notify, openSource }) {
  const [selected, setSelected] = useState([]),
    [question, setQuestion] = useState(""),
    [history, setHistory] = useState(() => {
      try {
        return JSON.parse(sessionStorage.getItem("scholar-chat") || "[]");
      } catch {
        return [];
      }
    }),
    [busy, setBusy] = useState(false),
    [searchOnly, setSearchOnly] = useState(false),
    [agent, setAgent] = useState(false);
  useEffect(() => {
    sessionStorage.setItem("scholar-chat", JSON.stringify(history.slice(-12)));
  }, [history]);
  async function ask(text = question) {
    if (!text.trim() || busy) return;
    setBusy(true);
    setQuestion("");
    try {
      const r = await post(searchOnly ? "/search" : "/ask", {
        query: text,
        doc_ids: selected,
        agent,
      });
      setHistory((prev) => [...prev, { question: text, ...r }]);
    } catch (e) {
      notify(e.message, true);
      setQuestion(text);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="ASK WITH EVIDENCE"
        title="让答案，回到原文。"
        description="对单篇或多篇文献提问，每条引用都能追溯。"
      />
      <div className="question-layout">
        <div className="chat-column">
          <div className="scope-panel">
            <span className="field-label">
              <Library size={15} />
              检索范围{" "}
              <small>
                {selected.length
                  ? "已选 " + selected.length + " 篇"
                  : "全部已解析文献"}
              </small>
            </span>
            <DocSelector
              multiple
              docs={ready}
              value={selected}
              onChange={setSelected}
            />
          </div>
          <div className="chat-history">
            {!history.length && !busy && (
              <div className="chat-welcome">
                <div className="ask-symbol">
                  <Sparkles size={30} />
                </div>
                <h2>带着问题读文献。</h2>
                <p>先检索，再生成。证据不足时，会明确告诉你。</p>
                <div className="prompt-grid">
                  {[
                    "总结这篇论文的主要贡献",
                    "论文使用了什么实验数据和评价指标？",
                    "对比这些论文的方法与局限",
                    "有哪些值得继续探索的研究方向？",
                  ].map((q) => (
                    <button key={q} onClick={() => setQuestion(q)}>
                      {q}
                      <ArrowUpRight size={14} />
                    </button>
                  ))}
                </div>
              </div>
            )}
            {history.map((h, i) => (
              <div className="chat-turn" key={i}>
                <div className="user-question">
                  <span>你</span>
                  <p>{h.question}</p>
                </div>
                <div className="assistant-answer">
                  <div className="assistant-label">
                    <span className="mini-brand">
                      <Layers size={15} />
                    </span>
                    <b>知研</b>
                    <em>{modes[h.mode] || h.mode}</em>
                  </div>
                  {h.answer ? (
                    <AnswerText
                      text={h.answer}
                      sources={h.sources || []}
                      onSource={openSource}
                    />
                  ) : (
                    <p className="muted">以下为检索到的原文片段。</p>
                  )}
                  {h.trace && (
                    <details className="trace">
                      <summary>查看检索与校验记录</summary>
                      {h.trace.map((t, j) => (
                        <div key={j}>
                          {t.status === "done" ? (
                            <CheckCircle2 size={14} />
                          ) : (
                            <AlertCircle size={14} />
                          )}
                          <b>{t.tool}</b>
                          <span>{t.detail}</span>
                        </div>
                      ))}
                    </details>
                  )}
                  <Sources sources={h.sources || []} openSource={openSource} />
                </div>
              </div>
            ))}
            {busy && (
              <Busy
                text={
                  searchOnly
                    ? "正在检索原文…"
                    : "本地模型正在处理，首次加载可能需要较长时间…"
                }
              />
            )}
          </div>
          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault();
              ask();
            }}
          >
            <textarea
              placeholder="输入你的研究问题，例如：这篇论文如何处理长距离依赖？"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  ask();
                }
              }}
            />
            <div className="composer-bottom">
              <label>
                <input
                  type="checkbox"
                  checked={searchOnly}
                  onChange={(e) => setSearchOnly(e.target.checked)}
                />
                仅检索原文
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={agent}
                  disabled={searchOnly}
                  onChange={(e) => setAgent(e.target.checked)}
                />
                智能体工具调用
              </label>
              <span>Enter 发送 · Shift + Enter 换行</span>
              <button
                className="send-button"
                disabled={busy || !question.trim() || !ready.length}
              >
                <Send size={17} />
              </button>
            </div>
          </form>
        </div>
        <aside className="right-info">
          <div className="info-card">
            <ShieldCheck size={24} />
            <h3>可核对的答案</h3>
            <p>
              回答中的数字角标连接到文献页码与原文段落。点击即可打开阅读器。
            </p>
            <div className="info-divider" />
            <b>更好的提问方式</b>
            <ul>
              <li>指明具体指标或实验设置</li>
              <li>选中两篇论文进行比较</li>
              <li>先建立语义索引，改善中英跨语言检索</li>
            </ul>
            <small>
              引用编号校验不等于事实核验。重要结论仍需回到原文确认。
            </small>
          </div>
        </aside>
      </div>
    </>
  );
}

function Discover({ notify, refresh }) {
  const [q, setQ] = useState(""),
    [results, setResults] = useState([]),
    [busy, setBusy] = useState(false),
    [importing, setImporting] = useState(null),
    [interests, setInterests] = useState([]),
    [searched, setSearched] = useState(false),
    [newest, setNewest] = useState(false);
  useEffect(() => {
    api("/settings")
      .then((s) => setInterests(s.interests || []))
      .catch(() => {});
  }, []);
  async function search(value = q) {
    if (!value.trim()) return;
    setQ(value);
    setBusy(true);
    try {
      const r = await api(
        "/discover?q=" + encodeURIComponent(value) + "&newest=" + newest,
      );
      setResults(r.results);
      setSearched(true);
    } catch (e) {
      notify(e.message, true);
    } finally {
      setBusy(false);
    }
  }
  async function follow() {
    if (!q.trim() || interests.includes(q.trim())) return;
    const next = [...interests, q.trim()].slice(-12);
    await api("/settings/interests", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ interests: next }),
    });
    setInterests(next);
    notify("研究兴趣已保存，点击兴趣标签即可刷新最新论文");
  }
  async function importPaper(p) {
    setImporting(p.id);
    try {
      const r = await post("/discover/import", { arxiv_id: p.id });
      notify(r.duplicate ? "文献已经在库中" : "已下载，正在解析");
      refresh();
    } catch (e) {
      notify(e.message, true);
    } finally {
      setImporting(null);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="FOLLOW YOUR CURIOSITY"
        title="发现下一篇，值得读的论文。"
        description="连接 arXiv，把新的研究线索带回文献库。"
      />
      <div className="discovery-search">
        <Compass size={25} />
        <form
          onSubmit={(e) => {
            e.preventDefault();
            search();
          }}
        >
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="输入研究主题、论文标题或关键词（英文更准确）"
          />
          <button className="button primary" disabled={busy || !q.trim()}>
            {busy ? (
              <Loader2 className="spin" size={17} />
            ) : (
              <Search size={17} />
            )}
            检索论文
          </button>
        </form>
      </div>
      <TrackingPanel
        query={q}
        notify={notify}
        onResults={(r) => {
          setResults(r);
          setSearched(true);
        }}
      />
      <div className="discovery-toolbar">
        <label>
          <input
            type="checkbox"
            checked={newest}
            onChange={(e) => setNewest(e.target.checked)}
          />
          按最新发表排序
        </label>
        <button className="text-button" onClick={follow} disabled={!q.trim()}>
          <Plus size={15} />
          追踪这个主题
        </button>
        <span>使用公开 arXiv 数据，需要网络连接</span>
      </div>
      <div className="interest-row">
        <span>研究兴趣</span>
        {interests.map((x) => (
          <button key={x} onClick={() => search(x)}>
            {x}
            <RefreshCw size={12} />
          </button>
        ))}
        {!interests.length && <small>保存你关心的主题，随时刷新研究动态</small>}
      </div>
      {busy ? (
        <Busy text="正在检索 arXiv…" />
      ) : !results.length ? (
        <Empty
          icon={Compass}
          title={searched ? "暂未找到匹配论文" : "让好奇心，带你走远一点"}
          description="试试 retrieval augmented generation、transformer 或你的研究领域。"
        />
      ) : (
        <div className="discovery-results">
          <div className="results-label">
            找到 {results.length} 篇论文{" "}
            <span>相关度为与本地文献的关键词重合度</span>
          </div>
          {results.map((p) => (
            <article className="paper-result" key={p.id}>
              <div className="paper-result-top">
                <span className="metadata-tag">arXiv · {p.id}</span>
                <span>{p.published}</span>
                {p.code_mentioned && (
                  <span className="code-badge">摘要提及代码</span>
                )}
              </div>
              <h2>
                <a href={p.url} target="_blank" rel="noreferrer">
                  {p.title}
                  <ArrowUpRight size={16} />
                </a>
              </h2>
              <p className="authors">{p.authors}</p>
              <p className="abstract">{p.abstract}</p>
              <div className="paper-result-bottom">
                <span>{p.recommendation_reason || "来自定期追踪结果"}</span>
                {[1, -1].map((v) => (
                  <button
                    className="text-button"
                    key={v}
                    onClick={async () => {
                      try {
                        await api("/discover/feedback", {
                          method: "PUT",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ arxiv_id: p.id, vote: v }),
                        });
                        notify("偏好已保存，将用于后续排序");
                      } catch (e) {
                        notify(e.message, true);
                      }
                    }}
                  >
                    {v === 1 ? "感兴趣" : "不感兴趣"}
                  </button>
                ))}
                <button
                  className="button secondary small"
                  disabled={!!importing}
                  onClick={() => importPaper(p)}
                >
                  {importing === p.id ? (
                    <Loader2 size={15} className="spin" />
                  ) : (
                    <Plus size={15} />
                  )}
                  加入文献库
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </>
  );
}

function GraphSpace({ docs, openSource, notify }) {
  const [graph, setGraph] = useState(null),
    [selected, setSelected] = useState(null);
  useEffect(() => {
    api("/graph")
      .then(setGraph)
      .catch((e) => notify(e.message, true));
  }, [docs.length]);
  if (!graph) return <Busy />;
  const sorted = [...graph.nodes].sort((a, b) => b.score - a.score);
  const positions = Object.fromEntries(
    graph.nodes.map((n, i) => {
      const angle =
        (i * 2 * Math.PI) / Math.max(graph.nodes.length, 1) - Math.PI / 2;
      const radius =
        graph.nodes.length === 1
          ? 0
          : Math.min(230, 140 + graph.nodes.length * 4);
      return [
        n.id,
        {
          x: 400 + Math.cos(angle) * radius,
          y: 300 + Math.sin(angle) * radius,
        },
      ];
    }),
  );
  const node = graph.nodes.find((n) => n.id === selected);
  return (
    <>
      <PageTitle
        eyebrow="SEE THE CONNECTIONS"
        title="让知识的关系，浮现出来。"
        description="从本地文献的真实引用出发，找到研究脉络。"
      >
        <span className="subtle-badge">
          {graph.nodes.length} 个节点 · {graph.edges.length} 条引用
        </span>
      </PageTitle>
      {!graph.nodes.length ? (
        <Empty
          icon={Network}
          title="图谱等待第一批文献"
          description="导入互有关联的论文后，系统会识别库内引用关系。"
        />
      ) : (
        <div className="graph-layout">
          <div className="graph-card">
            <div className="panel-top">
              <span>
                <Network size={16} />
                局域引用网络
              </span>
              <span className="muted">箭头：引用方 → 被引用方</span>
            </div>
            <svg
              className="graph-svg"
              viewBox="0 0 800 600"
              role="img"
              aria-label="本地文献引用关系图"
            >
              <defs>
                <pattern
                  id="dots"
                  width="22"
                  height="22"
                  patternUnits="userSpaceOnUse"
                >
                  <circle cx="1" cy="1" r="1" fill="#dce5e5" />
                </pattern>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="20"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#80a7a0" />
                </marker>
              </defs>
              <rect width="800" height="600" fill="url(#dots)" />
              {graph.edges.map((e, i) => {
                const a = positions[e.source],
                  b = positions[e.target];
                return (
                  a &&
                  b && (
                    <line
                      key={i}
                      x1={a.x}
                      y1={a.y}
                      x2={b.x}
                      y2={b.y}
                      stroke={
                        selected === e.source || selected === e.target
                          ? "#19776c"
                          : "#b5ccc6"
                      }
                      strokeWidth="2"
                      markerEnd="url(#arrow)"
                    />
                  )
                );
              })}
              {graph.nodes.map((n, i) => {
                const p = positions[n.id],
                  radius = 20 + Math.min(14, n.in_degree * 4);
                return (
                  <g
                    key={n.id}
                    className="graph-node"
                    onClick={() => setSelected(n.id)}
                    tabIndex="0"
                    role="button"
                    aria-label={n.title}
                    onKeyDown={(e) => e.key === "Enter" && setSelected(n.id)}
                  >
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r={radius + 9}
                      fill={selected === n.id ? "#cce6dd" : "#e8efec"}
                    />
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r={radius}
                      fill={["#286f66", "#779187", "#506c85", "#8f8070"][i % 4]}
                    />
                    <text
                      x={p.x}
                      y={p.y + 5}
                      textAnchor="middle"
                      fill="white"
                      fontSize="13"
                      fontWeight="600"
                    >
                      {i + 1}
                    </text>
                    <text
                      x={p.x}
                      y={p.y + radius + 30}
                      textAnchor="middle"
                      fill="#374d56"
                      fontSize="12"
                    >
                      {short(n.title, 35)}
                    </text>
                  </g>
                );
              })}
            </svg>
            {!graph.edges.length && (
              <p className="graph-note">
                当前尚未匹配到库内引用边。相邻摆放不代表论文之间存在引用。
              </p>
            )}
          </div>
          <aside className="graph-side">
            <div className="info-card">
              <span className="section-kicker">
                {node ? "所选文献" : "局域核心文献"}
              </span>
              {node ? (
                <>
                  <h3>{node.title}</h3>
                  <p>
                    库内被引 {node.in_degree} 次 · 引用库内 {node.out_degree} 篇
                  </p>
                  <button
                    className="button secondary small"
                    onClick={() => openSource({ doc_id: node.id, page: 1 })}
                  >
                    打开文献 <ArrowUpRight size={14} />
                  </button>
                </>
              ) : (
                sorted.slice(0, 6).map((n, i) => (
                  <button
                    className="rank-item"
                    key={n.id}
                    onClick={() => setSelected(n.id)}
                  >
                    <span>{i + 1}</span>
                    <div>
                      <b>{short(n.title, 55)}</b>
                      <small>
                        PageRank {n.score.toFixed(3)} · 库内被引 {n.in_degree}
                      </small>
                    </div>
                  </button>
                ))
              )}
              <div className="info-divider" />
              <p className="small-text">{graph.scope}</p>
            </div>
          </aside>
        </div>
      )}
    </>
  );
}

function WritingSpace({ ready, notify, openSource }) {
  const [mode, setMode] = useState("review"),
    [topic, setTopic] = useState(""),
    [selected, setSelected] = useState([]),
    [output, setOutput] = useState(null),
    [busy, setBusy] = useState(false),
    [notes, setNotes] = useState([]);
  useEffect(() => {
    api("/notes")
      .then(setNotes)
      .catch(() => {});
  }, []);
  const choices = [
    ["review", "文献综述"],
    ["outline", "论文框架"],
    ["future", "研究方向"],
    ["diagram", "结构图代码"],
    ["translate", "学术英译"],
    ["chart", "数据可视化"],
  ];
  async function generate() {
    setBusy(true);
    try {
      const r = await post("/write", { kind: mode, topic, doc_ids: selected });
      setOutput(r);
      setNotes(await api("/notes"));
    } catch (e) {
      notify(e.message, true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="TURN EVIDENCE INTO IDEAS"
        title="把研究，写下来。"
        description="从有来源的综述，到清晰的图表，让思路成为可编辑的成果。"
      />
      <div className="writing-tabs">
        {choices.map(([key, label]) => (
          <button
            key={key}
            className={mode === key ? "active" : ""}
            onClick={() => {
              setMode(key);
              setOutput(null);
            }}
          >
            {key === "chart" ? (
              <BarChart3 size={16} />
            ) : key === "translate" ? (
              <Languages size={16} />
            ) : (
              <PenLine size={16} />
            )}{" "}
            {label}
          </button>
        ))}
      </div>
      {mode === "chart" ? (
        <AdvancedChart notify={notify} />
      ) : (
        <div className="writing-layout">
          <div className="writing-input card">
            <h3>{choices.find((x) => x[0] === mode)?.[1]}</h3>
            <label className="field-label">
              {mode === "translate" ? "待翻译的中文学术文本" : "写作主题与要求"}
            </label>
            <textarea
              className="writing-textarea"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder={
                mode === "translate"
                  ? "粘贴摘要或正文；翻译忠实于输入，不补充研究结果。"
                  : "例如：综述 Transformer 在序列建模中的核心改进，比较方法与局限。"
              }
            />
            {mode !== "translate" && (
              <>
                <label className="field-label">
                  选择参考文献 <small>不选则检索全部文献</small>
                </label>
                <DocSelector
                  multiple
                  docs={ready}
                  value={selected}
                  onChange={setSelected}
                />
              </>
            )}
            <button
              className="button primary full-width"
              disabled={
                busy || !topic.trim() || (mode !== "translate" && !ready.length)
              }
              onClick={generate}
            >
              {busy ? (
                <Loader2 size={16} className="spin" />
              ) : (
                <Sparkles size={16} />
              )}{" "}
              {busy ? "本地模型生成中…" : "生成草稿"}
            </button>
            <p className="helper-text">
              生成内容是可编辑草稿。使用前请核对引用、事实与学术表述。
            </p>
            {notes.length > 0 && (
              <div className="saved-notes">
                <b>最近草稿</b>
                {notes.slice(0, 5).map((n) => (
                  <button
                    key={n.id}
                    onClick={() =>
                      setOutput({
                        id: n.id,
                        text: n.text,
                        sources: JSON.parse(n.sources),
                        kind: "review",
                      })
                    }
                  >
                    <FileText size={14} />
                    {short(n.title, 35)}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="writing-output card">
            <div className="panel-top">
              <span>工作草稿</span>
              {output && (
                <button
                  className="text-button"
                  onClick={() =>
                    saveFile(
                      "知研-" + mode + ".md",
                      output.text +
                        "\n\n" +
                        (output.sources
                          ?.map((s, i) => `[${i + 1}] ${s.title}, p.${s.page}`)
                          .join("\n") || ""),
                    )
                  }
                >
                  <Download size={14} />
                  导出 Markdown
                </button>
              )}
            </div>
            {busy ? (
              <Busy text="正在基于文献证据组织草稿，请稍候…" />
            ) : output ? (
              <>
                {mode === "diagram" && <Diagram text={output.text} />}
                <details>
                  <summary>编辑草稿 / 结构图代码</summary>
                  <textarea
                    aria-label="编辑草稿"
                    className="writing-textarea"
                    value={output.text}
                    onChange={(e) =>
                      setOutput({ ...output, text: e.target.value })
                    }
                  />
                  {output.id && (
                    <button
                      className="button secondary"
                      onClick={async () => {
                        try {
                          await api("/notes/" + output.id, {
                            method: "PUT",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ text: output.text }),
                          });
                          notify("草稿已保存");
                        } catch (e) {
                          notify(e.message, true);
                        }
                      }}
                    >
                      保存草稿
                    </button>
                  )}
                </details>
                <AnswerText
                  text={output.text}
                  sources={output.sources || []}
                  onSource={openSource}
                />
                <Sources
                  sources={output.sources || []}
                  openSource={openSource}
                />
              </>
            ) : (
              <Empty
                icon={PenLine}
                title="让想法有一个起点"
                description="输入主题、选择文献，生成带原文依据的初稿。"
              />
            )}
          </div>
        </div>
      )}
    </>
  );
}

function SettingsSpace({ stats, docs, notify, refresh }) {
  const [indexing, setIndexing] = useState(null);
  async function index(d) {
    setIndexing(d.id);
    try {
      await post("/documents/" + d.id + "/index", {});
      notify("语义索引任务已启动，可在文献库查看进度");
      refresh();
    } catch (e) {
      notify(e.message, true);
    } finally {
      setIndexing(null);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="A WORKSPACE OF YOUR OWN"
        title="研究空间，由你掌控。"
        description="检查本地模型、语义索引与数据状态。"
      />
      <div className="settings-grid">
        <div className="card settings-card">
          <div className="card-icon sage">
            <Database size={23} />
          </div>
          <h3>本地模型</h3>
          <div className="setting-line">
            <span>生成模型</span>
            <b>{stats?.model.model || "未连接"}</b>
          </div>
          <div className="setting-line">
            <span>向量模型</span>
            <b>{stats?.model.embedding_model || "未连接"}</b>
          </div>
          <div className="setting-line">
            <span>连接状态</span>
            <span
              className={
                "status-badge " + (stats?.model.available ? "ready" : "error")
              }
            >
              {stats?.model.available ? "已连接" : "未连接"}
            </span>
          </div>
          <p>
            模型在本机运行。首次加载、长文翻译与复杂问答可能需要等待。原始文献保存在项目
            data 目录。
          </p>
          <button className="button secondary small" onClick={refresh}>
            <RefreshCw size={15} />
            检查连接
          </button>
        </div>
        <div className="card settings-card">
          <div className="card-icon lavender">
            <ShieldCheck size={23} />
          </div>
          <h3>数据与能力边界</h3>
          <p>
            PDF 解析、OCR、检索、图谱与绘图在本地处理。arXiv
            检索和论文下载需要访问网络。
          </p>
          <p>
            扫描件的公式、复杂表格和引用匹配可能需要人工校对。生成答案与草稿应核查原文。
          </p>
          <div className="info-line">
            <CheckCircle2 size={16} />
            当前服务仅监听 127.0.0.1
          </div>
        </div>
      </div>
      <div className="card index-card">
        <div className="panel-top">
          <span>
            <Layers size={17} />
            文献语义索引
          </span>
          <small>启用跨语言语义检索，与关键词检索结合</small>
        </div>
        {!docs.length ? (
          <p className="muted">导入文献后即可建立索引。</p>
        ) : (
          docs.map((d) => (
            <div className="index-row" key={d.id}>
              <div>
                <b>{short(d.title, 70)}</b>
                <small>
                  {d.chunk_count} 个内容块 · {statusName[d.status]}
                </small>
              </div>
              <button
                className="button secondary small"
                disabled={!!indexing || d.status !== "ready"}
                onClick={() => index(d)}
              >
                {indexing === d.id || d.status === "indexing" ? (
                  <Loader2 size={14} className="spin" />
                ) : (
                  <Layers size={14} />
                )}
                建立 / 更新索引
              </button>
            </div>
          ))
        )}
      </div>
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);
