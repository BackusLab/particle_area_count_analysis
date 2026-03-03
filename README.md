1. Download the particle_area_count.py file.
2. Drag particle_area_count.py file and the microscopy image (czi) into Fiji ImageJ (note: don't split channels beforehand, just use default settings).
3. Add the pathname of the directory that you want your output folder to be (script will automatically make an output folder in the specified directory, you don't have to make one beforehand).
4. Adjust settings (constants) as needed (recommend testing on one image first).
5. Run the script.
6. You should have a new folder w/ in your specified directory called "[microscopy image name] output".
7. The output folder should contain 13 files (for 2 channels):
     For each channel:
        Original image
        Brightened image
        Thresholded image (black & white)
        Outline image (outline of thresholded particles)
        Overlay image (thresholded image + highlighted outline)
        CSV file w/ area + intensity of each particle 
     CSV file w/ summary of both channels (count, total area, avg size, % area, intensity)
8. Optional: If you would like to combine all the summary tables from multiple outputs, you can use the stress_granule_analysis.py.ipynb file.
9. Optional: If you would like histograms from the combined summary table, you can use the stress_granule_data_visualization.RMD file.
