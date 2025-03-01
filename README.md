## Brief description
This is a program that will bulk convert .PDB (protein databank) files into CSV chemical shift data
It uses ShiftX2 via python's request library

## How to use
Firstly, collect some .PDB files from somewhere (such as the AlphaFold database). Then put them into a folder of your choosing inside of `/pdbs/` (for example `pdbs/ecoli`)
Make sure to update the `input_pdbs_dir_name` and `cs_csv_output_dir_name` to your preferences in `shiftx2_conversion.py`

The program will keep track of what .PDB files have been converted, so feel free to stop and start the program whenever you need. No progress will be lost