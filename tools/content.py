"""Content data for the Lotus Sun Energy website: FAQ, glossary, national solar facts and government schemes.

Edit here, then run python3 tools/build.py. Keep every figure sourced, and never claim a project or client
here or anywhere on the site unless it really happened: Lotus Sun Energy is a new company.
"""

# ------------------------------------------------------------------ FAQ ----
# (topic, [(question, answer)]). Answers may contain inline HTML links.
FAQ = [
    ("Cost and savings", [
        ("How much does rooftop solar cost for a home in India?",
         "As a guide, a home rooftop system costs roughly Rs 55,000 to Rs 65,000 per kW before subsidy, depending on the roof, the structure "
         "height and the components. A typical 3 kW home system therefore costs about Rs 1.7 to 2 lakh, and the PM Surya Ghar subsidy brings "
         "Rs 78,000 of that back. Use our <a href=\"/#calculator\">savings calculator</a> for your own numbers; the exact price comes after a free site visit."),
        ("How much will I save on my electricity bill?",
         "Most homes that size the system to their usage cut their bill by 70 to 90%. Each kW of panels makes roughly 4 units a day on average "
         "in most of India (about 1,400 to 1,500 units a year), so at Rs 7 to 8 a unit a 3 kW system saves around Rs 2,500 to 3,000 a month."),
        ("How long does solar take to pay for itself?",
         "For a home with the subsidy, typically 3 to 5 years. Businesses without the subsidy usually see 3 to 6 years, depending on the tariff "
         "and how much of the power is used during the day. After that the system keeps generating for 25 years or more."),
        ("What size of system do I need?",
         "A quick rule: bills around Rs 1,000 to 2,500 a month suit 1 to 2 kW, Rs 2,500 to 4,500 suit about 3 kW, and bills above Rs 5,000 need "
         "5 kW or more. We confirm the size from your bills, sanctioned load and roof during the site visit."),
    ]),
    ("Subsidy and finance", [
        ("What government subsidy can I get for home solar?",
         "Under <a href=\"/pm-surya-ghar-subsidy/\">PM Surya Ghar: Muft Bijli Yojana</a> the central subsidy is Rs 30,000 per kW for the first 2 kW "
         "and Rs 18,000 for the 3rd kW: Rs 30,000 for 1 kW, Rs 60,000 for 2 kW and Rs 78,000 for 3 kW or more. Housing societies get Rs 18,000 "
         "per kW for common facilities. Some states add their own top-up."),
        ("Who is eligible for the PM Surya Ghar subsidy?",
         "A household with its own electricity connection, a suitable roof it owns, and no earlier solar subsidy on the same connection. "
         "The system must be grid-connected with net metering and use Indian-made (DCR) modules, installed by a vendor registered on the portal."),
        ("Do you handle the subsidy paperwork?",
         "Yes. We register you on the national portal, file the DISCOM feasibility and net-metering application, arrange the inspection after "
         "installation and follow the claim until the subsidy reaches your bank account."),
        ("Can I pay in EMIs?",
         "Yes. Banks offer solar loans, and for home systems up to 3 kW the scheme provides collateral-free loans at around 7% interest. "
         "In many cases the EMI is close to the bill it replaces, so you save from the first month. We guide you through the paperwork."),
        ("Do businesses get any benefit?",
         "Businesses do not get the PM Surya Ghar subsidy, but a business that owns its plant can usually claim "
         "<a href=\"/accelerated-depreciation-solar/\">accelerated depreciation</a>, and GST on solar modules is 5%. Ask your chartered accountant to confirm."),
    ]),
    ("Your roof and site", [
        ("Is my roof suitable for solar?",
         "Most are. You need roughly 80 to 100 sq ft of shade-free roof per kW, facing south, east or west, without tall trees or buildings "
         "shading it between 9 AM and 4 PM. RCC and metal-sheet roofs both work; we check the strength and shade on the site visit."),
        ("Will the panels damage my roof or cause leaks?",
         "No. On RCC roofs we use raised structures on concrete or chemically anchored bases with waterproofing at each fixing; on metal sheets "
         "we use clamps or sealed fixings matched to the sheet profile. The structure is designed for the wind speed of your area."),
        ("I live in a rented house or flat. Can I still go solar?",
         "The subsidy needs a roof the applicant owns. In an apartment, the housing society can install solar for common areas (lifts, pumps, "
         "lighting) and claim the society subsidy. Talk to us and we will suggest what is possible."),
        ("Do you install ground-mount solar on open land?",
         "Yes. For farms, factories and institutions with spare land we design and build ground-mount plants, including soil checks, pile "
         "foundations, structures, fencing and the grid connection. See <a href=\"/service-ground-mount/\">ground-mount solar</a>."),
    ]),
    ("Installation and approvals", [
        ("How long does installation take?",
         "For a typical home, the physical installation takes 2 to 4 days. The whole process, including portal registration, DISCOM "
         "feasibility, net meter and inspection, usually takes a few weeks, depending on your DISCOM."),
        ("What is net metering?",
         "A two-way meter records the power you draw from the grid and the surplus solar power you send to it. You pay only for the net units, "
         "and summer surplus can offset monsoon months within the settlement period. See our <a href=\"/net-metering-india/\">net metering guide</a>."),
        ("Does solar work during a power cut?",
         "A standard grid-connected (on-grid) system shuts down during a grid outage for the safety of line workers. If you want power during "
         "cuts, choose a hybrid system with batteries; we will explain the cost difference honestly."),
        ("Which panels and inverters do you use?",
         "We do not manufacture equipment. We specify BIS-certified, ALMM-listed modules (Indian-made DCR modules where the subsidy needs them) "
         "and reliable on-grid or hybrid inverters with monitoring, with the makes and warranties written into your quote."),
    ]),
    ("Maintenance and performance", [
        ("Does solar work in the monsoon and in winter?",
         "Yes, at lower output. Panels generate on cloudy days, just less. Over a year the sunny months more than make up for it, and net "
         "metering lets you bank the surplus."),
        ("How much maintenance does solar need?",
         "Very little: rinse the panels with plain water every 2 to 4 weeks (more often in dusty areas), keep shade-causing branches trimmed, "
         "and get a yearly check of the wiring, earthing and inverter. We offer <a href=\"/service-om/\">maintenance plans</a> for larger systems."),
        ("How long do solar panels last?",
         "Quality modules come with a 25 to 30 year performance warranty and keep producing well beyond that, losing only a small percentage of "
         "output each year. Inverters typically last 10 to 15 years."),
    ]),
    ("About Lotus Sun Energy", [
        ("Who is Lotus Sun Energy?",
         "A new, veteran-led solar company from Muzaffarpur, Bihar. We are led by ex-servicemen and bring the same discipline, honesty and "
         "commitment that served the nation to powering India's homes and businesses with clean solar energy."),
        ("Where do you work?",
         "Our office is in Pakhanaha Sriram, Muzaffarpur, Bihar, and we offer free site visits across India."),
        ("What services do you offer?",
         "Rooftop solar for homes, societies and businesses; ground-mount plants; turnkey EPC on the CAPEX model; installation and "
         "commissioning; pile foundations and civil works; and operation and maintenance."),
        ("How do I get a quote?",
         "Fill in the <a href=\"/free-solar-quote/\">free quote form</a>, use the <a href=\"/contact/\">contact form</a> or email "
         "info@lotussunenergy.com with your location and a recent electricity bill. We reply within one working day and book a free site visit."),
    ]),
]

