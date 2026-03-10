import os
import time
from dataclasses import dataclass
from typing import Dict, Optional, Literal, List

from mcp.server.fastmcp import FastMCP
from playwright.async_api import (async_playwright,
                                  Playwright,
                                  Browser,
                                  BrowserContext,
                                  Page,
                                  TimeoutError)


mcp = FastMCP('web_server')


@dataclass
class Session:
    browser: Browser
    context: BrowserContext
    page: Page
    created_at: float
    

_playwright: Optional[Playwright] = None
_sessions: Dict[str, Session] = {}
_session_counter = 0


def _new_session_id():
    global _session_counter
    _session_counter += 1
    return f'session-{_session_counter}'

def _get_session(session_id: str) -> Session:
    if session_id not in _sessions:
        raise ValueError(f'Unknown session_id: {session_id}.')
    return _sessions[session_id]

async def _ensure_playwright() -> Playwright:
    global _playwright
    if _playwright is None:
        _playwright = await async_playwright().start()
    return _playwright



@mcp.tool()
async def browser_start(headful: bool = True,
                        slow_mo_ms: int = 150,) -> str:
    """
    Start Chromium Browser. Shows the window and 
    slows down actions.
    Returns a session_id
    """
    pw = await _ensure_playwright()
    
    browser = await pw.chromium.launch(headless = not headful, slow_mo = slow_mo_ms)
    context = await browser.new_context()
    page = await context.new_page()
    
    session_id = _new_session_id()
    _sessions[session_id] = Session(browser = browser, context = context, page = page,
                                    created_at = time.time())
    return session_id


@mcp.tool()
async def goto(session_id: str, url: str, 
               wait_until: Literal['domcontentloaded', 'load', 'networkidel'] = 'domcontentloaded') -> str:
    """ Navigate to URL """
    s = _get_session(session_id)
    await s.page.goto(url, wait_until = wait_until)
    return f'navigated: {url}'

@mcp.tool()
async def wait_for(session_id: str, selector: str, timeout_ms: int = 8000) -> str:
    """ Wait until selector is visible on the page """
    s = _get_session(session_id)
    await s.page.wait_for_selector(selector, timeout = timeout_ms, state = 'visible')
    return f'ready: {selector}'

@mcp.tool()
async def click(session_id: str, selector: str, timeout_ms: int = 8000) -> str:
    """Click the first element that matches selector."""
    s = _get_session(session_id)
    await s.page.locator(selector).first.click(timeout=timeout_ms)
    return f"clicked: {selector}"


@mcp.tool()
async def fill(session_id: str, selector: str, text: str, timeout_ms: int = 8000) -> str:
    """Fill an input matching selector with text."""
    s = _get_session(session_id)
    await s.page.locator(selector).first.fill(text, timeout=timeout_ms)
    return f"filled: {selector}"


@mcp.tool()
async def press(session_id: str, key: str) -> str:
    """Press a keyboard key (e.g. 'Enter')."""
    s = _get_session(session_id)
    await s.page.keyboard.press(key)
    return f"pressed: {key}"


@mcp.tool()
async def get_title(session_id: str) -> str:
    """Return current page title."""
    s = _get_session(session_id)
    return await s.page.title()


@mcp.tool()
async def get_page_url(session_id: str) -> str:
    """Return current page URL."""
    s = _get_session(session_id)
    return s.page.url


@mcp.tool()
async def extract_text(session_id: str, selector: str, max_chars: int = 4000) -> str:
    """
    Extract inner text from the first matching selector.
    Returns empty string if not found.
    """
    s = _get_session(session_id)
    loc = s.page.locator(selector).first
    try:
        txt = await loc.inner_text(timeout=2000)
    except TimeoutError:
        return ""
    txt = (txt or "").strip()
    return txt[:max_chars]


@mcp.tool()
async def extract_many_texts(
    session_id: str,
    selector: str,
    limit: int = 20,
    max_chars_each: int = 400,
) -> List[str]:
    """
    Extract inner texts of multiple elements matching selector.
    Useful for lists (event cards, sight lists, etc.).
    """
    s = _get_session(session_id)
    loc = s.page.locator(selector)
    count = await loc.count()
    count = min(count, limit)

    out: List[str] = []
    for i in range(count):
        try:
            t = await loc.nth(i).inner_text(timeout=2000)
        except PWTimeout:
            t = ""
        t = (t or "").strip()
        if t:
            out.append(t[:max_chars_each])
    return out


@mcp.tool()
async def screenshot(session_id: str, path: str) -> str:
    """
    Save a full-page screenshot to a REQUIRED path and return that path.
    Example path: outputs/screenshots/page.png
    """
    if not path or not path.strip():
        raise ValueError("path is required, e.g. 'outputs/screenshots/page.png'")

    s = _get_session(session_id)
    dir_name = os.path.dirname(path) or "."
    os.makedirs(dir_name, exist_ok=True)

    await s.page.screenshot(path=path, full_page=True)
    return path


@mcp.tool()
async def browser_close(session_id: str) -> str:
    """Close one browser session."""
    s = _sessions.pop(session_id, None)
    if not s:
        return "already closed"

    await s.context.close()
    await s.browser.close()
    return f"closed: {session_id}"


@mcp.tool()
async def shutdown() -> str:
    """
    Close all sessions and stop Playwright.
    Useful when you restart the server often during development.
    """
    global _playwright

    # close sessions
    for sid in list(_sessions.keys()):
        try:
            await browser_close(sid)
        except Exception:
            pass

    # stop playwright
    if _playwright is not None:
        await _playwright.stop()
        _playwright = None

    return "shutdown complete"
    

if __name__ == '__main__':
    mcp.run(transport = 'stdio')