"""
CLI tool for searching mock contacts (for demo purposes).
Works without Apollo.io API - uses generated mock data.
"""

import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from scrapers.schemas import Contact

app = typer.Typer(help="LeadOn CRM - Mock Contact Search (Demo Mode)")
console = Console()


def load_mock_contacts(filename: str = "demo_contacts.json") -> List[Contact]:
    """Load mock contacts from JSON file."""
    file_path = Path("exports") / filename
    
    if not file_path.exists():
        console.print(f"[yellow]Mock data file not found: {file_path}[/yellow]")
        console.print("[cyan]Generating demo data...[/cyan]\n")
        
        # Generate demo data
        import subprocess
        subprocess.run(["python", "create_mock_contacts.py", "demo"], check=True)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    contacts = [Contact(**item) for item in data]
    return contacts


def filter_contacts(
    contacts: List[Contact],
    query: Optional[str] = None,
    titles: Optional[List[str]] = None,
    companies: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    tags: Optional[List[str]] = None
) -> List[Contact]:
    """Filter contacts based on criteria."""
    filtered = contacts
    
    if query:
        query_lower = query.lower()
        filtered = [
            c for c in filtered
            if (query_lower in (c.name or "").lower() or
                query_lower in (c.title or "").lower() or
                query_lower in (c.company or "").lower() or
                any(query_lower in tag.lower() for tag in c.tags))
        ]
    
    if titles:
        titles_lower = [t.lower() for t in titles]
        filtered = [
            c for c in filtered
            if any(title in (c.title or "").lower() for title in titles_lower)
        ]
    
    if companies:
        companies_lower = [comp.lower() for comp in companies]
        filtered = [
            c for c in filtered
            if any(comp in (c.company or "").lower() for comp in companies_lower)
        ]
    
    if locations:
        locations_lower = [loc.lower() for loc in locations]
        filtered = [
            c for c in filtered
            if any(loc in f"{c.city} {c.state}".lower() for loc in locations_lower)
        ]
    
    if tags:
        tags_lower = [t.lower() for t in tags]
        filtered = [
            c for c in filtered
            if any(tag in [ct.lower() for ct in c.tags] for tag in tags_lower)
        ]
    
    return filtered


def display_contacts_table(contacts: List[Contact], title: str = "Search Results"):
    """Display contacts in a table."""
    if not contacts:
        console.print("[yellow]No contacts found.[/yellow]")
        return
    
    table = Table(title=title, show_header=True, header_style="bold magenta")
    
    table.add_column("Name", style="cyan", no_wrap=False)
    table.add_column("Title", style="green")
    table.add_column("Company", style="blue")
    table.add_column("Email", style="yellow")
    table.add_column("Location", style="white")
    table.add_column("Tags", style="dim")
    
    for contact in contacts:
        location = f"{contact.city}, {contact.state}".strip(", ")
        tags_str = ", ".join(contact.tags[:3])  # Show first 3 tags
        table.add_row(
            contact.name or "N/A",
            contact.title or "N/A",
            contact.company or "N/A",
            contact.email or "N/A",
            location or "N/A",
            tags_str
        )
    
    console.print(table)


