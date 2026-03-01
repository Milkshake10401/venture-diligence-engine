from src.scraper_spacy_only import scrape_portfolio
from src.comparer import load_competitors, find_conflicts

def main():
    print("\n=== VC Diligence Automation Toolkit ===")
    url = input("Enter VC portfolio URL: ").strip()
    if not url:
        print("No URL provided.")
        return

    print(f"\n[+] Scraping company/portfolio data from: {url}")
    # from src.scraper import scrape_portfolio
    portfolio_names = scrape_portfolio(url, render_js=True)
    print(f"   → Found {len(portfolio_names)} potential company names.")

    competitors = load_competitors()
    direct, adjacent = find_conflicts(portfolio_names, competitors)

    print("\n[RESULTS]")
    print(f"Direct Conflicts: {direct or 'None'}")
    print(f"Adjacent Conflicts: {adjacent or 'None'}")
    print(f"Clean Matches: {len(portfolio_names) - len(direct) - len(adjacent)}")

if __name__ == "__main__":
    main()
