import os
from selenium import webdriver
import folium
import time
from selenium.webdriver.firefox.options import Options
from PIL import Image

def paste_img_on_img(background, foreground):
    # Get the dimensions of both images
    bg_width, bg_height = background.size
    fg_width, fg_height = foreground.size

    # Calculate the bottom right corner coordinates for placement
    right = 0#bg_width - fg_width  # Places at right edge, adjust if needed
    bottom = bg_height - fg_height  # Places at bottom edge

    # Paste the small image onto the large image
    background.paste(foreground, (right, bottom), foreground)

    return background

def get_satellite_map(latitude, longitude, zoom_start=18):
    # Initialize map centered at the specified latitude and longitude
    m = folium.Map(location=[latitude, longitude], zoom_start=zoom_start)

    # Add satellite tile layer
    folium.TileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                     attr='Google',
                     name='Google Satellite',
                     overlay=False).add_to(m)

    # Add red marker at the specified location
    icon_path = 'Images/GPS_logo.png'
    folium.Marker([latitude, longitude],
                  popup='Location',
                  #icon=folium.Icon(color='red', icon='glyphicon-map-marker')).add_to(m)
                  icon=folium.CustomIcon(icon_image=icon_path, icon_size=(100,100))).add_to(m)

    fileHeader = f'{latitude}_{longitude}_basemap'
    m.save(f'Temps/{fileHeader}.html')

    options = Options()
    options.add_argument('--headless')
    browser = webdriver.Firefox(options=options)
    browser.get(f"file:///mnt/c/Users/pilep/Downloads/GPScampy/Temps/{fileHeader}.html")
    time.sleep(2)  # Wait for the map to load
    browser.save_screenshot(f'Temps/{fileHeader}.png')
    browser.quit()

    size = 425

    img = Image.open(f'Temps/{fileHeader}.png')

    # Calculate coordinates for the square area
    left = (img.width - size) / 2
    top = (img.height - size) / 2
    right = (img.width + size) / 2
    bottom = (img.height + size) / 2

    # Crop the image to create a square area
    img_cropped = img.crop((left, top, right, bottom))

    # Save the cropped image as PNG
    #img_cropped.save('{fileHeader}.png', "PNG")

    GOOGLE_logo = Image.open("Images/GOOGLE_logo.png").convert('RGBA')

    gmap = paste_img_on_img(img_cropped,GOOGLE_logo).resize((259,259)).convert('RGB')

    #gmap.save(f'{fileHeader}.png','PNG')
    os.remove(f'Temps/{fileHeader}.html')
    os.remove(f'Temps/{fileHeader}.png')

    return gmap

