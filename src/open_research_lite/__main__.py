"""Professional Red-Themed Interactive Terminal Interface for open research-lite.

Modeled after Claude Code with a crimson red aesthetic, 19-model selector,
human-intuitive prompts, live progress reporting, and zero emojis.
"""

import os
import sys
import asyncio
import webbrowser
from typing import Optional

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from open_research_lite.researcher import Researcher
from open_research_lite.models import (
    AVAILABLE_MODELS,
    SMALL_EXTRACTOR_MODELS,
    MAIN_WRITER_MODELS,
    resolve_api_key
)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.text import Text
    from rich.align import Align
    import questionary
    HAS_TUI = True
except ImportError:
    HAS_TUI = False


BANNER_ASCII = r"""
 ██████╗ ██████╗ ███████╗███╗   ██╗    ██████╗ ███████╗███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║
██║   ██║██████╔╝█████╗  ██╔██╗ ██║    ██████╔╝█████╗  ███████╗█████╗  ███████║██████╔╝██║     ███████║
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║    ██╔══██╗██╔══╝  ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║
╚██████╔╝██║     ███████╗██║ ╚████║    ██║  ██║███████╗███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝    ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
"""

TAGLINE = "open research-lite: Autonomous Research Agent with Differential Knowledge Tracking"
SUBTAG = "Prunes 70%+ repetitive fluff | Dual-model extraction & synthesis | Visual dossier export"

# Custom Red TUI styling (Claude Code-inspired crimson palette)
RED_STYLE = questionary.Style([
    ('qmark', 'fg:#ef4444 bold'),
    ('question', 'bold white'),
    ('answer', 'fg:#ef4444 bold'),
    ('pointer', 'fg:#ef4444 bold'),
    ('highlighted', 'fg:#ffffff bg:#991b1b bold'),
    ('selected', 'fg:#ef4444'),
    ('separator', 'fg:#7f1d1d'),
    ('instruction', 'fg:#94a3b8'),
])


def render_banner(console: Console):
    banner_text = Text(BANNER_ASCII, style="bold red")
    sub_text = Text(f"\n{TAGLINE}\n", style="bold white")
    desc_text = Text(f"{SUBTAG}\n", style="dim white")
    
    panel = Panel(
        Align.center(banner_text + sub_text + desc_text),
        border_style="red",
        padding=(1, 2)
    )
    console.print(panel)


def _get_api_key_interactive(model_id: str, role_title: str, console: Optional[Console] = None) -> Optional[str]:
    """Resolves existing API key or prompts user with option to reuse or override."""
    from open_research_lite.models import resolve_api_key, get_env_var_for_model
    env_var = get_env_var_for_model(model_id)
    env_key = resolve_api_key(model_id)

    if env_key and env_key.strip():
        masked = env_key[:4] + "..." + env_key[-4:] if len(env_key) > 8 else "****"
        use_existing = questionary.confirm(
            f"Found configured {env_var} for {role_title} ({masked}). Use this key?",
            default=True,
            style=RED_STYLE
        ).ask()
        if use_existing is None:
            raise KeyboardInterrupt()
        if use_existing:
            return env_key.strip()

    while True:
        val = questionary.password(
            f"Enter API key ({env_var}) for {role_title} ({model_id}):",
            style=RED_STYLE
        ).ask()
        if val is None:
            raise KeyboardInterrupt()
        val = val.strip()
        if not val:
            msg = f"API key cannot be empty for {model_id}. Please enter your key (or press Ctrl+C to cancel):"
            if console:
                console.print(f"[bold yellow]{msg}[/bold yellow]")
            else:
                print(msg)
            continue
        os.environ[env_var] = val
        return val


