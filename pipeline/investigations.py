"""Investigation records (ARCHITECTURE.md 5.2). Text is copied from each PSI page (data/text/PSI-*.txt).

test_count is filled in by build_tests.py from the cleaned rows.
"""
from pipeline.schema import psi_url

SAFFIRE_SENSORS = ["2 cameras", "thermocouples", "2 radiometers", "pressure, CO2 and O2 sensors", "2 anemometers"]

INVESTIGATIONS = [
    {
        "id": "BASS-II",
        "psi_id": "PSI-25",
        "title": "Burning and Suppression of Solids - II",
        "area": ["prevention"],
        "objective": "Study the ignition, flame growth, flame spread, and extinction limits for solid fuels "
                     "burning in low-velocity forced flows in microgravity.",
        "hardware": "Microgravity Science Glovebox (MSG)",
        "fuels": ["solid"],
        "sensors": ["imaging", "radiometer", "O2, CO2 and CO measurements"],
        "source_url": psi_url("PSI-25"),
    },
    {
        "id": "SAFFIRE-II",
        "psi_id": "PSI-99",
        "title": "Spacecraft Fire Experiment-II",
        "area": ["prevention"],
        "objective": "The objectives of SAFFIRE-II are to determine how rapidly a large scale fire grows in "
                     "low-gravity and to investigate the low-g flammability limits compared to those obtained "
                     "in NASA’s normal gravity material flammability screening test.",
        "hardware": "Cygnus Pressurized Cargo Module; SAFFIRE",
        "fuels": ["solid"],
        "sensors": SAFFIRE_SENSORS,
        "source_url": psi_url("PSI-99"),
    },
    {
        "id": "SAFFIRE-III",
        "psi_id": "PSI-100",
        "title": "Spacecraft Fire Experiment-III",
        "area": ["prevention", "detection"],
        "objective": "(1) determine how rapidly a large scale fire grows in low-gravity and (2) investigate "
                     "the low-g flammability limits compared to those obtained in NASA’s normal gravity "
                     "material flammability screening test.",
        "hardware": "Saffire III enclosure in Cygnus",
        "fuels": ["solid"],
        "sensors": SAFFIRE_SENSORS,
        "source_url": psi_url("PSI-100"),
    },
    {
        "id": "FLEX",
        "psi_id": "PSI-69",
        "title": "Flame Extinguishment Experiment",
        "area": ["suppression"],
        "objective": "The FLEX (Flame Extinguishment Experiment) investigation aims to map the flammability "
                     "limits of liquid fuels in microgravity environments, measure the effectiveness of various "
                     "gaseous fire suppressants such as CO2, He, and SF6, and develop reliable predictive models "
                     "for combustion limits under reduced gravity conditions.",
        "hardware": "Combustion Integrated Rack (CIR)-Fluids and Combustion Facility (FCF); "
                    "Multi-user Droplet Combustion Appartatus (MDCA)",
        "fuels": ["liquid"],
        "sensors": [],
        "source_url": psi_url("PSI-69"),
    },
]
