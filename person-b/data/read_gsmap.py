import h5py
import numpy as np


def inspect_gsmap_file(file_path):
    with h5py.File(file_path, "r") as f:
        print("\nGSMaP file structure:")
        
        def show_structure(name, obj):
            print(name)

        f.visititems(show_structure)


if __name__ == "__main__":
    print("GSMaP reader ready.")