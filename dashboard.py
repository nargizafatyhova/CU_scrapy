import math

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pymongo import MongoClient

app = FastAPI()

_client = MongoClient("mongodb://localhost:27017/")
_db = _client["kp_news_db"]
_collection = _db["articles"]

PAGE_SIZE = 50

# ---------------------------------------------------------------------------
# CSS (dark theme, VS Code inspired)
# ---------------------------------------------------------------------------

_CSS = """\
body { background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', monospace; margin: 0; padding: 20px; }
.header { position: sticky; top: 0; background: #2d2d2d; padding: 15px; border-bottom: 2px solid #007acc; z-index: 100; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
h1 { margin: 0; color: #fff; font-size: 24px; }
.stats { color: #aaa; font-size: 14px; }
.pagination a { background: #007acc; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; margin: 0 5px; font-weight: bold; }
.pagination a:hover { background: #005f9e; }
.pagination span { font-size: 18px; margin: 0 10px; color: #fff; }
.disabled { background: #555 !important; pointer-events: none; color: #888 !important; }
.card { background-color: #252526; border-left: 5px solid #0e639c; margin-bottom: 20px; padding: 15px; border-radius: 3px; font-size: 14px; line-height: 1.4; }
.key { color: #9cdcfe; }
.string { color: #ce9178; }
.null { color: #569cd6; }
.bracket { color: #ffd700; font-weight: bold; }
.img-preview { max-width: 300px; border: 1px solid #555; margin-top: 5px; display: block; }
.field-row { margin-left: 20px; margin-bottom: 2px; }
a.link { color: #4da6ff; text-decoration: none; border-bottom: 1px dashed #4da6ff; }
.comment { color: #6a9955; }
"""

# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _fmt_value(value) -> str:
    if value is None:
        return '<span class="null">null</span>'
    escaped = str(value).replace('"', '\\"')
    return f'<span class="string">"{escaped}"</span>'


def _fmt_link(url) -> str:
    return f'<a href="{url}" target="_blank" class="link">"{url}"</a>'


def _fmt_photo_b64(raw: str) -> str:
    if not raw:
        return '<span class="null">null</span>'
    label = f'<span class="string">"DATA_PRESENT ({len(raw)} chars)..."</span>'
    preview = f'<img src="data:image/jpeg;base64,{raw}" class="img-preview">'
    return f"{label}<br>{preview}"


def _fmt_article_text(doc: dict) -> str:
    full_text = doc.get("article_text", "")
    preview = full_text[:200].replace('"', '\\"') + "..." if full_text else ""
    return (
        f'<span class="string">"{preview}"</span> '
        f'<span class="comment">// \u041f\u043e\u043b\u043d\u0430\u044f \u0434\u043b\u0438\u043d\u0430: {len(full_text)} \u0441\u0438\u043c\u0432.</span>'
    )


def _pagination_block(page: int, total_pages: int) -> str:
    prev_cls = 'class="disabled"' if page == 1 else ""
    next_cls = 'class="disabled"' if page == total_pages else ""
    return (
        '<div class="pagination">'
        f'<a href="/?page={page - 1}" {prev_cls}>\u2190 \u041d\u0430\u0437\u0430\u0434</a>'
        f'<span>\u0421\u0442\u0440. {page}/{total_pages}</span>'
        f'<a href="/?page={page + 1}" {next_cls}>\u0412\u043f\u0435\u0440\u0435\u0434 \u2192</a>'
        "</div>"
    )


def _render_card(doc: dict, ordinal: int) -> str:
    rows = [
        f'<div class="field-row"><span class="key">"title":</span> {_fmt_value(doc.get("title"))},</div>',
        f'<div class="field-row"><span class="key">"description":</span> {_fmt_value(doc.get("description"))},</div>',
        f'<div class="field-row"><span class="key">"article_text":</span> {_fmt_article_text(doc)},</div>',
        f'<div class="field-row"><span class="key">"publication_datetime":</span> {_fmt_value(doc.get("publication_datetime"))},</div>',
        f'<div class="field-row"><span class="key">"header_photo_url":</span> {_fmt_link(doc.get("header_photo_url"))},</div>',
        f'<div class="field-row"><span class="key">"header_photo_base64":</span> {_fmt_photo_b64(doc.get("header_photo_base64", ""))},</div>',
        f'<div class="field-row"><span class="key">"keywords":</span> {_fmt_value(doc.get("keywords"))},</div>',
        f'<div class="field-row"><span class="key">"authors":</span> {_fmt_value(doc.get("authors"))},</div>',
        f'<div class="field-row"><span class="key">"source_url":</span> {_fmt_link(doc.get("source_url"))}</div>',
    ]
    inner = "\n".join(rows)
    return (
        '<div class="card">'
        f'<div style="color: #888; margin-bottom:5px;">Item #{ordinal}</div>'
        '<span class="bracket">{</span>'
        f"{inner}"
        '<span class="bracket">}</span>'
        "</div>"
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def dashboard(page: int = Query(1, ge=1)):
    total_items = _collection.estimated_document_count()
    total_pages = math.ceil(total_items / PAGE_SIZE) if total_items > 0 else 1
    if page > total_pages:
        page = total_pages

    skip = (page - 1) * PAGE_SIZE
    docs = list(_collection.find().sort("_id", -1).skip(skip).limit(PAGE_SIZE))

    cards = "\n".join(
        _render_card(doc, skip + idx + 1) for idx, doc in enumerate(docs)
    )
    nav = _pagination_block(page, total_pages)

    return (
        "<html>"
        f"<head><title>KP Report ({total_items})</title><style>{_CSS}</style></head>"
        "<body>"
        '<div class="header">'
        "<div>"
        "<h1>\U0001f4d1 \u041e\u0442\u0447\u0435\u0442 \u043f\u043e \u0441\u0431\u043e\u0440\u0443 (\u0422\u0417: KP.ru)</h1>"
        f'<span class="stats">\u0417\u0430\u043f\u0438\u0441\u0435\u0439 \u0432 Mongo: <b>{total_items}</b></span>'
        "</div>"
        f"{nav}"
        "</div>"
        f'<div style="margin-top: 20px;">{cards}</div>'
        f'<div style="text-align: center; margin-top: 30px; padding-bottom: 30px;">{nav}</div>'
        "</body></html>"
    )