@app.command()
def search(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    titles: Optional[str] = typer.Option(None, "--titles", "-t", help="Job titles (comma-separated)"),
    companies: Optional[str] = typer.Option(None, "--companies", "-c", help="Companies (comma-separated)"),
    locations: Optional[str] = typer.Option(None, "--locations", "-l", help="Locations (comma-separated)"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Tags (comma-separated)"),
    limit: int = typer.Option(25, "--limit", "-n", help="Number of results"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Interactive mode")
):
    """
    Search mock contacts (demo mode).
    
    Examples:
        python -m cli.search_mock search
        python -m cli.search_mock search -q "AI" -t "CEO,CTO"
        python -m cli.search_mock search --tags investor
    """
    console.print(Panel.fit(
        "[bold cyan]LeadOn CRM - Contact Search (DEMO MODE)[/bold cyan]\n"
        "[yellow]Using mock data for demonstration[/yellow]",
        border_style="cyan"
    ))
    
    # Interactive mode
    if interactive and not query:
        console.print("\n[bold]Let's find some contacts![/bold]\n")
        
        query = Prompt.ask("🔍 What are you looking for?", default="")
        
        if Prompt.ask("Add job title filters?", choices=["y", "n"], default="n") == "y":
            titles = Prompt.ask("Job titles (comma-separated)", default="CEO,CTO")
        
        if Prompt.ask("Add company filters?", choices=["y", "n"], default="n") == "y":
            companies = Prompt.ask("Companies (comma-separated)", default="")
        
        if Prompt.ask("Add location filters?", choices=["y", "n"], default="n") == "y":
            locations = Prompt.ask("Locations (comma-separated)", default="San Francisco")
        
        if Prompt.ask("Add tag filters?", choices=["y", "n"], default="n") == "y":
            tags = Prompt.ask("Tags (comma-separated)", default="investor,ai")
        
        limit = int(Prompt.ask("How many results?", default="25"))
    
    # Parse filters
    titles_list = [t.strip() for t in titles.split(",")] if titles else None
    companies_list = [c.strip() for c in companies.split(",")] if companies else None
    locations_list = [l.strip() for l in locations.split(",")] if locations else None
    tags_list = [t.strip() for t in tags.split(",")] if tags else None
    
    # Load and filter contacts
    console.print("\n[cyan]Loading mock contacts...[/cyan]")
    all_contacts = load_mock_contacts()
    console.print(f"[green]✓[/green] Loaded {len(all_contacts)} contacts\n")
    
    console.print("[cyan]Filtering contacts...[/cyan]")
    filtered_contacts = filter_contacts(
        all_contacts,
        query=query,
        titles=titles_list,
        companies=companies_list,
        locations=locations_list,
        tags=tags_list
    )
    
    # Apply limit
    results = filtered_contacts[:limit]
    
    # Display results
    console.print(f"\n[bold green]Found {len(filtered_contacts)} matching contacts[/bold green]")
    console.print(f"Showing {len(results)} results\n")
    
    display_contacts_table(results)
    
    # Export option
    if results and interactive:
        console.print()
        if Confirm.ask("Export to JSON?"):
            output_file = f"filtered_contacts_{query or 'search'}.json".replace(" ", "_")
            output_path = Path("exports") / output_file
            
            data = [c.model_dump(mode='json') for c in results]
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            console.print(f"[green]✓[/green] Exported to {output_path}")


@app.command()
def stats():
    """Show statistics about mock data."""
    console.print(Panel.fit(
        "[bold cyan]Mock Data Statistics[/bold cyan]",
        border_style="cyan"
    ))
    
    contacts = load_mock_contacts()
    
    console.print(f"\n[bold]Total Contacts:[/bold] {len(contacts)}")
    
    # Count by company
    companies = {}
    for c in contacts:
        companies[c.company] = companies.get(c.company, 0) + 1
    
    console.print(f"\n[bold]Top Companies:[/bold]")
    for company, count in sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]:
        console.print(f"  • {company}: {count} contacts")
    
    # Count by tags
    tags = {}
    for c in contacts:
        for tag in c.tags:
            tags[tag] = tags.get(tag, 0) + 1
    
    console.print(f"\n[bold]Top Tags:[/bold]")
    for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10]:
        console.print(f"  • {tag}: {count} contacts")
    
    # Count by location
    locations = {}
    for c in contacts:
        loc = f"{c.city}, {c.state}"
        locations[loc] = locations.get(loc, 0) + 1
    
    console.print(f"\n[bold]Top Locations:[/bold]")
    for location, count in sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]:
        console.print(f"  • {location}: {count} contacts")
    
    console.print()


@app.command()
def examples():
    """Show example search queries."""
    console.print(Panel.fit(
        "[bold cyan]Example Search Queries[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print("\n[bold]1. Find AI company executives:[/bold]")
    console.print("   python -m cli.search_mock search -q 'AI' -t 'CEO,CTO'")
    
    console.print("\n[bold]2. Find investors:[/bold]")
    console.print("   python -m cli.search_mock search --tags investor")
    
    console.print("\n[bold]3. Find contacts in San Francisco:[/bold]")
    console.print("   python -m cli.search_mock search -l 'San Francisco'")
    
    console.print("\n[bold]4. Find contacts at specific companies:[/bold]")
    console.print("   python -m cli.search_mock search -c 'Anthropic,OpenAI'")
    
    console.print("\n[bold]5. Interactive search:[/bold]")
    console.print("   python -m cli.search_mock search")
    
    console.print("\n[bold]6. View statistics:[/bold]")
    console.print("   python -m cli.search_mock stats")
    
    console.print()


if __name__ == "__main__":
    app()