# ------------------------------------------------------------ glossary ----
GLOSSARY = [
    ("ACDB / DCDB", "AC and DC distribution boards: the enclosures that house the fuses, isolators and surge protection between the panels, the inverter and the grid connection."),
    ("Accelerated depreciation", "A tax benefit that lets a business that owns a solar plant write off its cost faster than normal assets, reducing taxable income in the early years."),
    ("ALMM", "Approved List of Models and Manufacturers: the list of solar modules (and, from June 2026, cells) approved by the Ministry of New and Renewable Energy (MNRE) for covered projects."),
    ("Balance of system (BOS)", "Everything in a solar system except the panels: mounting structures, inverters, cables, distribution boards, earthing, lightning protection and monitoring."),
    ("Bifacial module", "A solar module that generates power from both sides, using light reflected from the roof or ground onto its rear face."),
    ("CAPEX model", "You pay for the solar system upfront (or with a loan) and own it outright, keeping all the savings."),
    ("Commissioning", "The final stage of an installation: testing every component, synchronising the system with the grid and handing it over ready to generate."),
    ("CUF (capacity utilisation factor)", "The energy a system actually generates in a year as a percentage of what it would generate running at full capacity all year."),
    ("DCR (domestic content requirement)", "A rule in some government schemes, including PM Surya Ghar, that modules and cells must be made in India."),
    ("DISCOM", "Your electricity distribution company, which approves net metering, installs the bi-directional meter and inspects grid-connected systems."),
    ("Earthing", "Connecting the system's metal structures and electrical equipment to the ground so that fault currents and lightning are carried safely away."),
    ("EMI", "Equated monthly instalment: paying for a solar system in fixed monthly amounts through a loan instead of all at once."),
    ("EPC", "Engineering, procurement and construction: a single contract covering the design, equipment purchase and building of the whole system."),
    ("Grid-connected (on-grid) system", "A solar system connected to the utility grid, which can draw from or export to the grid; the most common type for homes and businesses."),
    ("Ground-mount solar", "Panels installed on structures fixed to the ground, typically on pile foundations; used for farms, factories and open land."),
    ("Hybrid system", "A solar system with batteries that also connects to the grid, so it can keep essential loads running during power cuts."),
    ("I&C (installation & commissioning)", "The on-site work of building a solar system to an agreed design and bringing it into operation: structures, panels, cabling, inverters, earthing, testing and commissioning."),
    ("Inverter", "The equipment that converts the direct current (DC) from the panels into alternating current (AC) for use at home or export to the grid."),
    ("kW / kWp", "Kilowatt and kilowatt-peak: the rated output of a solar system under standard test conditions. A 3 kW home system has about 3 kWp of panels."),
    ("kWh (unit)", "A kilowatt-hour, the 'unit' on your electricity bill. In most of India, 1 kW of panels makes about 4 units a day on average."),
    ("Lightning arrestor", "A device that intercepts lightning strikes and conducts them safely to earth, protecting panels and equipment."),
    ("MMS (module mounting structure)", "The steel or aluminium frame that holds the panels at the designed tilt and height."),
    ("National Portal", "pmsuryaghar.gov.in, the website where households apply for the PM Surya Ghar subsidy and choose a registered vendor."),
    ("Net metering", "A billing arrangement where the power your solar system exports to the grid is offset against the power you draw from it."),
    ("Off-grid system", "A solar system with batteries that is not connected to the grid; used where there is no reliable grid supply."),
    ("OPEX / RESCO model", "A developer finances and owns the plant on your roof or land, and you buy its power at an agreed tariff for many years."),
    ("Payback period", "The time it takes for the savings on your electricity bill to equal what you paid for the solar system."),
    ("Performance ratio (PR)", "Actual energy generated divided by the theoretical energy available from the sunlight; a measure of how well a system is built and maintained."),
    ("Pile foundation", "A steel or concrete pile driven or cast into the ground to anchor the mounting structures of a ground-mount plant."),
    ("PM Surya Ghar: Muft Bijli Yojana", "The central government scheme that subsidises rooftop solar for homes: up to Rs 78,000 for a system of 3 kW or more."),
    ("Rooftop solar", "Panels installed on a building's RCC or metal-sheet roof, turning unused roof space into a power source."),
    ("Sanctioned load", "The maximum load (in kW or kVA) your DISCOM has approved for your connection; it usually caps the size of a net-metered system."),
    ("Shadow analysis", "A check of where trees, water tanks, parapets and nearby buildings cast shade on the roof through the day and year, so panels go where the sun is."),
    ("Tier-1 module", "A module from a large, bankable manufacturer with an established production and financing track record."),
    ("TOPCon", "Tunnel oxide passivated contact: a high-efficiency solar cell technology now common in new modules."),
]

