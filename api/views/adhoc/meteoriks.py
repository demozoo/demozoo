import csv

from django.contrib.humanize.templatetags.humanize import ordinal as original_ordinal
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse

from pouet.models import Production as PouetProduction
from productions.models import Production, ProductionType


def ordinal(val):
    if isinstance(val, str) and val.startswith("="):  # pragma: no cover
        return ".=" + original_ordinal(val[1:])
    else:
        return original_ordinal(val)


POUET_OLDSCHOOL_PLATFORM_NAMES = [
    "Commodore 64",
    "Amstrad CPC",
    "ZX Spectrum",
    "Oric",
    "VIC 20",
    "MSX",
    "Atari XL/XE",
    "Commodore 128",
    "Apple II GS",
    "Apple II",
    "Atari VCS",
    "ZX-81",
    "BBC Micro",
    "TRS-80/CoCo/Dragon",
    "Commodore PET",
    "NES/Famicom",
    "BK-0010/11M",
    "Atari Lynx",
    "C16/116/plus4",
    "KC-85",
    "Thomson",
    "SAM Coupé",
    "MSX 2",
    "Gameboy",
    "Sharp MZ",
    "Amstrad Plus",
    "Gameboy Color",
    "Vectrex",
    "Atari 7800",
    "Vector-06c",
    "SEGA Master System",
    "Enterprise",
    "Sinclair QL",
    "TI-8x (Z80)",
]
POUET_MIDSCHOOL_PLATFORM_NAMES = [
    "MS-Dos",
    "MS-Dos/gus",
    "Atari ST",
    "Amiga AGA",
    "Atari STe",
    "Amiga OCS/ECS",
    "Amiga PPC/RTG",
    "Atari Falcon 030",
    "Atari TT 030",
    "Atari Jaguar",
    "PICO-8",
    "TIC-80",
    "MicroW8",
    "Acorn",
    "Wonderswan",
    "NEC TurboGrafx/PC Engine",
    "Gamecube",
    "Nintendo Wii",
    "Gameboy Advance",
    "SNES/Super Famicom",
    "Nintendo DS",
    "Nintendo 64",
    "Playstation Portable",
    "SEGA Genesis/Mega Drive",
    "Dreamcast",
    "Playstation",
    "Wonderswan",
    "MacOS",
    "ZX Enhanced",
    "C64DX/C65/MEGA65",
    "C64 DTV",
    "MacOSX PPC",
]
POUET_HIGHEND_PLATFORM_NAMES = [
    "Linux",
    "Windows",
    "MacOSX Intel",
    "JavaScript",
    "Raspberry Pi",
    "Android",
    "Java",
    "FreeBSD",
    "iOS",
    "Flash",
    "SGI/IRIX",
]
POUET_LIMBO_PLATFORM_NAMES = [
    "Animation/Video",
    "Wild",
    "Mobile Phone",
]

DZ_OLDSCHOOL_PLATFORM_NAMES = [
    "Amstrad CPC",
    "Atari 8 bit",
    "Commodore 64",
    "Nintendo Entertainment System (NES)",
    "Sharp MZ",
    "Commodore 128",
    "KC 85/Robotron KC 87",
    "ZX81",
    "ZX Spectrum",
    "Electronika BK-0010/11M",
    "Amstrad Plus",
    "Commodore PET",
    "Commodore 16/Plus 4",
    "Atari Lynx",
    "Apple II",
    "MSX",
    "BBC Micro",
    "Oric",
    "Apple II GS",
    "Thomson",
    "Commodore VIC-20",
    "Atari 2600 Video Computer System (VCS)",
    "SAM Coupé",
    "Nintendo Game Boy (GB)",
    "Nintendo Game Boy Color (GBC)",
    "Vector-06C",
    "Atari 7800 ProSystem",
    "Enterprise",
    "Calculator",
    "VTech Laser 200 / VZ 200",
    "Vectrex",
    "ZVT PP01",
    "PMD 85",
    "Vector-06C",
    "Sega Master System",
    "Atari Portfolio",
    "Sinclair QL",
    "TRS-80",
]
DZ_MIDSCHOOL_PLATFORM_NAMES = [
    "Amiga OCS/ECS",
    "TIC-80",
    "Atari Jaguar",
    "Atari TT",
    "Sony Playstation Portable (PSP)",
    "Atari ST/E",
    "Amiga AGA",
    "Atari Falcon",
    "Amiga PPC/RTG",
    "Fantasy Console",
    "MS-Dos",
    "Nintendo GameCube (NGC)",
    "PICO-8",
    "Sega Megadrive/Genesis",
    "Sega Dreamcast",
    "Acorn Archimedes",
    "Nintendo Game Boy Advance (GBA)",
    "Console Handheld",
    "NEC PC Engine",
    "Nintendo 3DS",
    "Nintendo 64 (N64)",
    "Nintendo SNES/Super FamiCom",
    "Nintendo Switch (NSW)",
    "NeoGeo",
    "MicroW8",
    "Sony Playstation 1 (PSX)",
    "Wonderswan",
    "Mac OS (Classic)",
    "Nintendo DS (NDS)",
    "ZX Spectrum Enhanced",
    "Nintendo Wii",
    "Commodore 64-DTV",
    "Sharp X68000",
    "Neo Geo",
]
DZ_HIGHEND_PLATFORM_NAMES = [
    "Windows",
    "Javascript",
    "FreeBSD",
    "Linux",
    "Java",
    "Android",
    "Browser",
    "Raspberry Pi",
    "macOS",
    "Flash",
]
DZ_LIMBO_PLATFORM_NAMES = [
    "Custom Hardware",
    "Mobile",
    "Paper",
]


