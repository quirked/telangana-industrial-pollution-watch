DISTRICTS = (
    "Adilabad", "Bhadradri Kothagudem", "Hanumakonda", "Hyderabad",
    "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal",
    "Kamareddy", "Karimnagar", "Khammam", "Kumuram Bheem", "Mahabubabad",
    "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu",
    "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad",
    "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy",
    "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal",
    "Yadadri Bhuvanagiri",
)

OBSERVATION_TYPES = (
    "Smoke / Air Emission",
    "Dust / Particulate Emission",
    "Fumes / Strong Industrial Odor",
    "Effluent / Wastewater Discharge",
    "Oily Discharge",
    "Industrial Waste Dumping",
    "Chemical-looking Discharge",
    "Other",
)

INDUSTRY_TYPES = (
    "Pharmaceuticals / Bulk Drugs / APIs", "Thermal Power", "Cement / Clinker",
    "Steel / Sponge Iron", "Mining / Washery", "Rice Mill",
    "Distillery / Sugar", "Chemical Industry", "Tyre / Rubber Processing",
    "General Manufacturing", "Other", "Unknown",
)

STATUSES = (
    "Reported", "Under Review", "Verified", "Action in Progress", "Resolved", "Rejected",
)

STATUS_DESCRIPTIONS = {
    "Reported": "Observation received",
    "Under Review": "Initial review underway",
    "Verified": "Report reviewed by authority",
    "Action in Progress": "Response action recorded",
    "Resolved": "Response process completed",
    "Rejected": "Report closed after review",
}
