"""
Company metadata and moat information endpoints.
"""

from typing import List

from fastapi import APIRouter, HTTPException

from api.models.company import Company, CompanyMoat, CompaniesListResponse, MoatCharacteristic

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


# Mock company data (will be replaced with database in production)
COMPANIES_DB = [
    Company(
        id="aapl",
        name="Apple Inc.",
        ticker="AAPL",
        sector="Technology",
        market_cap="$2.8T",
        description="Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide."
    ),
    Company(
        id="nvda",
        name="Nvidia Corporation",
        ticker="NVDA",
        sector="Semiconductors",
        market_cap="$1.2T",
        description="NVIDIA Corporation provides graphics, compute, and networking solutions worldwide."
    ),
    Company(
        id="msft",
        name="Microsoft Corporation",
        ticker="MSFT",
        sector="Technology",
        market_cap="$2.4T",
        description="Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide."
    ),
    Company(
        id="googl",
        name="Alphabet Inc.",
        ticker="GOOGL",
        sector="Technology",
        market_cap="$1.7T",
        description="Alphabet Inc. provides various products and platforms in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America."
    ),
    Company(
        id="amzn",
        name="Amazon.com, Inc.",
        ticker="AMZN",
        sector="E-commerce & Cloud",
        market_cap="$1.5T",
        description="Amazon.com, Inc. engages in the retail sale of consumer products and subscriptions in North America and internationally."
    ),
    Company(
        id="meta",
        name="Meta Platforms, Inc.",
        ticker="META",
        sector="Social Media",
        market_cap="$900B",
        description="Meta Platforms, Inc. engages in the development of products that enable people to connect and share with friends and family through mobile devices, personal computers, virtual reality headsets, and wearables worldwide."
    ),
]


