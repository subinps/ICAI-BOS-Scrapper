import os

import requests
from bs4 import BeautifulSoup

_URL = "https://www.icai.org"


def makeDir(path: str):
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def getTableContents(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("div", {"class": "table-responsive"})
    if table:
        return table.find_all("li")  # type: ignore
    return []


def downloadFile(url, fileName: str):
    response = requests.get(url)
    extension = url.split(".")[-1]
    file = fileName.strip() + f".{extension}"
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "wb+") as out:
        out.write(response.content)


def handleChild(child, path):
    for i in child:
        _sub = i.find("a")
        if not _sub:
            continue
        name = _sub.text
        _path = path + f"/{name}"
        url = _sub["href"]
        if url.startswith("https://resource.cdn"):
            downloadFile(url, _path)
            print(f"Downloading: {url} to {_path}", flush=True)
        else:
            makeDir(_path)
            if url.startswith(".."):
                link = _URL + url.lstrip("..")
            else:
                link = url
            child = getTableContents(link)
            if not child:
                handleTableOldStyle(link, _path)
            handleChild(child, _path)


def handleTableOldStyle(url, path: str):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("div", {"class": "table-responsive"})
    if table:
        table = table.find_all("tr")  # type: ignore
    else:
        return
    _first = _second = path
    first, second = _first, _second
    __first, __second = first, second
    for i in table:
        head = i.find_all("strong")
        if head:
            if len(head) > 1:
                first = makeDir(_first + f"/{head[0].text}")
                second = makeDir(_second + f"/{head[1].text}")
            elif head[0].text.strip():
                __first = makeDir(first + f"/{head[0].text}")
                __second = makeDir(second + f"/{head[0].text}")
        else:
            columns = i.find_all("td")
            if len(columns) == 2:
                material, practiceManual = columns
            else:
                material, practiceManual = columns[0], []
            links = material.find_all("a")
            for i in links:
                url = i["href"]
                if url.startswith("https://resource.cdn"):
                    downloadFile(i["href"], f"{__first}/{i.text}")
            if practiceManual:
                links = practiceManual.find_all("a")  # type: ignore
                for i in links:
                    url = i["href"]
                    if url.startswith("https://resource.cdn"):
                        downloadFile(i["href"], f"{__second}/{i.text}")


COURSES = {
    1: {"Foundation New": "foundation-course"},
    2: {"Intermediate New": "intermediate-course"},
    3: {"Intermediate Old": "intermediate-integrated-professional-competence-course"},
    4: {"Final New": "final-course-new-scheme-of-education-and-training"},
    5: {"Final Old": "final-course-old-scheme-of-education-and-training"},
}


def main():
    print(">>>> ICAI BOS Downloader by https://github.com/subinps <<<<")
    print("\n")
    for i in COURSES:
        print(i, ": ", list(COURSES[i].keys())[0], "\n")
    while True:
        course = input("Enter the number corresponding to your course: ")
        try:
            course = int(course)
        except Exception:
            print("!Invalid, Enter A Number between 1-5\n")
            continue
        else:
            if course in COURSES:
                break
            else:
                print("!Invalid, Enter A Number between 1-5\n")
    url = list(COURSES[course].values())[0]
    name = list(COURSES[course].keys())[0]
    res = requests.get(_URL + f"/post/{url}")
    soup = BeautifulSoup(res.text, "html.parser")
    subjects = soup.find("ul", {"style": "list-style-type: disc;"}).find_all("li")  # type: ignore
    makeDir(name)
    handleChild(subjects, name)


if __name__ == "__main__":
    main()