def candidates(request, year):
    if not request.user.is_staff:
        raise PermissionDenied

    exe_graphics = ProductionType.objects.get(internal_name="exe-graphics")

    prods = (
        Production.objects.filter(
            Q(release_date_date__year=year) & (Q(supertype="production") | Q(types__path__startswith=exe_graphics.path))
        )
        .prefetch_related(
            "types",
            "platforms",
            "links",
            "author_nicks",
            "author_affiliation_nicks",
            "competition_placings__competition__party",
        )
        .order_by("sortable_title")
        .distinct()
    )

    pouet_prods = PouetProduction.objects.filter(Q(release_date_date__year=year)).prefetch_related(
        "groups",
        "platforms",
        "types",
        "competition_placings__party",
        "competition_placings__competition_type",
        "download_links",
    )
    pouet_prods_by_id = {prod.pouet_id: prod for prod in pouet_prods}

    response = HttpResponse(content_type="text/plain;charset=utf-8")
    csvfile = csv.writer(response)
    csvfile.writerow(
        [
            "category",
            "pouet_url",
            "demozoo_url",
            "title",
            "groups",
            "thumbup",
            "piggy",
            "thumbdown",
            "up-down",
            "avg",
            "cdcs",
            "popularity",
            "party",
            "type",
            "platform",
            "youtube",
        ]
    )

    def write_row(dz_prod, pouet_prod):
        youtube_links = []

        if pouet_prod:
            vote_diff = pouet_prod.vote_up_count - pouet_prod.vote_down_count
            vote_count = pouet_prod.vote_up_count + pouet_prod.vote_pig_count + pouet_prod.vote_down_count
            vote_avg = vote_diff / vote_count if vote_count else 0
            pouet_platform_names = [platform.name for platform in pouet_prod.platforms.all()]
            pouet_prodtype_names = [typ.name for typ in pouet_prod.types.all()]

            pouet_platform_category = set()
            if pouet_prodtype_names == ["demotool"] and "Windows" in pouet_platform_names:  # pragma: no cover
                pouet_platform_category.add("highend")
            elif pouet_prodtype_names == ["demotool"] and "MacOSX Intel" in pouet_platform_names:  # pragma: no cover
                pouet_platform_category.add("highend")
            elif pouet_prodtype_names == ["demotool"] and "JavaScript" in pouet_platform_names:  # pragma: no cover
                pouet_platform_category.add("highend")
            elif set(pouet_platform_names) == {"MS-Dos", "Windows"}:  # pragma: no cover
                pouet_platform_category.add("midschool")
            elif set(pouet_platform_names) == {"MS-Dos", "Linux"}:  # pragma: no cover
                pouet_platform_category.add("midschool")
            elif set(pouet_platform_names) == {"MS-Dos", "Windows", "MS-Dos/gus"}:  # pragma: no cover
                pouet_platform_category.add("midschool")
            elif set(pouet_platform_names) == {"Acorn", "Raspberry Pi"}:  # pragma: no cover
                pouet_platform_category.add("midschool")
            elif (
                set(pouet_platform_names) == {"Gameboy", "SNES/Super Famicom"} and pouet_prod.name == "EsGeBe Bounce"
            ):  # pragma: no cover
                pouet_platform_category.add("midschool")
            elif pouet_prod.pouet_id in (104477,):  # pragma: no cover
                # SCONNEX - oldschool cross-platform with Linux/Windows ports
                pouet_platform_category.add("oldschool")
            elif pouet_prod.pouet_id in (94983, 94385, 94814, 104089):  # pragma: no cover
                # TIC-80 / Pico-8 prods with spurious windows / linux platforms assigned
                pouet_platform_category.add("midschool")
            elif pouet_prod.pouet_id in (104603, 104606, 104332, 104340):  # pragma: no cover
                # Aleph Null - multi-platform but primarily MMX-class DOS
                # Space Wolf - for Macintosh Performa 5200
                # Neko City - Wii with Windows/Linux ports
                # NekoStation - Wii with Linux port
                pouet_platform_category.add("midschool")
            elif pouet_prod.pouet_id in (105393, 105264, 104778):  # pragma: no cover
                # HeXenium - macOS Intel/ARM miscategorized as MacOS (classic)
                # L-Packer - Windows-hosted demotool missing Windows platform
                # Sentinel 7 - macOS ARM miscategorized as MacOS (classic)
                pouet_platform_category.add("highend")
            elif pouet_prod.pouet_id == 96567:  # pragma: no cover
                # A Statement on the Platform Wars - multi platform
                pass
            else:
                for platform in pouet_platform_names:
                    if platform in POUET_OLDSCHOOL_PLATFORM_NAMES:
                        pouet_platform_category.add("oldschool")
                    elif platform in POUET_MIDSCHOOL_PLATFORM_NAMES:  # pragma: no cover
                        pouet_platform_category.add("midschool")
                    elif platform in POUET_HIGHEND_PLATFORM_NAMES:  # pragma: no cover
                        pouet_platform_category.add("highend")
                    elif platform in POUET_LIMBO_PLATFORM_NAMES:  # pragma: no cover
                        pass
                    else:  # pragma: no cover
                        raise Exception("Undefined platform %s" % platform)

            if len(pouet_platform_category) > 1:  # pragma: no cover
                raise Exception("Multiple platform categories for %s" % pouet_prod.name)

            if "procedural graphics" in pouet_prodtype_names:  # pragma: no cover
                pouet_derived_category = "Executable GFX"
            elif pouet_prod.pouet_id in (104469, 105460):  # pragma: no cover
                # Grand motel - missing procedural graphics tag
                # Shaft - missing procedural graphics tag
                pouet_derived_category = "Executable GFX"
            elif pouet_prod.pouet_id in (103012, 104184, 105423):  # pragma: no cover
                # Best Before 2024 - tagged as intro rather than 8k
                # First - tagged as invitation rather than 64k
                # 到遐就知到矣 - miscategorised as 32b
                pouet_derived_category = "High-End Intro"
            elif pouet_prod.pouet_id in (105175,):
                # Xmas Live 2025 Invitro - miscategorised as 256b
                pouet_derived_category = "Oldschool"
            elif pouet_prod.pouet_id in (103665, 103322, 103321, 103660, 102982):  # pragma: no cover
                # Cordic Demo 8 - tagged as intro rather than 32b
                # Lemon Shark Attacks The Sun! - tagged as demo rather than 512b
                # Love Letter - tagged as demo rather than 1k
                # Nano Chaos 8 - tagged as intro rather than 32b
                # Faulty Robots Forever - tagged as musicdisk rather than 512b
                pouet_derived_category = "Tiny Intro"
            elif any(
                intro_category in pouet_prodtype_names
                for intro_category in [
                    "1k",
                    "512b",
                    "256b",
                    "128b",
                    "64b",
                    "32b",
                ]
            ):
                pouet_derived_category = "Tiny Intro"
            elif pouet_platform_category == {"midschool"}:  # pragma: no cover
                pouet_derived_category = "Midschool"
            elif pouet_platform_category == {"oldschool"}:
                pouet_derived_category = "Oldschool"
            elif pouet_platform_category == {"highend"}:  # pragma: no cover
                if any(
                    intro_category in pouet_prodtype_names
                    for intro_category in [
                        "64k",
                        "4k",
                        "16k",
                        "40k",
                        "32k",
                        "8k",
                    ]
                ):
                    pouet_derived_category = "High-End Intro"
                else:
                    pouet_derived_category = "High-End Demo"
            else:  # pragma: no cover
                pouet_derived_category = ""

            for link in pouet_prod.download_links.all():
                if "youtu" in link.url:  # pragma: no cover
                    youtube_links.append(link.url)

        if dz_prod:
            dz_platform_names = [platform.name for platform in dz_prod.platforms.all()]
            dz_prodtype_names = [typ.name for typ in dz_prod.types.all()]

            dz_platform_category = set()
            if dz_prodtype_names == ["Tool"] and "Windows" in dz_platform_names:  # pragma: no cover
                dz_platform_category.add("highend")
            elif dz_prodtype_names == ["Tool"] and "JavaScript" in dz_platform_names:  # pragma: no cover
                dz_platform_category.add("highend")
            elif set(dz_platform_names) == {"MS-Dos", "Windows"}:  # pragma: no cover
                dz_platform_category.add("midschool")
            elif set(dz_platform_names) == {"MS-Dos", "Linux"}:  # pragma: no cover
                dz_platform_category.add("midschool")
            elif set(dz_platform_names) == {"Acorn Archimedes", "Raspberry Pi"}:  # pragma: no cover
                dz_platform_category.add("midschool")
            elif dz_prod.id in (334702, 337880, 342318, 370699):  # pragma: no cover
                # multi-platform prods:
                # JoG christmas card pack 2023
                # Lovebyte 2024 Countdown Invite
                # A Statement On The Platform Wars
                # Demo 25 (BBS door thing)
                pass
            elif dz_prod.id in (374860, 380125):  # pragma: no cover
                # SCONNEX - oldschool cross-platform with Linux/Windows ports
                # TinyLife-6502 - oldschool cross-platform with C64-DTV port
                dz_platform_category.add("oldschool")
            elif dz_prod.id in (
                317579,
                375933,
                381522,
                378341,
                380591,
                375852,
                373529,
                373273,
                372845,
                376072,
                381524,
            ):  # pragma: no cover
                # mhm-hny2023 - party version on Windows, final on Amiga?
                # Aleph Null - multi-platform but primarily MMX-class DOS
                # Get Ready - primarily Atari ST but multi-platform including Sinclair QL
                # Gorski - primarily Atari ST but multi-platform including Sinclair QL
                # Gifted - MacOS but specifically PowerMac G3
                # Space Wolf - for Macintosh Performa 5200
                # Neko City - Wii with Windows/Linux ports
                # NekoStation - Wii with Linux port
                # Phased - primarily Atari ST but multi-platform including Sinclair QL
                # Shattered - primarily Atari ST but multi-platform including Sinclair QL
                # Singen68k v1.2 - multi-platform 68k
                dz_platform_category.add("midschool")
            else:
                for platform in dz_platform_names:
                    if platform in DZ_OLDSCHOOL_PLATFORM_NAMES:
                        dz_platform_category.add("oldschool")
                    elif platform in DZ_MIDSCHOOL_PLATFORM_NAMES:  # pragma: no cover
                        dz_platform_category.add("midschool")
                    elif platform in DZ_HIGHEND_PLATFORM_NAMES:  # pragma: no cover
                        dz_platform_category.add("highend")
                    elif platform in DZ_LIMBO_PLATFORM_NAMES:  # pragma: no cover
                        pass
                    else:  # pragma: no cover
                        raise Exception("Undefined platform %s" % platform)

            if len(dz_platform_category) > 1:  # pragma: no cover
                raise Exception("Multiple platform categories for %s" % dz_prod.title)

            if any(
                exegfx_category in dz_prodtype_names
                for exegfx_category in ["Executable Graphics", "4K Executable Graphics", "256b Executable Graphics"]
            ):  # pragma: no cover
                dz_derived_category = "Executable GFX"
            elif any(
                intro_category in dz_prodtype_names
                for intro_category in [
                    "1K Intro",
                    "512b Intro",
                    "256b Intro",
                    "128b Intro",
                    "64b Intro",
                    "32b Intro",
                    "16b intro",
                    "8b intro",
                ]
            ):
                dz_derived_category = "Tiny Intro"
            elif dz_platform_category == {"midschool"}:  # pragma: no cover
                dz_derived_category = "Midschool"
            elif dz_platform_category == {"oldschool"}:
                dz_derived_category = "Oldschool"
            elif dz_platform_category == {"highend"}:  # pragma: no cover
                if any(
                    intro_category in dz_prodtype_names
                    for intro_category in [
                        "64K Intro",
                        "40k Intro",
                        "32K Intro",
                        "16K Intro",
                        "8K Intro",
                        "4K Intro",
                        "2K Intro",
                    ]
                ):
                    dz_derived_category = "High-End Intro"
                else:
                    dz_derived_category = "High-End Demo"
            else:  # pragma: no cover
                dz_derived_category = ""

            for link in dz_prod.links.all():
                if link.link_class == "YoutubeVideo":
                    youtube_links.append(link.url)

        if dz_prod and pouet_prod:
            if pouet_derived_category == "Executable GFX":  # pragma: no cover
                # trust Pouet if it says a prod is exe gfx
                pass
            elif (
                dz_derived_category and pouet_derived_category and dz_derived_category != pouet_derived_category
            ):  # pragma: no cover
                raise Exception("mismatched categories for %s" % dz_prod.title)
            csvfile.writerow(
                [
                    pouet_derived_category or dz_derived_category,
                    "https://pouet.net/prod.php?which=%d" % pouet_prod.pouet_id,
                    "https://demozoo.org" + dz_prod.get_absolute_url(),
                    dz_prod.title,
                    dz_prod.byline_string,
                    pouet_prod.vote_up_count,
                    pouet_prod.vote_pig_count,
                    pouet_prod.vote_down_count,
                    vote_diff,
                    "{:.2f}".format(vote_avg),
                    pouet_prod.cdc_count,
                    round(pouet_prod.popularity),
                    "; ".join(
                        "%s at %s %s"
                        % (ordinal(placing.ranking), placing.competition.party.name, placing.competition.name)
                        for placing in dz_prod.competition_placings.all()
                    ),
                    ", ".join(dz_prodtype_names),
                    ", ".join(dz_platform_names),
                    youtube_links[0] if youtube_links else "",
                ]
            )
        elif dz_prod:
            csvfile.writerow(
                [
                    dz_derived_category,
                    "",
                    "https://demozoo.org" + dz_prod.get_absolute_url(),
                    dz_prod.title,
                    dz_prod.byline_string,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "; ".join(
                        "%s at %s %s"
                        % (ordinal(placing.ranking), placing.competition.party.name, placing.competition.name)
                        for placing in dz_prod.competition_placings.all()
                    ),
                    ", ".join(dz_prodtype_names),
                    ", ".join(dz_platform_names),
                    youtube_links[0] if youtube_links else "",
                ]
            )
        else:
            csvfile.writerow(
                [
                    pouet_derived_category,
                    "https://pouet.net/prod.php?which=%d" % pouet_prod.pouet_id,
                    "",
                    pouet_prod.name,
                    " :: ".join([group.name for group in pouet_prod.groups.all()]),
                    pouet_prod.vote_up_count,
                    pouet_prod.vote_pig_count,
                    pouet_prod.vote_down_count,
                    vote_diff,
                    "{:.2f}".format(vote_avg),
                    pouet_prod.cdc_count,
                    round(pouet_prod.popularity),
                    "; ".join(
                        (
                            "%s at %s %s"
                            % (ordinal(placing.ranking), placing.party.name, placing.competition_type.name)
                            if placing.competition_type
                            else "%s at %s" % (ordinal(placing.ranking), placing.party.name)
                        )
                        for placing in pouet_prod.competition_placings.all()
                    ),
                    ", ".join(pouet_prodtype_names),
                    ", ".join(pouet_platform_names),
                    youtube_links[0] if youtube_links else "",
                ]
            )

    for prod in prods:
        pouet_ids = [link.parameter for link in prod.links.all() if link.link_class == "PouetProduction"]
        if len(pouet_ids) > 1:  # pragma: no cover
            raise Exception("Multiple Pouet IDs for prod %d" % prod.id)
        elif pouet_ids:
            pouet_prod = pouet_prods_by_id.pop(int(pouet_ids[0]), None)
        else:
            pouet_prod = None

        write_row(prod, pouet_prod)

    for pouet_prod in pouet_prods_by_id.values():
        write_row(None, pouet_prod)

    return response
