__author__ = 'Junghwan Kim'
__copyright__ = 'Copyright 2016-2018 Junghwan Kim. All Rights Reserved.'
__version__ = '1.0.0'

import numpy as np
import os
import pydicom
import scipy.misc
import shutil
from PIL import Image


def main():

    # Set input path
    path = '/home/jkim/NAS/temp_dicom/ifac/New_Cerebral_Infarction/PKS2'

    # Set output path
    path_result = '/home/jkim/NAS/raw_dicom/brain/_3_infarction/FROM/NCCT/PKS2'

    # Output information
    print '\n----------------------------------------------------------------------------------------------------' \
          '\nNCCT Categorizer %s' \
          '\n----------------------------------------------------------------------------------------------------' \
          '\nYou set path: %s' % (__version__, path)

    # Set variables
    result = 0

    # New folder
    if not os.path.exists(path_result):
        os.makedirs(path_result)

    # Recur load input directories
    for paths, dirs, files in sorted(os.walk(path)):
        if paths.endswith('/NCCT'):

            # Output loaded directory
            print '\n[LOAD]', paths
            empty = True

            # Get accessionNumber and instanceNumber
            global accessionNumber
            accessionNumber = ''
            global instanceNumber
            instanceNumber = ''
            for name in sorted(files):
                if accessionNumber.isdigit() and instanceNumber.isdigit():
                    continue
                if not name.endswith('.dcm'):
                    continue
                accessionNumber = name[0:20]
                instanceNumber = name[21:24]

            # Set path
            path_target = path_result + '/' + accessionNumber
            path_target_dcms = path_target + '/dcms'
            path_target_images = path_target + '/images'
            path_target_labels = path_target + '/labels'

            # Check the folder is correct
            for name in sorted(files):
                if not name.endswith('.dcm'):
                    empty = False
            if empty is True:
                print '[SKIP] The folder is empty:', path_target
                continue

            # New folder and Move files
            os.makedirs(path_result + '/' + accessionNumber + '/dcms')
            os.makedirs(path_result + '/' + accessionNumber + '/images')
            os.makedirs(path_result + '/' + accessionNumber + '/labels')
            for name in sorted(files):
                if name.endswith('.dcm'):
                    shutil.copyfile(paths + '/' + name, path_target_dcms + '/' + name)
                else:
                    shutil.copyfile(paths + '/' + name, path_target + '/' + name)

            # Move folders
            for paths, dirs, files in sorted(os.walk(paths)):
                if paths.endswith('/labels'):
                    for name in sorted(files):
                        shutil.copyfile(paths + '/' + name, path_target_labels + '/' + name)

            # Check the label is empty and then Rename
            tags = {}
            for paths, dirs, files in sorted(os.walk(path_target_labels)):
                instanceNumber = int(instanceNumber)
                for name in sorted(files):
                    number = '{:03d}'.format(instanceNumber)
                    labels_array = np.array(Image.open(path_target_labels + '/' + name))
                    if labels_array.max() == 0:
                        tags[number] = 0
                        name_new = accessionNumber + '_' + number + '_BLNK.png'
                    else:
                        tags[number] = 1
                        name_new = accessionNumber + '_' + number + '_IFAC.png'
                    os.rename(os.path.join(paths, name), os.path.join(paths, name_new))
                    instanceNumber += 1

            # Convert dcm to png
            for paths, dirs, files in sorted(os.walk(path_target_dcms)):
                for name in sorted(files):
                    ds = pydicom.dcmread(os.path.join(paths, name))
                    ds_array = ds.pixel_array
                    intercept = ds.RescaleIntercept
                    slope = ds.RescaleSlope
                    ds_array = ds_array * slope + intercept
                    ds_array = GetLUTValue(ds_array, 100, 50)
                    AdjImage = scipy.misc.toimage(ds_array)
                    if tags[name[21:24]] == 0:
                        tag = '_BLNK.png'
                    else:
                        tag = '_IFAC.png'
                    AdjImage.save(os.path.join(path_target_images + '/' + name[0:24] + tag))

            # Complete every process
            result += 1
            print '[SUCCESS]', path_target

        else:
            continue

    # Print result
    print '\n----------------------------------------------------------------------------------------------------' \
          '\nResult' \
          '\n----------------------------------------------------------------------------------------------------' \
          '\n', result, 'Folders are processed successfully.'

    return None


def GetLUTValue(data, window, level):
    """Apply the RGB Look-Up Table for the given data and window/level value."""

    lutvalue = np.piecewise(data,
                            [data <= (level - 0.5 - (window - 1) / 2),
                             data > (level - 0.5 + (window - 1) / 2)],
                            [0, 255, lambda data: ((data - (level - 0.5)) / (window - 1) + 0.5) * (255 - 0)])
    # Convert the resultant array to an unsigned 8-bit array to create
    # an 8-bit grayscale LUT since the range is only from 0 to 255
    return np.array(lutvalue, dtype=np.uint8)


if __name__ == '__main__':
    main()
