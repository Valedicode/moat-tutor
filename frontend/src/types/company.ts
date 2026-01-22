export type Company = {
  id: string;
  name: string;
  ticker: string;
  sector: string;
  marketCap: string;
  logo?: string;
  historicalNewsAvailable?: boolean; // FNSPID data (2015-2023)
};

