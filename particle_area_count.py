'''
Author: Lucia Liu
Purpose: Finds the number of particles and area of each particle for each channel in a .czi file
Input: Single 2 channel .czi file OR a folder of .czi files
Last edited: 10/30/26
'''

import os
from loci.plugins import BF
from ij.io import OpenDialog
from ij.gui import GenericDialog
from ij import IJ, WindowManager, ImagePlus
from ij.io import DirectoryChooser, FileSaver
from ij.measure import ResultsTable
from ij.gui import Overlay, Roi
from ij.plugin.frame import RoiManager
from java.io import File


# OPTIONAL: type paths here to skip the popups. Leave as None to be prompted.
INPUT_PATH = None       # single .czi file OR a folder of .czi files
OUTPUT_DIR = None       # folder where the "<imagename>_output" subfolders get saved

# EDIT THE FOLLOWING VARIABLES AS NEEDED:
'''
THRESHOLD_MIN → Recommend 17-20 to filter small particles (eg. p62 bodies), 7-10 for larger particles (eg. Nuclei), lower threshold to recognize larger particles 
FILTER_MIN → Filters out noise, recommend 0.1 for particles (eg. p62 bodies), 5 for nuclei
IMG_MAX → Recommend around 80-120, lower the max to make image brighter (NOTE: Does not affect analysis, only for visualization purposes if the picture is dark)
'''
# Channel 1
C0_THRESHOLD_MIN = 17  
C0_FILTER_MIN = 0.1
C0_IMG_MAX = 80         
 
# Channel 2 (eg. Nuclei)
C1_THRESHOLD_MIN = 9    
C1_FILTER_MIN = 5
C1_IMG_MAX = 120        


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
    
def process_image(imp, base_output_dir):
    # Runs analysis on already-open .czi image
    name = imp.getTitle()
    if not name.lower().endswith(".czi"):
        raise ValueError("Incompatible file type - must be a two-channel .czi file")

    # Split channels (original image closes, channel windows replace it)
    if imp.getNChannels() == 1:
        image_titles = [name]
    else:
        IJ.run(imp, "Split Channels", "")
        image_titles = sorted(WindowManager.getImageTitles())  # C1-..., C2-...

    # Each image gets its own subfolder inside the chosen output directory
    output_dir = File(base_output_dir + File.separator + name.replace(".czi", "") + "_output")
    output_dir.mkdirs()
    output_dir = output_dir.getAbsolutePath() + File.separator

    # Analyze channels
    analyze_channel(0, image_titles, C0_IMG_MAX, C0_THRESHOLD_MIN, C0_FILTER_MIN, output_dir)
    summary = analyze_channel(1, image_titles, C1_IMG_MAX, C1_THRESHOLD_MIN, C1_FILTER_MIN, output_dir)

    # Save summary
    summary.save(output_dir + name.replace(".czi", "") + "_summary.csv")
    summary_window = WindowManager.getFrame("Summary")
    if summary_window is not None:
        summary_window.close()


def open_czi(path):
    imp = BF.openImagePlus(path)[0]
    imp.setTitle(os.path.basename(path))
    imp.show()
    return imp


def process_folder(folder, base_output_dir):
    files = sorted(f for f in os.listdir(folder)
                   if f.lower().endswith(".czi") and not f.startswith("."))  # skips Mac "._" files
    if not files:
        raise ValueError("No .czi files found in " + folder)

    failed = []
    for i, fname in enumerate(files):
        IJ.log("Processing {}/{}: {}".format(i + 1, len(files), fname))
        IJ.run("Close All")  # avoid leftover windows being mistaken for channels
        try:
            imp = open_czi(os.path.join(folder, fname))
            process_image(imp, base_output_dir)
        except Exception as e:
            IJ.log("FAILED on {}: {}".format(fname, e))
            failed.append(fname)
        finally:
            IJ.run("Close All")

    IJ.log("Done. {} processed, {} failed.".format(len(files) - len(failed), len(failed)))
    for f in failed:
        IJ.log("  failed: " + f)


def choose_input():
    if INPUT_PATH:  # manually set, skip popup
        if not os.path.exists(INPUT_PATH):
            raise ValueError("INPUT_PATH does not exist: " + INPUT_PATH)
        return INPUT_PATH

    # Ask whether to pick one image or a whole folder
    gd = GenericDialog("Input")
    gd.addMessage("Choose your input image/folder.")
    gd.addChoice("Input type:", ["Single image", "Folder of images"], "Single image")
    gd.showDialog()
    if gd.wasCanceled():
        raise ValueError("No input selected.")
    input_type = gd.getNextChoice()

    if input_type == "Single image":
        od = OpenDialog("Choose your input image")
        if od.getFileName() is None:
            raise ValueError("No input selected.")
        return od.getDirectory() + od.getFileName()
    else:
        dc = DirectoryChooser("Choose your input folder")
        folder = dc.getDirectory()
        if folder is None:
            raise ValueError("No input selected.")
        return folder
        

def choose_output():
    if OUTPUT_DIR:  # manually set, skip popup
        File(OUTPUT_DIR).mkdirs()  # create it if it doesn't exist yet
        return OUTPUT_DIR

    IJ.showMessage("Output", "Choose the folder to save output files in.")
    dc = DirectoryChooser("Choose folder to save output files in.")
    output_dir = dc.getDirectory()
    if output_dir is None:
        raise ValueError("No output directory selected.")
    return output_dir


def main():
    # Priority: manual INPUT_PATH > already-open image > input popup
    if INPUT_PATH:
        imp = None
        path = choose_input()
    elif WindowManager.getImageCount() > 0:
        imp = IJ.getImage()
        path = None
    else:
        imp = None
        path = choose_input()

    base_output_dir = choose_output()

    if imp is not None:
        process_image(imp, base_output_dir)
    elif os.path.isdir(path):
        process_folder(path, base_output_dir)
    else:
        IJ.run("Close All")
        imp = open_czi(path)
        process_image(imp, base_output_dir)

main()