def main():
    # Show help message if requested
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h", "help"):
        print("""
open research-lite: Autonomous Deep Research Agent with Differential Knowledge Tracking

Usage:
    open-research                          Launch interactive crimson TUI wizard
    open-research "<query>"                Run research directly on target topic
    python -m open_research_lite           Universal launcher

Options:
    -h, --help                             Display this help message
""")
        return

    # If arguments are passed directly on CLI (e.g. open-research "my query"), run directly!
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:]).strip()
        console = Console() if HAS_TUI else None
        if console:
            render_banner(console)

        search_api = "tavily" if os.getenv("TAVILY_API_KEY") else "duckduckgo"
        from open_research_lite.models import get_default_models
        default_ext, default_wri = get_default_models()
        ext_key = resolve_api_key(default_ext)
        wri_key = resolve_api_key(default_wri)

        try:
            asyncio.run(_execute_research(
                console=console or Console(),
                query=query,
                extractor_model=default_ext,
                writer_model=default_wri,
                extractor_api_key=ext_key,
                writer_api_key=wri_key,
                search_api=search_api,
                max_sources=5
            ))
        except (KeyboardInterrupt, EOFError):
            print("\nSession terminated by user.")
            sys.exit(0)
        return

    if not HAS_TUI or not sys.stdin.isatty():
        _headless_cli()
        return

    console = Console()
    render_banner(console)

    while True:
        try:
            # 1. Research Topic Prompt
            query = questionary.text(
                "What topic would you like to research? (Press Ctrl+C anytime to exit)",
                default="High-Bandwidth Memory HBM4 Architecture and Interconnect Scaling",
                style=RED_STYLE
            ).ask()

            if query is None:
                raise KeyboardInterrupt()

            query = query.strip()
            if not query or query.lower() in ("exit", "quit", "q", ":q"):
                console.print("[dim]Session ended by user.[/dim]")
                break

            # 2. Select Fast LLM (Fact Extractor)
            extractor_choices = [item["label"] for item in SMALL_EXTRACTOR_MODELS]
            selected_ext_label = questionary.select(
                "Choose Fast LLM (Sifts web scrapes, extracts facts, catches contradictions):",
                choices=extractor_choices,
                style=RED_STYLE
            ).ask()

            if selected_ext_label is None:
                raise KeyboardInterrupt()

            selected_ext = next((m for m in SMALL_EXTRACTOR_MODELS if m["label"] == selected_ext_label), SMALL_EXTRACTOR_MODELS[0])
            extractor_model_id = selected_ext["id"]
            extractor_api_key = _get_api_key_interactive(extractor_model_id, "Fast LLM", console)

            # 3. Select Smart LLM (Report Writer)
            writer_choices = [item["label"] for item in MAIN_WRITER_MODELS]
            selected_writer_label = questionary.select(
                "Choose Smart LLM (Synthesizes comprehensive research dossier from verified graph):",
                choices=writer_choices,
                style=RED_STYLE
            ).ask()

            if selected_writer_label is None:
                raise KeyboardInterrupt()

            selected_writer = next((m for m in MAIN_WRITER_MODELS if m["label"] == selected_writer_label), MAIN_WRITER_MODELS[0])
            writer_model_id = selected_writer["id"]
            writer_api_key = _get_api_key_interactive(writer_model_id, "Smart LLM", console)

            # 4. Select Search Engine
            search_choice = questionary.select(
                "Choose web search provider:",
                choices=[
                    "DuckDuckGo Search (Free, no API key required - Recommended)",
                    "Tavily Search API (Deep web research across multiple pages)"
                ],
                style=RED_STYLE
            ).ask()

            if search_choice is None:
                raise KeyboardInterrupt()

            search_api = "tavily" if "Tavily" in (search_choice or "") else "duckduckgo"
            if search_api == "tavily":
                tav_env = os.getenv("TAVILY_API_KEY")
                if tav_env and tav_env.strip():
                    masked_tav = tav_env[:4] + "..." + tav_env[-4:] if len(tav_env) > 8 else "****"
                    use_tav = questionary.confirm(
                        f"Found TAVILY_API_KEY ({masked_tav}). Use this key?",
                        default=True,
                        style=RED_STYLE
                    ).ask()
                    if use_tav is None:
                        raise KeyboardInterrupt()
                    if not use_tav:
                        tav_key = questionary.password("Enter new TAVILY_API_KEY (or press Enter to use DuckDuckGo):", style=RED_STYLE).ask()
                        if tav_key is None:
                            raise KeyboardInterrupt()
                        if tav_key and tav_key.strip():
                            os.environ["TAVILY_API_KEY"] = tav_key.strip()
                        else:
                            console.print("[dim]No Tavily key entered; continuing with free DuckDuckGo search.[/dim]")
                            search_api = "duckduckgo"
                else:
                    tav_key = questionary.password(
                        "Enter TAVILY_API_KEY (or press Enter to use free DuckDuckGo):",
                        style=RED_STYLE
                    ).ask()
                    if tav_key is None:
                        raise KeyboardInterrupt()
                    if tav_key and tav_key.strip():
                        os.environ["TAVILY_API_KEY"] = tav_key.strip()
                    else:
                        console.print("[dim]No Tavily key entered; continuing with free DuckDuckGo search.[/dim]")
                        search_api = "duckduckgo"

            # 5. Select Research Depth
            depth_choice = questionary.select(
                "How many web sources should we investigate?",
                choices=[
                    "Quick scan (3 sources)",
                    "Standard research (5 sources - Recommended)",
                    "Comprehensive research (8 sources)"
                ],
                style=RED_STYLE
            ).ask()

            if depth_choice is None:
                raise KeyboardInterrupt()

            max_sources = 5
            if "Quick" in (depth_choice or ""):
                max_sources = 3
            elif "Comprehensive" in (depth_choice or ""):
                max_sources = 8

            # Run Autonomous Research with auto-recovery on bad keys or search errors
            while True:
                try:
                    asyncio.run(_execute_research(
                        console=console,
                        query=query,
                        extractor_model=extractor_model_id,
                        writer_model=writer_model_id,
                        extractor_api_key=extractor_api_key,
                        writer_api_key=writer_api_key,
                        search_api=search_api,
                        max_sources=max_sources
                    ))
                    break
                except (KeyboardInterrupt, EOFError):
                    console.print("\n[dim]Mission interrupted by user.[/dim]")
                    return
                except Exception as e:
                    err_str = str(e)
                    is_auth_error = any(kw in err_str.lower() for kw in (
                        "api_key", "api key", "401", "authentication", "unauthorized", 
                        "permission denied", "quota", "invalid_api_key", "forbidden"
                    ))
                    is_search_error = any(kw in err_str.lower() for kw in ("tavily", "duckduckgo", "search"))

                    if is_auth_error:
                        console.print(f"\n[bold red][Authentication Error][/bold red] {err_str}\n")
                        retry = questionary.confirm(
                            "An API key was rejected or invalid. Would you like to enter a new API key and retry?",
                            default=True,
                            style=RED_STYLE
                        ).ask()
                        if retry is None or not retry:
                            break
                        extractor_api_key = _get_api_key_interactive(extractor_model_id, "Fast LLM", console)
                        writer_api_key = _get_api_key_interactive(writer_model_id, "Smart LLM", console)
                        continue

                    elif is_search_error:
                        console.print(f"\n[bold red][Search Error][/bold red] {err_str}\n")
                        if search_api != "duckduckgo":
                            retry_search = questionary.confirm(
                                "Web search failed. Would you like to switch to free DuckDuckGo search (no API key required) and retry?",
                                default=True,
                                style=RED_STYLE
                            ).ask()
                            if retry_search:
                                search_api = "duckduckgo"
                                continue
                        else:
                            tav_key = os.getenv("TAVILY_API_KEY")
                            if tav_key:
                                switch_tav = questionary.confirm(
                                    "DuckDuckGo search encountered an issue. Would you like to switch to Tavily Search and retry?",
                                    default=True,
                                    style=RED_STYLE
                                ).ask()
                                if switch_tav:
                                    search_api = "tavily"
                                    continue
                            retry_same = questionary.confirm(
                                "Search encountered a network issue. Would you like to retry?",
                                default=True,
                                style=RED_STYLE
                            ).ask()
                            if retry_same:
                                continue
                        break
                    else:
                        console.print(f"\n[bold red][Error][/bold red] {err_str}\n")
                        retry_gen = questionary.confirm(
                            "An error occurred during research. Would you like to retry?",
                            default=False,
                            style=RED_STYLE
                        ).ask()
                        if retry_gen:
                            continue
                        break

            # What next?
            next_action = questionary.select(
                "What would you like to do next?",
                choices=[
                    "Open interactive visual HTML dossier in browser",
                    "Run another research query",
                    "Exit"
                ],
                style=RED_STYLE
            ).ask()

            if next_action and "Open" in next_action:
                html_path = os.path.abspath("research_report.html")
                console.print(f"[bold red]Opening {html_path} in your default browser...[/bold red]")
                webbrowser.open(f"file://{html_path}")

                again = questionary.confirm("Run another research query?", default=True, style=RED_STYLE).ask()
                if not again:
                    break
            elif not next_action or "Exit" in next_action:
                break

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session terminated by user.[/dim]")
            sys.exit(0)

    console.print("\n[bold red]open research-lite session closed.[/bold red]\n")