# Mock moat data
MOAT_DB = {
    "AAPL": CompanyMoat(
        ticker="AAPL",
        company_name="Apple Inc.",
        overall_moat_rating="Wide",
        characteristics=[
            MoatCharacteristic(
                name="Network Effects",
                strength="Strong",
                description="Apple's ecosystem creates powerful network effects. The more people who use Apple devices, the more valuable the ecosystem becomes through features like iMessage, FaceTime, AirDrop, and seamless device integration."
            ),
            MoatCharacteristic(
                name="Intangible Assets",
                strength="Strong",
                description="Apple has one of the world's most valuable brands, extensive patents, proprietary chip designs (M-series, A-series), and exclusive relationships with premium app developers."
            ),
            MoatCharacteristic(
                name="Switching Costs",
                strength="Strong",
                description="High switching costs due to ecosystem lock-in. Users would lose purchased apps, media, integration between devices, and face a learning curve when switching platforms."
            ),
            MoatCharacteristic(
                name="Cost Advantages",
                strength="Moderate",
                description="Scale advantages in manufacturing and supply chain, though margins come more from premium pricing than cost leadership."
            ),
            MoatCharacteristic(
                name="Efficient Scale",
                strength="Weak",
                description="The smartphone market allows multiple competitors. Apple succeeds through differentiation rather than being the only viable player."
            ),
        ],
        summary="Apple has a wide economic moat primarily driven by powerful network effects, brand strength, and high switching costs within its ecosystem. The integration of hardware, software, and services creates a self-reinforcing cycle that makes it difficult for customers to leave and competitors to replicate."
    ),
    "MSFT": CompanyMoat(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        overall_moat_rating="Wide",
        characteristics=[
            MoatCharacteristic(
                name="Network Effects",
                strength="Strong",
                description="Microsoft's products become more valuable as more users adopt them. Office suite compatibility, Teams collaboration, and Azure enterprise adoption all exhibit network effects."
            ),
            MoatCharacteristic(
                name="Intangible Assets",
                strength="Strong",
                description="Strong brand in enterprise, extensive patent portfolio, and proprietary technologies across Windows, Azure, and Office."
            ),
            MoatCharacteristic(
                name="Switching Costs",
                strength="Strong",
                description="Enterprise customers face high switching costs due to deep integration of Microsoft products, employee training, data migration costs, and dependency on Microsoft-specific workflows."
            ),
            MoatCharacteristic(
                name="Cost Advantages",
                strength="Strong",
                description="Massive scale in cloud infrastructure (Azure), software development, and enterprise relationships provide significant cost advantages."
            ),
            MoatCharacteristic(
                name="Efficient Scale",
                strength="Moderate",
                description="Cloud and enterprise software markets have room for multiple players, though Microsoft's dominance in productivity software approaches efficient scale."
            ),
        ],
        summary="Microsoft has a wide moat built on enterprise dominance, high switching costs, and network effects. Its transition to cloud services has strengthened its competitive position."
    ),
    "GOOGL": CompanyMoat(
        ticker="GOOGL",
        company_name="Alphabet Inc.",
        overall_moat_rating="Wide",
        characteristics=[
            MoatCharacteristic(
                name="Network Effects",
                strength="Strong",
                description="Google Search improves with more users and queries. The advertising platform becomes more valuable as more advertisers and users participate."
            ),
            MoatCharacteristic(
                name="Intangible Assets",
                strength="Strong",
                description="Dominant brand in search, vast proprietary data on user behavior, advanced AI/ML algorithms, and patents."
            ),
            MoatCharacteristic(
                name="Switching Costs",
                strength="Moderate",
                description="Moderate switching costs for consumers (habit, data). Higher for advertisers due to platform expertise and campaign history."
            ),
            MoatCharacteristic(
                name="Cost Advantages",
                strength="Strong",
                description="Massive scale in data centers, AI infrastructure, and advertising technology provides significant cost advantages over competitors."
            ),
            MoatCharacteristic(
                name="Efficient Scale",
                strength="Strong",
                description="Google's dominance in search approaches efficient scale - the market can only support a limited number of competitors profitably."
            ),
        ],
        summary="Google has a wide moat driven by network effects in search and advertising, massive data advantages, and efficient scale. Its dominance in search creates a self-reinforcing cycle."
    ),
    "NVDA": CompanyMoat(
        ticker="NVDA",
        company_name="Nvidia Corporation",
        overall_moat_rating="Wide",
        characteristics=[
            MoatCharacteristic(
                name="Network Effects",
                strength="Moderate",
                description="CUDA ecosystem creates network effects - more developers using CUDA leads to more optimized software, attracting more users."
            ),
            MoatCharacteristic(
                name="Intangible Assets",
                strength="Strong",
                description="Extensive patents in GPU technology, CUDA software platform, and strong brand in gaming and AI computing."
            ),
            MoatCharacteristic(
                name="Switching Costs",
                strength="Strong",
                description="High switching costs for enterprises that have built AI infrastructure and models on CUDA. Developers face retraining and code migration costs."
            ),
            MoatCharacteristic(
                name="Cost Advantages",
                strength="Moderate",
                description="Scale advantages in R&D and manufacturing partnerships, though semiconductor economics limit pure cost leadership."
            ),
            MoatCharacteristic(
                name="Efficient Scale",
                strength="Weak",
                description="GPU market has room for multiple competitors (AMD, Intel), though NVIDIA leads in performance and ecosystem."
            ),
        ],
        summary="NVIDIA has a wide moat primarily from switching costs (CUDA ecosystem), technological leadership, and intangible assets. Its dominance in AI computing strengthens its competitive position."
    ),
    "AMZN": CompanyMoat(
        ticker="AMZN",
        company_name="Amazon.com, Inc.",
        overall_moat_rating="Wide",
        characteristics=[
            MoatCharacteristic(
                name="Network Effects",
                strength="Strong",
                description="Amazon's marketplace exhibits strong network effects - more sellers attract more buyers and vice versa. AWS benefits from ecosystem effects."
            ),
            MoatCharacteristic(
                name="Intangible Assets",
                strength="Moderate",
                description="Strong brand in e-commerce and cloud, proprietary logistics technology, and customer data."
            ),
            MoatCharacteristic(
                name="Switching Costs",
                strength="Moderate",
                description="Prime membership creates moderate switching costs. AWS customers face migration costs and learning curves."
            ),
            MoatCharacteristic(
                name="Cost Advantages",
                strength="Strong",
                description="Massive scale in logistics, warehousing, and cloud infrastructure provides significant cost advantages."
            ),
            MoatCharacteristic(
                name="Efficient Scale",
                strength="Strong",
                description="Amazon's logistics network and AWS infrastructure approach efficient scale - few competitors can match the required investment."
            ),
        ],
        summary="Amazon has a wide moat driven by network effects in its marketplace, cost advantages from scale, and efficient scale in logistics and cloud. AWS strengthens the overall competitive position."
    ),
    "META": CompanyMoat(
        ticker="META",
        company_name="Meta Platforms, Inc.",
        overall_moat_rating="Wide",
        characteristics=[
            MoatCharacteristic(
                name="Network Effects",
                strength="Strong",
                description="Social networks have powerful network effects - platforms become more valuable as more friends and family join."
            ),
            MoatCharacteristic(
                name="Intangible Assets",
                strength="Strong",
                description="Strong brands (Facebook, Instagram, WhatsApp), proprietary algorithms, and vast user behavior data."
            ),
            MoatCharacteristic(
                name="Switching Costs",
                strength="Strong",
                description="High switching costs due to social graph - users' entire network of connections and shared history."
            ),
            MoatCharacteristic(
                name="Cost Advantages",
                strength="Moderate",
                description="Scale advantages in advertising technology and infrastructure, though ad-supported model limits pure cost leadership."
            ),
            MoatCharacteristic(
                name="Efficient Scale",
                strength="Moderate",
                description="Social media market can support multiple large players, though network effects create winner-take-most dynamics."
            ),
        ],
        summary="Meta has a wide moat primarily from network effects and switching costs in social networking. The social graph creates powerful barriers to competition."
    ),
}


