export type Company = {
  id: string;
  name: string;
  ticker: string;
  sector: string;
  marketCap: string;
  logo?: string;
  historicalNewsAvailable?: boolean; // FNSPID data (2000-2023)
  etfSubSector?: string; // MOAT ETF technology sub-sector
  isMoatEtfHolding?: boolean;
};

