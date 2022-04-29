""" 
COMP 593 - Final Project

Description: 
  Downloads NASA's Astronomy Picture of the Day (APOD) from a specified date
  and sets it as the desktop background image.

Usage:
  python apod_desktop.py image_dir_path [apod_date]

Parameters:
  image_dir_path = Full path of directory in which APOD image is stored
  apod_date = APOD image date (format: YYYY-MM-DD)

History:
  Date        Author    Description
  2022-03-11  J.Dalby   Initial creation
  2022-04-21-29  A. Neal   Edited to make functional
"""
from sys import argv, exit
from datetime import datetime, date
import hashlib
import os 
import requests
import sqlite3 
import ctypes

def main():

    # Determine the paths where files are stored
    image_dir_path = get_image_dir_path()
    db_path = os.path.join(image_dir_path, 'apod_images.db')

    # Get the APOD date, if specified as a parameter
    apod_date = get_apod_date()

    # Create the images database if it does not already exist
    create_image_db(db_path)

    # Get info for the APOD
    apod_info_dict = get_apod_info(apod_date)
    
    # Download today's APOD
    image_url = apod_info_dict['url']
    image_msg = download_apod_image(image_url)
    image_sha256 = hashlib.sha256(image_msg).hexdigest()
    image_size = len(image_msg)
    image_path = get_image_path(image_url, image_dir_path)

    # Print APOD image information
    print_apod_info(image_url, image_path, image_size, image_sha256)

    # Add image to cache if not already present
    if not image_already_in_db(db_path, image_sha256):
        save_image_file(image_msg, image_path, image_url)
        add_image_to_db(db_path, image_path, image_size, image_sha256)

    # Set the desktop background image to the selected APOD
    set_desktop_background_image(image_path)

def get_image_dir_path():
    """
    Validates the command line parameter that specifies the path
    in which all downloaded images are saved locally.

    :returns: Path of directory in which images are saved locally
    """
    if len(argv) >= 2:
        dir_path = argv[1]
        if os.path.isdir(dir_path):
            print("Images directory:", dir_path)
            return dir_path
        else:
            print('Error: Non-existent directory', dir_path)
            exit('Script execution aborted')
    else:
        print('Error: Missing path parameter.')
        exit('Script execution aborted')

def get_apod_date():
    """
    Validates the command line parameter that specifies the APOD date.
    Aborts script execution if date format is invalid.

    :returns: APOD date as a string in 'YYYY-MM-DD' format
    """    
    if len(argv) >= 3:
        # Date parameter has been provided, so get it
        apod_date = argv[2]

        # Validate the date parameter format
        try:
            datetime.strptime(apod_date, '%Y-%m-%d')
        except ValueError:
            print('Error: Incorrect date format; Should be YYYY-MM-DD')
            exit('Script execution aborted')
    else:
        # No date parameter has been provided, so use today's date
        apod_date = date.today().isoformat()
    
    print("APOD date:", apod_date)
    return apod_date

def get_image_path(image_url, dir_path):
    """
    Determines the path at which an image downloaded from
    a specified URL is saved locally.

    :param image_url: URL of image
    :param dir_path: Path of directory in which image is saved locally
    :returns: Path at which image is saved locally
    """
    url = image_url
    image_name = url.split('/')[-1]
    return os.path.join(dir_path, image_name)

def get_apod_info(date):
    """
    Gets information from the NASA API for the Astronomy 
    Picture of the Day (APOD) from a specified date.

    :param date: APOD date formatted as YYYY-MM-DD
    :returns: Dictionary of APOD info
    """    
    resp_msg = requests.get("https://api.nasa.gov/planetary/apod?api_key=OgN20BOtcOfM9Nt8lj8JZzAJbhMkn9C79DYlMZ6p&date=" + date)

    if resp_msg.status_code == 200:
        print('Accessing the APOD API... Complete')
        return resp_msg.json()
    else:
        print('Failed to connect to the APOD API. Code: ', resp_msg.status_code)

def print_apod_info(image_url, image_path, image_size, image_sha256):
    """
    Prints information about the APOD

    :param image_url: URL of image
    :param image_path: Path of the image file saved locally
    :param image_size: Size of image in bytes
    :param image_sha256: SHA-256 of image
    :returns: None
    """    
    print('Some information about the APOD:')
    print('\tThe URL of the image is: ', image_url)
    print('\tThe path to the downloaded image is: ', image_path)
    print('\tThe size of the image is: ', image_size, 'bytes.')
    print('\tThe SHA-256 of the image is: ', image_sha256)

def download_apod_image(image_url):
    """
    Downloads an image from a specified URL.

    :param image_url: URL of image
    :returns: Response message that contains image data
    """
    resp_msg = requests.get(image_url)
    if resp_msg.status_code == 200:
        print('Downloading APOD Image... Complete')
        return resp_msg.content
    else:
        print('Failed to download APOD Image. Code: ', resp_msg.status_code)

def save_image_file(image_msg, image_path, image_url):
    """
    Extracts an image file from an HTTP response message
    and saves the image file to disk.

    :param image_msg: HTTP response message
    :param image_path: Path to save image file
    :returns: None
    """
    image_msg = requests.get(image_url)
    image_data = image_msg.content
    with open(image_path, 'wb') as handler:
        handler.write(image_data)
        print('Saving Image... Complete')

def create_image_db(db_path):
    """
    Creates an image database if it doesn't already exist.

    :param db_path: Path of .db file
    :returns: None
    """
    myConnection = sqlite3.connect(db_path)
    myCursor = myConnection.cursor()
    create_apod_table = """ CREATE TABLE IF NOT EXISTS apod_info (
                    imagepath text PRIMARY KEY,
                    imagesize text NOT NULL,
                    imagesha256 text NOT NULL UNIQUE,
                    downloaded date NOT NULL

    );"""
    myCursor.execute(create_apod_table)
    myConnection.commit()
    myConnection.close()

def add_image_to_db(db_path, image_path, image_size, image_sha256):
    """
    Adds a specified APOD image to the DB.

    :param db_path: Path of .db file
    :param image_path: Path of the image file saved locally
    :param image_size: Size of image in bytes
    :param image_sha256: SHA-256 of image
    :returns: None
    """
    myConnection = sqlite3.connect(db_path)
    myCursor = myConnection.cursor()
    add_apod_query = """ INSERT INTO apod_info (
                        imagepath,
                        imagesize,
                        imagesha256,
                        downloaded)
                        VALUES(?,?,?,?);"""
    
    apod_data = (image_path,
                image_size,
                image_sha256,
                datetime.now())

    myCursor.execute(add_apod_query, apod_data)
    myConnection.commit()
    myConnection.close()

def image_already_in_db(db_path, image_sha256):
    """
    Determines whether the image in a response message is already present
    in the DB by comparing its SHA-256 to those in the DB.

    :param db_path: Path of .db file
    :param image_sha256: SHA-256 of image
    :returns: True if image is already in DB; False otherwise
    """ 
    myConnection = sqlite3.connect(db_path)
    myCursor = myConnection.cursor()
    selectStatement = "SELECT imagesha256 FROM apod_info WHERE imagesha256 = ?"
    values = (image_sha256,)
    myCursor.execute(selectStatement, values)
    results = myCursor.fetchall()

    if len(results) > 0:
        print('Image already exists in the cache.')
        return True
    myConnection.close()

def set_desktop_background_image(image_path):
    """
    Changes the desktop wallpaper to a specific image.

    :param image_path: Path of image file
    :returns: None
    """
    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)
        print('Setting Image as Desktop Background... Complete')
    except:
        print('Error setting Desktop Background')
        
main()