@router.get("", response_model=CompaniesListResponse)
async def list_companies() -> CompaniesListResponse:
    """
    List all available companies.
    
    Returns information about companies available for analysis in the system.
    
    Returns:
        List of companies with metadata
    """
    return CompaniesListResponse(
        companies=COMPANIES_DB,
        total=len(COMPANIES_DB)
    )


@router.get("/{ticker}", response_model=Company)
async def get_company(ticker: str) -> Company:
    """
    Get detailed information about a specific company.
    
    Args:
        ticker: Stock ticker symbol (case-insensitive)
        
    Returns:
        Company information
        
    Raises:
        HTTPException: If company not found
    """
    ticker_upper = ticker.upper()
    
    for company in COMPANIES_DB:
        if company.ticker == ticker_upper:
            return company
    
    raise HTTPException(
        status_code=404,
        detail=f"Company with ticker '{ticker}' not found"
    )


@router.get("/{ticker}/moat", response_model=CompanyMoat)
async def get_company_moat(ticker: str) -> CompanyMoat:
    """
    Get detailed moat analysis for a company.
    
    Returns the company's competitive advantages analyzed through the MOAT framework:
    - Network Effects
    - Switching Costs
    - Intangible Assets
    - Cost Advantages
    - Efficient Scale
    
    Args:
        ticker: Stock ticker symbol (case-insensitive)
        
    Returns:
        Detailed moat analysis
        
    Raises:
        HTTPException: If company not found or moat data not available
    """
    ticker_upper = ticker.upper()
    
    if ticker_upper not in MOAT_DB:
        raise HTTPException(
            status_code=404,
            detail=f"Moat data not available for ticker '{ticker}'"
        )
    
    return MOAT_DB[ticker_upper]