# ------------------------------------------------------- national facts ----
NATIONAL_FACTS = [
    dict(num="500", suffix=" GW", label="Non-fossil capacity target for 2030: the first of the Prime Minister's Panchamrit commitments at COP26",
         url="https://pib.gov.in/PressReleasePage.aspx?PRID=1768712"),
    dict(num="283.46", suffix=" GW", label="Non-fossil capacity installed in India as on 31 March 2026",
         url="https://pib.gov.in/PressReleasePage.aspx?PRID=2250039"),
    dict(num="50", suffix="%", label="Share of India's installed power capacity from non-fossil sources, reached June 2025",
         url="https://pib.gov.in/PressReleasePage.aspx?PRID=2250039"),
    dict(num="164.59", suffix=" GW", label="Solar capacity installed in India as on 31 July 2026 (MNRE data)",
         url="https://solarquarter.com/2026/08/12/indias-solar-capacity-surpasses-164-gw-as-2026-installations-approach-29-gw-by-july-end/"),
    dict(num="75", suffix=" lakh", label="Households targeted for rooftop solar under PM Surya Ghar by December 2026, on the way to 1 crore",
         url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2268992"),
]


# -------------------------------------------------------------- schemes ----
SCHEMES = [
    # (title, who, points, where we fit, source name, source url, in-depth guide, status in October 2026)
    ("PM Surya Ghar: Muft Bijli Yojana", "Homes & housing societies",
     ["Launched on 13 February 2024; approved by the Union Cabinet on 29 February 2024 with an outlay of Rs 75,021 crore",
      "Central subsidy: Rs 30,000 for 1 kW, Rs 60,000 for 2 kW and Rs 78,000 for 3 kW or more",
      "Housing societies and RWAs: Rs 18,000 per kW for common facilities, up to 500 kW",
      "Collateral-free loans of around 7% for home systems up to 3 kW; Indian-made (DCR) modules and a registered vendor required",
      "Target: 75 lakh households by December 2026, on the way to 1 crore"],
     "We register you on the national portal, file the DISCOM feasibility and net-metering papers, install a DCR-compliant system and follow the subsidy claim to your bank account.",
     "PIB", "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2268992", "pm-surya-ghar-subsidy.html", "Open; apply on pmsuryaghar.gov.in"),
    ("PM-KUSUM", "Farmers, cooperatives, panchayats, FPOs",
     ["Component A: grid-connected solar plants of 500 kW to 2 MW on farmers' land, power bought by the DISCOM",
      "Component B: standalone solar pumps, with 30% central support (50% in the North-East, hill states and islands) plus state support",
      "Component C: solarisation of grid-connected pumps, individually or by whole feeders",
      "Financial closure for Components A and C extended to 30 November 2026; completion by 31 March 2027, with no further extension",
      "PM-KUSUM 2.0, with about 10 GW for agri-photovoltaics, announced but not yet notified"],
     "Component A and feeder-level plants are ground-mount plants: we can design and build them, including piling, fencing, civil works, installation and commissioning.",
     "Energetica India", "https://energetica-india.net/news/mnre-extends-pm-kusum-financial-closure-deadline-to-nov-30", "pm-kusum-scheme.html", "Closing: complete by 31 Mar 2027"),
    ("Accelerated depreciation", "Businesses that own their plant",
     ["Solar power generating systems are depreciated at 40% a year on the written-down value",
      "The Income-tax Act, 2025 applies from 1 April 2026; the 40% rate for qualifying solar assets is reported to continue",
      "Half the year's depreciation if the plant is used for less than 180 days in its first year"],
     "Every plant we build on the CAPEX model belongs to the client, so the depreciation is theirs. Confirm the position with your chartered accountant.",
     "Taxguru: Income-tax Act, 2025", "https://taxguru.in/income-tax/depreciation-income-tax-act-2025-section-34-rates-provisions.html", "accelerated-depreciation-solar.html", "Available to business owners"),
    ("GST on solar at 5%", "Everyone buying a solar plant",
     ["The 56th GST Council cut GST on solar cells, modules and specified devices from 12% to 5%, effective 22 September 2025",
      "EPC contracts: 70% goods at 5% and 30% services at 18%, about 8.9% overall",
      "The Andhra Pradesh High Court upheld the 70:30 method for a solar EPC contract in December 2025"],
     "We set out supply and services clearly in every quotation, so the tax treatment is transparent from the start.",
     "pv magazine India, 4 Sep 2025", "https://www.pv-magazine-india.com/2025/09/04/gst-on-solar-cells-modules-cut-to-5/", "gst-on-solar-india.html", "In force"),
    ("Net metering and time-of-day tariffs", "Grid-connected consumers",
     ["Net metering up to 500 kW or the sanctioned load, whichever is lower, under the national consumer rules; states set the details",
      "Above that, net billing or gross metering",
      "Time-of-day tariffs make solar hours cheaper and evening peaks dearer",
      "Draft amendment of March 2026 proposes charges above 5 kW and storage above 500 kW; check whether it has been notified"],
     "We handle the net-metering application, the DISCOM inspection and, for larger plants, the electrical inspector's (CEIG) approval.",
     "Mercom India", "https://www.mercomindia.com/government-proposes-amendments-to-electricity-consumer-rights-rules", "net-metering-india.html", "In force; 2026 changes in draft"),
    ("Green Energy Open Access", "Consumers of 100 kW and more",
     ["Buy green power from an off-site plant from 100 kW of load (down from 1 MW); captive consumers have no minimum",
      "Connections in the same electricity division can be aggregated (2023 amendment)",
      "Single-window applications on the national GOAR portal, with deemed approval if not decided in time",
      "The ISTS charges waiver ended for projects commissioned after 30 June 2025 and is phasing out in steps"],
     "Captive and open-access plants are usually ground-mount plants: we can take on the piling, civil works, fencing and installation & commissioning.",
     "GOAR portal", "https://greenopenaccess.in/", "green-energy-open-access.html", "In force; state charges vary"),
    ("ALMM List-I and List-II", "Projects covered by the ALMM order",
     ["List-I sets which solar modules may be used in covered projects",
      "From 1 June 2026, List-II for solar cells applies: covered projects need List-I modules made with List-II cells",
      "Exemptions for projects whose bid deadline was before the amendment, and for net-metering and open-access projects commissioned before 1 June 2026",
      "A List-III for wafers is reported for June 2028"],
     "We do not manufacture modules, so we specify the ALMM-listed or client-approved makes each project needs and keep the documents.",
     "PIB", "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2082901", "almm-list-ii-solar-cells.html", "In force from 1 June 2026"),
    ("Customs duty on modules and cells", "Anyone importing equipment",
     ["Budget 2025-26: BCD on modules cut to 20% with a 20% AIDC (about 40% combined); on cells to 20% with 7.5% AIDC",
      "Budget 2026-27 left the headline rates unchanged and removed duty on a solar-glass input",
      "Anti-dumping duty on Chinese-origin cells and modules recommended in September 2025; check the current notification"],
     "For most home, business and scheme projects the route is now Indian ALMM modules; we compare options and paperwork before you commit.",
     "Energetica India", "https://www.energetica-india.net/news/union-budget-2025-26-solar-cells-and-modules-duty-cut-to-20-percent", "solar-import-duty-india.html", "In force"),
    ("BIS Quality Control Order", "Every plant: modules, inverters, batteries",
     ["Solar Systems, Devices and Components Goods Order, 2025, notified 27 January 2025",
      "Modules, solar inverters and storage batteries must meet Indian Standards and carry the BIS mark",
      "Inverters above 200 kW given extra time on self-certification, reportedly to the end of 2026"],
     "We check BIS and ALMM documents for every component on site and hand them over with the test reports.",
     "PIB", "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2097219", "solar-quality-standards-bis-cea.html", "In force"),
    ("Storage with solar", "Utility tenders and large prosumers",
     ["Power Ministry advisory (Feb 2025): two-hour co-located storage equal to 10% of capacity in future solar tenders",
      "Viability gap funding for battery storage; a second tranche of about Rs 5,400 crore announced in 2025",
      "ISTS waiver for co-located BESS commissioned by 30 June 2028"],
     "We can add batteries where backup matters; for most homes and businesses a grid-connected system sized to daytime use pays back fastest.",
     "pv magazine India", "https://www.pv-magazine-india.com/2025/02/20/power-ministry-mandates-co-locating-energy-storage-with-solar-projects/", "battery-storage-with-solar.html", "Advisory for future tenders"),
]


# ----------------------------------------------------------- panchamrit ----
# Verbatim from the Prime Minister's national statement at COP26, Glasgow (PIB, 1 Nov 2021).
PANCHAMRIT_URL = "https://pib.gov.in/PressReleasePage.aspx?PRID=1768712"
PANCHAMRIT = [
    "India will reach its non-fossil energy capacity to 500 GW by 2030.",
    "India will meet 50 percent of its energy requirements from renewable energy by 2030.",
    "India will reduce the total projected carbon emissions by one billion tonnes from now onwards till 2030.",
    "By 2030, India will reduce the carbon intensity of its economy by less than 45 percent.",
    "By the year 2070, India will achieve the target of Net Zero.",
]

