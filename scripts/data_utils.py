from secedgar.core import CompanyFilings, FilingType

def get_audits(ticker: str, output_dir: str):
    filing = CompanyFilings(cik_lookup=ticker, filing_type=FilingType.FILING_10K)
    filing.save(output_dir)