Last edited: 10/30/26

Quick video demo: https://drive.google.com/file/d/19mXD4BDA9yIGpMhHgECvw_bSzrhsqy1o/view?usp=sharing

1. Download the "particle_area_count.py" file.
2. Drag or open the "particle_area_count.py" file into Fiji ImageJ.
3. Adjust settings (constants) as needed (recommend testing on one image first).
   - THRESHOLD_MIN → Recommend 17-20 to filter small particles (eg. p62 bodies), 7-10 for larger particles (eg. Nuclei), lower threshold to recognize larger particles 
   - FILTER_MIN → Filters out noise, recommend 0.1 for particles (eg. p62 bodies), 5 for nuclei
   - IMG_MAX → Recommend around 80-120, lower the max to make image brighter (does not affect analysis, only for visualization purposes if the picture is dark)
4. Click 'Run' to run the script. You should get two pop ups to choose your input image/folder and output folder.
   - Your input files should be 2 channel .czi files
   - Optional: You can also manually specify your input and output folders where labeled INPUT_PATH and OUTPUT_DIR.
8. You should have a new folder in your specified output directory called "[microscopy image name] output".
9. The output folder should contain 13 files (for 2 channels):
   - For each channel:
        - Original image
        - Brightened image
        - Thresholded image (black & white)
        - Outline image (outline of thresholded particles)
        - Overlay image (thresholded image + highlighted outline)
        - CSV file w/ area + intensity of each particle 
   - CSV file w/ summary of both channels (count, total area, avg size, % area, intensity)
10. Optional: If you would like to combine all the summary tables from multiple outputs, you can use the stress_granule_analysis.py.ipynb file.
11. Optional: If you would like histograms from the combined summary table, you can use the stress_granule_data_visualization.RMD file.
