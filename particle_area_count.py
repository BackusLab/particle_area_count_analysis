'''
Author: Lucia Liu
Purpose: Finds the number of particles and area of each particle for each channel in a .czi file
Notes:
- Image that is dragged in must be multi-channel and .czi
- For the output folder, can do 2 options:
    Option 1: Choose a directory beforehand (uncomment out "Choose directory" code section) and comment out "Make directory" section
    Option 2: Let the script make a directory (paste your target base directory pathname where specified) --> easier for large batches
- Sometimes if the output identify really abnormal large chunks, first try rerunning since it might be a system glitch
Last edited: 3/2/26
'''

from ij import IJ, WindowManager, ImagePlus
from ij.io import DirectoryChooser, FileSaver
from ij.measure import ResultsTable
from ij.gui import Overlay, Roi
from ij.plugin.frame import RoiManager
from java.io import File

BASE_DIR = '/Users/lucialiu/Downloads/2025.12.16 Ctrl-SHKBP1 DDC diet 2wks p62/czi/40x' # Replace with base folder directory (just copy pathname)

C0_IMG_MAX = 80 # lower max to brighten image
C0_THRESHOLD_MIN = 17 # lower threshold to recognize more particles
C0_FILTER_MIN = 0.1

C1_IMG_MAX = 120 # lower max to brighten image 
C1_THRESHOLD_MIN = 9 # lower threshold to recognize more particles 
C1_FILTER_MIN = 5

def adjust_brightness(image, max):
    edited_image = image.duplicate()
    IJ.run(edited_image, "8-bit", "")
    ip = edited_image.getProcessor()
    scale = 255 / (max - 0)
    ip.multiply(scale)
    edited_image.updateAndDraw()
    return edited_image

def apply_threshold(image, min):
    IJ.run("8-bit")
    IJ.run("Subtract Background...", "rolling=50")
    ip = image.getProcessor()
    ip.setThreshold(min, 255)
    image.updateAndDraw()
    IJ.run("Convert to Mask")
    return image

def add_scale_bar(img, color):
    dup = img.duplicate()
    WindowManager.setCurrentWindow(dup.getWindow())
    IJ.run(dup, "Scale Bar...", "width=20 height=4 thickness=8 font=30 color={} location=[Lower Right]".format(color))
    return dup

def analyze_particles(image, min_size, channel_num):
    # Set measurements
    IJ.run(image, "Set Measurements...", "area mean redirect=[" + image.getTitle() + "]")
	    # redirect to original image (to get the mean gray value)
	    # area = area of particle in micrometers
	    # mean = mean gray value (brightness aka intensity)

	# Analyze particles
    if channel_num == 0:
        IJ.run(image, "Analyze Particles...",
               "size={}-Infinity show=Outlines add display summarize include redirect=[{}]".format(min_size, image.getTitle()))
                # {min_size}-Infinity = filters out noise, only counts particles greater than {min_size} µm^2
                # Outlines = shows image w/ outline and numbered particles
                # add = add to ROI manager
                # display = makes table of list of areas for each particle in an image
                # summarize = summarizes data (count, total area, avg size, % area, mean) for each image
                # include = include holes
    elif channel_num == 1:
        IJ.run(image, "Analyze Particles...",
               "size={}-Infinity show=Outlines add display summarize redirect=[{}]".format(min_size, image.getTitle()))
    else:
        return None

    outline = WindowManager.getCurrentImage()
    results = ResultsTable.getResultsTable()
    summary = ResultsTable.getResultsTable("Summary")

    overlay = Overlay()
    rm = RoiManager.getInstance()
    for roi in rm.getRoisAsArray():
        overlay.add(roi)
    rm.reset()
    rm.setVisible(False)

    return outline, overlay, results, summary


# channel_num starts at 0
def analyze_channel(channel_num, image_titles, img_max, threshold_min, filter_min, output_dir):
    title = image_titles[channel_num]
    image = WindowManager.getImage(title)
    image.show()

    # Adjust brightness
    edited_image = adjust_brightness(image, img_max)
    edited_image.show()

    # Create duplicate to apply threshold
    dup = image.duplicate()
    dup.show()
    WindowManager.setCurrentWindow(dup.getWindow())

    # Apply threshold
    threshold = apply_threshold(dup, threshold_min)
    threshold.show()

    # Analyze particles
    outline, overlay, results, summary = analyze_particles(dup, filter_min, channel_num)
    if channel_num == 0:
        edited_image.setOverlay(overlay)
        edited_image.updateAndDraw()
        flattened = edited_image.flatten()
        flattened.show()
    elif channel_num == 1:
        image.setOverlay(overlay)
        image.updateAndDraw()
        flattened = image.flatten()
        flattened.show()

    # Save files
    fs = FileSaver(add_scale_bar(image, "White"))
    fs.saveAsTiff(output_dir + title.replace(".czi", "") + "_original.tif")  # save original image

    fs = FileSaver(add_scale_bar(edited_image, "White"))
    fs.saveAsTiff(output_dir + title.replace(".czi", "") + "_edited.tif")  # save image with adjusted brightness

    fs = FileSaver(add_scale_bar(threshold, "White"))
    fs.saveAsTiff(output_dir + title.replace(".czi", "") + "_thresholded.tif") # save thresholded image

    fs = FileSaver(add_scale_bar(flattened, "White"))
    fs.saveAsTiff(output_dir + title.replace(".czi", "") + "_overlay.tif") # save overlay

    fs = FileSaver(add_scale_bar(outline, "Black"))
    fs.saveAsTiff(output_dir + title.replace(".czi", "") + "_outline.tif") # save outline

    results.save(output_dir + title.replace(".czi", "") + "_results.csv")
    results.reset()

    # Close windows
    image.changes = False
    image.close()
    edited_image.changes = False
    edited_image.close()
    dup.changes = False
    dup.close()
    outline.changes = False
    outline.close()
    flattened.changes = False
    flattened.close()
    results_window = WindowManager.getFrame("Results")
    if results_window is not None:
        results_window.close()

    return summary

def main():
    '''
    # Choose directory
    dc = DirectoryChooser("Choose folder to save output files in.")
    output_dir = dc.getDirectory()

    if output_dir is None:
        raise ValueError("No output directory selected.")
    '''

    # Get input image
    imp = IJ.getImage() # gets dragged-in image

    if imp.getNChannels() == 1:
        image_titles = [imp.getTitle()]
    else:
        IJ.run(imp, "Split Channels", "")
        image_titles = WindowManager.getImageTitles()

    if not imp.getTitle().lower().endswith(".czi"):
        raise ValueError("Incompatible file type - must be a two-channel .czi file")

    # Make new directory - Comment out if you want to choose directory instead
    output_dir = File(BASE_DIR + File.separator + imp.getTitle().replace(".czi", "") + "_output")
    output_dir.mkdirs()
    output_dir = output_dir.getAbsolutePath() + File.separator

    # Analyze channels
    analyze_channel(0, image_titles, C0_IMG_MAX, C0_THRESHOLD_MIN, C0_FILTER_MIN, output_dir)
    summary = analyze_channel(1, image_titles, C1_IMG_MAX, C1_THRESHOLD_MIN, C1_FILTER_MIN, output_dir)

    # Save summary
    summary.save(output_dir + imp.getTitle().replace(".czi", "") + "_summary.csv")
    summary_window = WindowManager.getFrame("Summary")
    if summary_window is not None:
        summary_window.close()

main()