async def _execute_research(
    console: Console,
    query: str,
    extractor_model: str,
    writer_model: str,
    extractor_api_key: Optional[str],
    writer_api_key: Optional[str],
    search_api: str,
    max_sources: int
):
    console.print(f"\n[bold red]--> INITIALIZING RESEARCH MISSION[/bold red]")
    console.print(f"    [dim]Topic           :[/dim] [bold white]{query}[/bold white]")
    console.print(f"    [dim]Fast LLM (Fact) :[/dim] [red]{extractor_model}[/red]")
    console.print(f"    [dim]Smart LLM (Doc) :[/dim] [red]{writer_model}[/red]")
    console.print(f"    [dim]Search Engine   :[/dim] [white]{search_api}[/white] [dim]({max_sources} sources)[/dim]\n")

    researcher = Researcher(
        query=query,
        search_api=search_api,
        max_results=max_sources,
        extractor_model=extractor_model,
        writer_model=writer_model,
        extractor_api_key=extractor_api_key,
        writer_api_key=writer_api_key,
        verbose=False
    )

    with console.status("[bold red]Step 1/3:[/] [white]Searching web sources...[/]", spinner="line"):
        sources = await researcher._fetch_sources()

    with console.status(f"[bold red]Step 2/3:[/] [white]Extracting facts and diffing {len(sources)} sources with Fast LLM...[/]", spinner="line"):
        await researcher.conduct_research(custom_sources=sources)

    with console.status("[bold red]Step 3/3:[/] [white]Synthesizing final research report with Smart LLM...[/]", spinner="line"):
        report = await researcher.write_report()
        md_path = researcher.export_markdown("research_report.md")
        html_path = researcher.export_html("research_report.html")


    stats = researcher.get_stats()
    tel = stats["telemetry"]
    graph = stats["graph"]

    # Red Telemetry Scorecard Table
    table = Table(title="TELEMETRY & KNOWLEDGE STATE", border_style="red")
    table.add_column("Metric", style="bold white")
    table.add_column("Value", style="bold red")
    table.add_column("Impact", style="dim white")

    table.add_row("Raw Words Ingested", f"{tel['total_input_words']:,}", "Multi-page search stream")
    table.add_row("Summary Words Retained", f"{tel['total_output_words']:,}", f"{tel['token_reduction_pct']}% text pruned")
    table.add_row("Verified Facts Isolated", f"{graph['total_facts']}", f"{graph['total_entities']} unique entities mapped")
    table.add_row(
        "Conflicting Claims Detected", 
        f"{tel['facts_conflicted']}", 
        "[bold red]Contradiction Flagged[/bold red]" if tel['facts_conflicted'] > 0 else "Source Consensus"
    )

    console.print("\n")
    console.print(table)
    console.print("\n")

    # Render Report in Red Border Panel
    console.print(Panel(
        Markdown(report), 
        title=f"[bold red]RESEARCH REPORT: {query}[/bold red]", 
        border_style="red",
        padding=(1, 2)
    ))

    console.print(f"\n[bold red][OK][/bold red] Markdown report saved to: [bold underline white]{os.path.abspath(md_path)}[/]")
    console.print(f"[bold red][OK][/bold red] Interactive HTML dossier saved to: [bold underline white]{os.path.abspath(html_path)}[/]")


def _headless_cli():
    try:
        query = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
        if not query:
            query = input("Enter your research query (or press Ctrl+C to exit):\n> ").strip()
        if not query or query.lower() in ("exit", "quit", "q"):
            print("Session ended.")
            return

        researcher = Researcher(query=query)

        async def _run():
            await researcher.conduct_research()
            report = await researcher.write_report()
            print(report)

        asyncio.run(_run())
    except (KeyboardInterrupt, EOFError):
        print("\nSession terminated by user.")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nSession terminated by user.")
        sys.exit(0)

