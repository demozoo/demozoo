import os
import os.path
import StringIO
import subprocess
import tempfile

from PIL import Image
from recoil import RecoilImage

from django.conf import settings

from screenshots.processing import get_thumbnail_sizing_params

# file extensions that we are able to convert to web-usable images.
# (RECOIL supports many more, but we won't list them all as some of them have quite
# generic extensions, like .max, and that's likely to introduce false positives
# when looking for possible image files in zipfiles)
USABLE_IMAGE_FILE_EXTENSIONS = [
	'bmp', 'gif', 'iff', 'iff24', 'ilbm', 'jpe', 'jpg', 'jpeg', 'lbm', 'pcx',
	'png', 'tga', 'tif', 'tiff', 'xbm', 'xpm',
	'msp', 'neo', 'pac', 'pc1', 'pc2', 'pc3', 'pi1', 'pi2', 'pi3', 'rgb', 'scr',
	'tny', 'tn1', 'tn2', 'tn3',
]
# image formats that we recognise as images, even if we can't convert them
IMAGE_FILE_EXTENSIONS = [
	'bmp', 'ce', 'ce1', 'ce2', 'dcx', 'dib', 'eps', 'fpx', 'gif', 'ic1',
	'ic2', 'ic3', 'ico', 'iff', 'iff24', 'ilbm', 'jng', 'jpe', 'jpg', 'jpeg', 'lbm', 'msp', 'neo',
	'pac', 'pbm', 'pc1', 'pc2', 'pc3', 'pcd', 'pcx', 'pgm', 'pi1', 'pi2',
	'pi3', 'png', 'ppm', 'psd', 'rgb', 'rle', 'scr', 'sgi', 'svg', 'tga',
	'tif', 'tiff', 'tny', 'tn1', 'tn2', 'tn3', 'wmf', 'xbm', 'xcf', 'xpm',
]

PIL_READABLE_FORMATS = ['BMP', 'GIF', 'ICO', 'JPEG', 'PCD', 'PCX', 'PNG', 'PPM', 'PSD', 'TGA', 'TIFF', 'XBM', 'XPM']
WEB_USABLE_FORMATS = ['PNG', 'JPEG', 'GIF']
EXTENSIONS_BY_FORMAT = {'PNG': 'png', 'JPEG': 'jpg', 'GIF': 'gif'}


ANSILOVE_C_PATH = getattr(settings, 'ANSILOVE_C_PATH')
if ANSILOVE_C_PATH:
	ANSILOVE_C_READABLE_FORMATS = ['ans', 'adf', 'idf', 'xb', 'pcb', 'tnd', 'asc', 'nfo', 'diz']
	USABLE_IMAGE_FILE_EXTENSIONS += ANSILOVE_C_READABLE_FORMATS
	IMAGE_FILE_EXTENSIONS += ANSILOVE_C_READABLE_FORMATS
else:
	ANSILOVE_C_READABLE_FORMATS = []


# file formats that are readable by ansilove.js
USABLE_ANSI_FILE_EXTENSIONS = [
	# leave out 'bin', because those might require us to specify number of columns, and if
	# other versions of the file exist, we'd rather use those instead
	'ans', 'txt', 'nfo', 'asc', 'diz', 'ion', 'adf', 'idf', 'pcb', 'tnd', 'xb'
]


class PILConvertibleImage(object):
	"""
		represents an image which can be converted to an 'original' or a thumbnail
		using PIL.
	"""
	def __init__(self, source_file, name_hint=""):
		# we will retain the original file object if AND ONLY IF it is directly readable by PIL,
		# so that it can be returned as-is for use as the original rendition in the case of web-usable formats
		self.file = None

		opened_with_pil = False
		try:
			self.image = Image.open(source_file)  # raises IOError if image can't be identified
			opened_with_pil = True
			self.file = source_file
		except IOError:
			basename, ext = os.path.splitext(os.path.basename(name_hint))
			if ext and ext[1:].lower() in ANSILOVE_C_READABLE_FORMATS:
				# write source file contents to a temporary file
				fd, input_path = tempfile.mkstemp(prefix=basename, suffix=ext)
				f = os.fdopen(fd, 'wb')
				source_file.seek(0)
				f.write(source_file.read())
				f.close()

				# run file through ansilove
				output_path = input_path + '.png'
				subprocess.check_call([ANSILOVE_C_PATH, input_path, '-o', output_path])

				# open result with PIL
				try:
					self.image = Image.open(output_path)
				except IOError:
					# On Linux (or just on the live server or something), ansilove adds a
					# redundant .png to the output filename. LULZ.
					output_path += '.png'
					self.image = Image.open(output_path)
				self.image.load()  # load pixel data and close file so we can delete it

				# delete input and output files
				os.remove(input_path)
				os.remove(output_path)

			else:
				# try pyrecoil
				try:
					source_file.seek(0)
					img = RecoilImage(name_hint, source_file)
					self.image = img.to_pil()
				except ValueError:
					raise IOError("Image format is not supported")

		if opened_with_pil and self.image.format not in PIL_READABLE_FORMATS:
			raise IOError("Image format is not supported")

	def create_original(self):
		"""
			return a file object for an image of the same dimensions as the original, in a
			web-usable format, along with a tuple of its dimensions and the appropriate file extension
		"""
		if self.image.format in WEB_USABLE_FORMATS and self.file is not None:
			# just return the original file object, since it's already usable in that format
			return self.file, self.image.size, EXTENSIONS_BY_FORMAT[self.image.format]
		else:
			# convert to PNG (a sensible choice for all non-web-native images, as it's reasonable
			# to assume that those formats are lossless - and even if they weren't, converting to
			# JPG and potentially losing more fidelity may not me ideal.)
			output = StringIO.StringIO()
			self.image.save(output, format='PNG', optimize=True)
			return output, self.image.size, 'png'

	def create_thumbnail(self, target_size):
		img = self.image
		crop_params, resize_params = get_thumbnail_sizing_params(img.size, target_size)
		if crop_params:
			img = img.crop(crop_params)

		# check whether the original image has <=256 distinct colours, in which case we'll create
		# the thumbnail as a png rather than jpg. img.getcolors will return None if the colour count
		# exceeds the passed max_colours.
		has_limited_palette = bool(img.getcolors(256))

		if resize_params:
			# must ensure image is non-paletted for a high-quality resize
			if img.mode in ['1', 'P']:
				img = img.convert('RGB')
			img = img.resize(resize_params, Image.ANTIALIAS)

		output = StringIO.StringIO()
		if has_limited_palette:
			if img.mode not in ['1', 'P']:
				# img.convert with palette=Image.ADAPTIVE will apparently only work on
				# 'L' or 'RGB' images, not RGBA for example. So, need to pre-convert to RGB...
				img = img.convert('RGB')
				img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
			img.save(output, format='PNG', optimize=True)
			return output, img.size, 'png'
		else:
			try:
				img.save(output, format='JPEG', optimize=True, quality=90)
			except IOError:
				# optimize option can fail with quality > 85 - see http://mail.python.org/pipermail/image-sig/2006-April/003858.html
				# ...so try without optimize
				img.save(output, format='JPEG', quality=90)
			return output, img.size, 'jpg'
