import os
import sys
import glob
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Arial'
from reverse_geocode import *
from make_geomap import *
from textwrap import wrap
import piexif
from datetime import datetime
from tqdm import tqdm

def paste_img_on_img_right(background, foreground, shiftL=0, shiftD=0):
    # Get the dimensions of both images
    bg_width, bg_height = background.size
    fg_width, fg_height = foreground.size

    # Calculate the bottom right corner coordinates for placement
    right = shiftL #bg_width - fg_width - shiftL  # Places at right edge, adjust if needed
    bottom = bg_height - fg_height - shiftD  # Places at bottom edge

    # Paste the small image onto the large image
    background.paste(foreground, (right, bottom), foreground)

    return background

def paste_img_on_img_bottom(background, foreground, shiftL=0, shiftD=0):
    # Get the dimensions of both images
    bg_width, bg_height = background.size
    fg_width, fg_height = foreground.size

    # Calculate the bottom right corner coordinates for placement
    right = bg_width - fg_width - shiftL  # Places at right edge, adjust if needed
    bottom = shiftD  # Places at bottom edge

    # Paste the small image onto the large image
    background.paste(foreground, (right, bottom), foreground)

    return background

def wrap_addr(line):
    #lines = wrap(line, width=95)
    lines = wrap(line, width=95)
    wrapped_line = '\n'.join(lines)
    return wrapped_line, len(lines)

def crop_to_aspect_ratio(image_to_crop, aspect_ratio=(4,3)):
    """Crops an image to match the given aspect ratio.

    Args:
        image_to_crop: The PIL Image object to crop.
        aspect_ratio: The desired aspect ratio as a tuple of width and height (e.g., (4, 3)).

    Returns:
        A cropped PIL Image object.
    """

    # Get image dimensions
    width, height = image_to_crop.size

    # Calculate target dimensions based on aspect ratio
    target_width = int(height * aspect_ratio[0] / aspect_ratio[1])
    target_height = int(width * aspect_ratio[1] / aspect_ratio[0])

    # Determine crop box based on the smaller dimension
    if width > target_width:
        left = (width - target_width) // 2
        right = left + target_width
        top = 0
        bottom = height
    else:
        left = 0
        right = width
        top = (height - target_height) // 2
        bottom = top + target_height

    # Crop the image
    cropped_image = image_to_crop.crop((left, top, right, bottom))
    return cropped_image


def save_texts_as_fig(texts,size1=11.5,size2=8.3):
    fig = plt.figure(dpi=300)
    plt.axis('off')
    plt.axis([0, 20, 0, 5])
    loc, addr = texts
    plt.text(0, 4, loc, fontsize=size1, ha='left', va='top', wrap=True, color='white', weight='semibold')
    plt.text(0, 3.7, addr, fontsize=size2, ha='left', va='top', wrap=False, color='white', weight='semibold',linespacing=1.7)
    plt.gcf().set_facecolor('none')
    plt.savefig('Temps/dummy_text.png', transparent=True, dpi=300)
    text = Image.open('Temps/dummy_text.png')
    os.remove('Temps/dummy_text.png')
    return text


def get_requisites(fileName):
    full = str(fileName[:str(fileName[:fileName.rfind('.')]).rfind('~')])
    body = full.split('_')[-5:]
    lat,long,date,time1,time2 = body
    date = date.replace('-','/')
    time1 = time1.replace('-',':')
    time = f'{time1} {time2}'
    STR = f"Lat {lat}\u00b0\nLong {long}\u00b0\n{date} {time} GMT +05:30"
    header = '_'.join(full.split('_')[:-3])
    return lat, long, date, time, STR, header


def main(camImage,des):
    #F = '3_NH12_Alipore_22.52705833_88.33145278_16-04-2024_11-05_AM~2.jpg'
    lat, long, date, time, STR, header = get_requisites(camImage)
    if des[-1]=='/':
        pass
    else:
        des=des+'/'
    header = des + header[header.rfind('/')+1:]
    geotagged_IMG = f'{header}_geotagged_GPScam.jpg'
    LOC, addr = reverse_geocode(lat, long)
    addr, lines = wrap_addr(addr)
    #addr = '27C, S Sinthee Rd, Pearabagan, South Sinthee, Biswanath Colony, Sinthee, Kolkata, West Bengal 7'
    ADDR = f'{addr}\n{STR}'

    #print(lines)
    #addr = '27C, S Sinthee Rd, Pearabagan, South Sinthee, Biswanath Colony, Sinthee, Kolkata, West Bengal 7'
    if lines>1:
        txtIMG = save_texts_as_fig(texts=[LOC,ADDR])
    elif len(addr)>80:
        txtIMG = save_texts_as_fig(texts=[LOC,ADDR],size1=12,size2=8.6)
    else:
        txtIMG = save_texts_as_fig(texts=[LOC,ADDR],size1=12,size2=9.75)

    mapIMG = get_satellite_map(lat, long).convert('RGBA')

    camIMG = crop_to_aspect_ratio(Image.open(camImage)).resize((1600,1200))
    bgIMG = Image.open('Images/TEXTback.png')

    newIMG = paste_img_on_img_right(camIMG, mapIMG, shiftL=24, shiftD=24)
    newIMG = paste_img_on_img_right(newIMG, bgIMG)

    scale=0.7
    sL=90

    if lines==2:
        sD=670
    elif len(addr)>80:
        sD=655
        sL=5
        scale=0.75
    elif len(addr)>90:
        sD=680
    else:
        sD=675
    
    width, height = txtIMG.size
    txtIMG = txtIMG.resize((int(width*scale),int(height*scale)))

    finIMG = paste_img_on_img_bottom(newIMG,txtIMG,shiftL=sL,shiftD=sD)
    finIMG.save(geotagged_IMG)
    return geotagged_IMG,lat,long,date,time

