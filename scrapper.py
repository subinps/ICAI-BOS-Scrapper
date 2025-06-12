import json
import os
import re
import requests
from bs4 import BeautifulSoup

_URL = "https://www.icai.org"


treeInfo = {
    "final": [
        {"url": "/post/sm-final-p1-may2025", "name": "Paper -1 - Financial Reporting"},
        {
            "url": "/post/sm-final-p2-may2025",
            "name": "Paper-2: Advanced Financial Management",
        },
        {
            "url": "/post/sm-final-p3-may2025",
            "name": "Paper-3: Advanced Auditing, Assurance and Professional Ethics",
        },
        {
            "url": "/post/sm-final-p4-may-nov2025",
            "name": "Paper-4: Direct Tax Laws & International Taxation",
        },
        {"url": "/post/sm-final-p5-may-nov-2025", "name": "Paper-5: Indirect Tax Laws"},
    ]
}


def sanitize(filename: str, replacement: str = "-") -> str:
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    sanitized = re.sub(invalid_chars, replacement, filename)
    sanitized = sanitized.rstrip(" .")
    return sanitized[:255]


def capitalize_words(text: str) -> str:
    return " ".join(word.capitalize() for word in text.split())


def generateJson(module, primitive: bool = False):
    if primitive:
        group_data = {"group": "MODULE 1", "subgroups": []}
        mainTable =  module
    else:
        group_name = module.contents[0].strip()
        group_data = {"group": group_name, "subgroups": []}
        mainTable = module.find_all("ul", recursive=False)[0].find_all(
        "li", recursive=False
    )

    for item in mainTable:
        if item.find("ul"):
            subgroup_title = item.contents[0].strip()
            units = [
                {"title": a.get_text(strip=True), "link": a["href"]}
                for a in item.find("ul").find_all("a")
            ]
            group_data["subgroups"].append({"subgroup": subgroup_title, "units": units})
        else:
            a_tag = item.find("a")
            if a_tag:
                title = a_tag.get_text(strip=True)
                group_data["subgroups"].append(
                    {
                        "subgroup": title,
                        "units": [{"title": title, "link": a_tag["href"]}],
                    }
                )

    return group_data


def print_header(title: str):
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")


def main():
    print_header("ICAI FINAL STUDY MATERIAL DOWNLOADER")
    print("Available Papers:")
    for i, paper in enumerate(treeInfo["final"], 1):
        print(f"{i}. {paper['name']}")

    paperSelect = input("\nEnter the number corresponding to the paper: ").strip()
    if not paperSelect.isdigit() or not (
        1 <= int(paperSelect) <= len(treeInfo["final"])
    ):
        print("\n[!] Invalid selection. Exiting...")
        return

    paper_index = int(paperSelect) - 1
    isPrimitive = True if paper_index == 1 else False
    selected_paper = treeInfo["final"][paper_index]
    paper_name = selected_paper["name"]
    url = _URL + selected_paper["url"]

    print(f"\nSelected Paper: {paper_name}\nFetching modules from: {url}\n")
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    mainTable = soup.find("ul", {"style": "list-style-type: disc;"})
    allModules = mainTable.find_all("li", recursive=False)

    print(f"Found {len(allModules)} modules.\n")

    json_data = {"paper": paper_name, "modules": []}
    if isPrimitive:
        print(f"{i}. Processing module")
        json_data["modules"].append(generateJson(allModules, primitive=True))
    else:
        for i, module in enumerate(allModules, 1):
            print(f"{i}. Processing module: {module.contents[0].strip()}")
            json_data["modules"].append(generateJson(module))

    os.makedirs("json", exist_ok=True)
    output_filename = f"{sanitize(paper_name)}.json"
    output_path = os.path.join("json", output_filename)

    with open(output_path, "w") as f:
        json.dump(json_data, f, indent=4)

    print(f"\n[✓] JSON saved to: {output_path}\n")

    parentFolder = sanitize(paper_name)
    os.makedirs(parentFolder, exist_ok=True)

    for mod_idx, module in enumerate(json_data["modules"], 1):
        module_name = sanitize(f"{mod_idx}. {capitalize_words(module['group'])}")
        module_path = os.path.join(parentFolder, module_name)
        os.makedirs(module_path, exist_ok=True)
        print(f"\n[+] Module: {module_name}")

        for sub_idx, subgroup in enumerate(module["subgroups"], 1):
            subgroup_name = sanitize(
                f"{sub_idx}. {capitalize_words(subgroup['subgroup'])}"
            )
            subgroup_path = os.path.join(module_path, subgroup_name)
            os.makedirs(subgroup_path, exist_ok=True)
            print(f"  [-] Subgroup: {subgroup_name}")

            for unit_idx, unit in enumerate(subgroup["units"], 1):
                unit_title = (
                    sanitize(f"{unit_idx}. {capitalize_words(unit['title'])}") + ".pdf"
                )
                unit_link = unit["link"]
                unit_path = os.path.join(subgroup_path, unit_title)

                print(f"    [>] Downloading: {unit_title}")
                res = requests.get(unit_link)
                if res.status_code == 200:
                    with open(unit_path, "wb") as file:
                        file.write(res.content)
                    print(f"        [✓] Saved to: {unit_path}")
                else:
                    print(f"        [!] Failed (Status: {res.status_code})")


if __name__ == "__main__":
    main()
