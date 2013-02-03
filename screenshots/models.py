from django.db import models
from PIL import Image
import StringIO

from screenshots.processing import get_thumbnail_sizing_params

PIL_READABLE_FORMATS = []
WEB_USABLE_FORMATS = ['PNG', 'JPEG', 'GIF']
EXTENSIONS_BY_FORMAT = {'PNG': 'png', 'JPEG': 'jpg', 'GIF': 'gif'}


class PILConvertibleImage(object):
	"""
		represents an image which can be converted to an 'original' or a thumbnail
		using PIL.
	"""
	def __init__(self, source_file):
		self.file = source_file
		self.image = Image.open(source_file)  # raises IOError if image can't be identified
		if self.image.format not in PIL_READABLE_FORMATS:
			raise IOError("Image format is not supported")

	def create_original(self):
		"""
			return a file object for an image of the same dimensions as the original, in a
			web-usable format, along with a tuple of its dimensions and the appropriate file extension
		"""
		if self.image.format in WEB_USABLE_FORMATS:
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
				img = img.convert('P')
			img.save(output, format='PNG', optimize=True)
			return output, self.image.size, 'png'
		else:
			img.save(output, format='JPEG', optimize=True, quality=90)
			return output, self.image.size, 'jpg'