def deg_to_gps(degrees):
    degrees_abs = abs(degrees)
    minutes, seconds = divmod(degrees_abs * 3600, 60)
    degrees_int, minutes = divmod(minutes, 60)
    return (degrees_int, minutes, seconds) if degrees >= 0 else (-degrees_int, minutes, seconds)

def modify_exif(image_path, latitude, longitude, date, time, camera_maker, camera_model):
    datestr = [int(e) for e in date.split('/')][::-1]
    time_format = "%I:%M %p"
    time_obj = datetime.strptime(time, time_format).time()
    timestr = [time_obj.hour, time_obj.minute, time_obj.second]
    datetime_list = datestr+timestr
    datetime_original = datetime(*datetime_list)

    img = Image.open(image_path)

    #exif_dict = piexif.load(img.info['exif'])
    ref_image = 'Images/GEO_reference.jpg'
    exif_dict = piexif.load(ref_image)
    print(exif_dict)

    # Modify GPS coordinates
    # Latitude and Longitude
    lat_deg, lat_min, lat_sec = deg_to_gps(float(latitude))
    lon_deg, lon_min, lon_sec = deg_to_gps(float(longitude))

    # Set fig size
    exif_dict['0th'][256] = 1600
    exif_dict['0th'][257] = 1200

    # Set GPS Info
    exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = [(abs(int(lat_deg)),1), (int(lat_min),1), (int(lat_sec*1e3),int(1e3))]
    exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if float(latitude) >= 0 else 'S'
    exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = [(abs(int(lon_deg)),1), (int(lon_min),1), (int(lon_sec*1e3),int(1e3))]
    exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if float(longitude) >= 0 else 'W'
    formatted_date = datetime(datestr[0], datestr[1], datestr[2])
    gpsdate = formatted_date.strftime("%Y:%m:%d")
    #gpsdate = ':'.join([str(e) for e in datestr])
    exif_dict['GPS'][29] = gpsdate.encode('utf-8')
    exif_dict['GPS'][6] = ((8, 1), (36, 1), (22, 1))
    #exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = [(abs(int(lat_deg)),1), (int(lat_min),1), (int(lat_sec),1)]
    #exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if float(latitude) >= 0 else 'S'
    #exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = [(abs(int(lon_deg)),1), (int(lon_min),1), (int(lon_sec),1)]
    #exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if float(longitude) >= 0 else 'W'
    
    #exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = [(lat_deg,1), (lat_min,1), (lat_sec,1)]
    #exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = [(lon_deg,1), (lon_min,1), (lon_sec,1)]

    #exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = deg_to_gps(float(latitude))#piexif.GPSHelper.degrees_to_gps(latitude)
    #exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = deg_to_gps(float(longitude))#piexif.GPSHelper.degrees_to_gps(longitude)

    # Modify datetime original
    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = datetime_original.strftime("%Y:%m:%d %H:%M:%S")

    # Modify camera maker and camera model
    exif_dict['0th'][piexif.ImageIFD.Make] = camera_maker.encode('utf-8')
    exif_dict['0th'][piexif.ImageIFD.Model] = camera_model.encode('utf-8')

    # Save modified Exif data back to the image
    exif_bytes = piexif.dump(exif_dict)
    #piexif.insert(exif_bytes, image_path)
    img.save(image_path, exif=exif_bytes)

# Example usage
#image_path = "example.jpg"
#latitude = 37.7749
#longitude = -122.4194
#datetime_original = datetime(2022, 4, 20, 10, 30, 0)
#camera_maker = "New Camera Maker"
#camera_model = "New Camera Model"

#modify_exif(image_path, latitude, longitude, datetime_original, camera_maker, camera_model)


if __name__ == '__main__':
    camFigs = list(sys.argv[1:-1])
    des = sys.argv[-1]
    print(camFigs)
    #camFigs = glob.glob(src)
    for camFig in tqdm(camFigs):
        geotagged_IMG,lat,long,date,time = main(camFig,des)
        cam_maker = 'Google'
        cam_model = 'Pixel 6 :: Captured by - GPS Map Camera'
        modify_exif(geotagged_IMG,lat,long,date,time,cam_maker,cam_model)
