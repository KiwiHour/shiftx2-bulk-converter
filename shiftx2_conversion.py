import requests, os, re
from datetime import datetime
from requests import Response
from typing import Literal, TextIO

# Configurable
input_pdbs_dir_name = "ecoli_proteome" # Directory which contains all the .pdb files
cs_csv_output_dir_name = "ecoli" # The output directory in which all the .pdb.cs.csv files will go

# Do not touch
input_pdbs_dir = os.path.join("./pdbs", input_pdbs_dir_name)
output_chemical_shifts_dir = os.path.join("./chemical_shifts", cs_csv_output_dir_name)
total_pdb_files = len(os.listdir(input_pdbs_dir))
completed_conversions_file_path = "completed_conversions.txt"

URL = "http://www.shiftx2.ca/cgi-bin/shiftx2.cgi"
HEADERS = {
    "Host": "www.shiftx2.ca",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "multipart/form-data; boundary=----geckoformboundary",
    "Origin": "http://www.shiftx2.ca",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Referer": "http://www.shiftx2.ca/index.html",
    "Upgrade-Insecure-Requests": "1"
}

def create_body(
    pdb_contents: str,
    filename: str,
    deuterate: bool = False,
    pH: float = 5,
    temperature_k: int = 298,
    phosphorylated: bool = False,
    shift_type: Literal["all"] | Literal["backbone"] | Literal["side"] = "all",
    output_format: Literal["tabular"] | Literal["csv"] | Literal["nmr_star"] | Literal["nef"] = "tabular",
    use_shifty: bool = True,
    analyse_non_overlap_chains: bool = False
    ):
    
    return f"""
------geckoformboundary
Content-Disposition: form-data; name="deuterate"

{0 if deuterate else 1}
------geckoformboundary
Content-Disposition: form-data; name="ph"

{pH}
------geckoformboundary
Content-Disposition: form-data; name="temper"

{temperature_k}
------geckoformboundary
Content-Disposition: form-data; name="phospho"

{0 if phosphorylated else 1}
------geckoformboundary
Content-Disposition: form-data; name="shifttype"

{["all", "backbone", "side"].index(shift_type)}
------geckoformboundary
Content-Disposition: form-data; name="format"

{["tabular", "csv", "nmr_star", "nef"].index(output_format)}
------geckoformboundary
Content-Disposition: form-data; name="shifty"

{0 if use_shifty else 1}
------geckoformboundary
Content-Disposition: form-data; name="pdbid"


------geckoformboundary
Content-Disposition: form-data; name="file"; filename="{filename}"
Content-Type: application/octet-stream

{pdb_contents}                                                                  
------geckoformboundary
Content-Disposition: form-data; name="nonoverlap"

{0 if analyse_non_overlap_chains else 1}
------geckoformboundary
Content-Disposition: form-data; name="Submit"

Submit
------geckoformboundary--
"""
    
def extract_cs_csv_data_from_response(response: Response):
    pattern = r'NUM,RES,ATOMNAME,SHIFT[\s\S]*?(?=<\/PRE>)'
    matches = re.findall(pattern, response.text)
    
    try:
        csv = matches[0].strip()    
        return csv
    
    except IndexError:
        print(response.text)
        raise Exception("ShiftX2 response was not in the expected format")
    

def remove_completed_conversion_paths(paths: list[str]):
    filtered_paths: list[str] = []
    no_removed_paths = 0
    completed_conversion_paths: list[str] = []    
    
    with open(completed_conversions_file_path, "r") as completed_conversions_file:
        for completed_conversion_path in completed_conversions_file:
            completed_conversion_paths.append(completed_conversion_path.replace("\n",""))
    
    for path in paths:
        if path in completed_conversion_paths:
            no_removed_paths += 1
            continue
        filtered_paths.append(path)
    
    return filtered_paths, no_removed_paths

def convert_pdb_file_to_cs_csv(pdb_file: TextIO, total_converted: int):
    
    fraction_completion = f"{total_converted+1}/{total_pdb_files}"
    timestamp = datetime.now().strftime("[%d-%m-%Y %H:%M]")
    
    print(f"{timestamp} ({fraction_completion}) Converting \"{pdb_file_path}\"... ", end="", flush=True)
    
    # Collect PDB file contents and build the POST request to ShiftX2
    pdb_contents = pdb_file.read()
    body = create_body(pdb_contents, pdb_file_path, shift_type="backbone", output_format="csv")
    res = requests.post(
        url=URL,
        headers=HEADERS,
        data=body
    )
    
    # Extract chemical shift data
    cs_csv_data = extract_cs_csv_data_from_response(res)
    
    # Save the chemical shift csv data to output directory
    with open(os.path.join("chemical_shifts", cs_csv_output_dir_name, f"{pdb_file_path}.cs.csv"), "w") as cs_csv_file:
        cs_csv_file.write(cs_csv_data)
    
    # Log that that PDB file has been converted
    with open(completed_conversions_file_path, "a") as completed_conversions_file:
        completed_conversions_file.write(f"{pdb_file_path}\n")
    
    print("Completed!")

if __name__ == "__main__":
    
    # Create completed conversions file if it does note exist
    if not os.path.exists(completed_conversions_file_path):
        with open(completed_conversions_file_path, "w") as completed_conversions_file:
            print("Created completed conversions file")
            completed_conversions_file.write("")

    all_pdb_file_paths = os.listdir(input_pdbs_dir)
    pdb_file_paths, no_removed_paths = remove_completed_conversion_paths(all_pdb_file_paths)
    
    # Total completed starts at the number of removed paths (since removed paths are ones already completed)
    total_converted = no_removed_paths

    for pdb_file_path in pdb_file_paths:
        with open(os.path.join(input_pdbs_dir, pdb_file_path), "r") as pdb_file:
            convert_pdb_file_to_cs_csv(pdb_file=pdb_file, total_converted=total_converted)
            total_converted += 1