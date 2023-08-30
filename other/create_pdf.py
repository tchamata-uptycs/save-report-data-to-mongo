import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image as PILImage
import time
from collections import defaultdict

class LoadTestReportNewPdf():
	def create_pdf_from_images(self,directory_path, pdf_file_name,grafana_ids,table_ids):
		doc = SimpleDocTemplate(pdf_file_name, pagesize=letter)
		header_style = ParagraphStyle('Heading3', parent=getSampleStyleSheet()['Heading2'], italic=False)
		story = []
		# styles = getSampleStyleSheet()
		# header_style = styles['Heading3']
		count=0
		all_shots = os.listdir('grafana_screenshots')
		mapping=defaultdict(lambda : defaultdict(lambda :[]))
		for shot in all_shots:
			panel_id , n , topic = shot.split('_')
			panel_id = int(panel_id)
			n=int(n)
			title,_ = topic.split('.')
			mapping[panel_id]['title'] = [title]
			mapping[panel_id]['images'].append(shot)

		for index,panel in enumerate(grafana_ids):
			if panel in table_ids:(mapping[panel]['images']).sort(key=lambda s: int(s.split('_')[1]))
			title = mapping[panel]['title'][0]
			story.append(Paragraph(f'<h1><b>{title}</b></h1>', header_style))
			# if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
			for filename in mapping[panel]['images']:
				file_path = os.path.join(directory_path, filename)
				try:
					img = PILImage.open(file_path)
					width, height = img.size
					aspect_ratio = height / width
					img_width = 450
					img_height = int(img_width * aspect_ratio)
					story.append(Image(file_path, width=img_width, height=img_height))
				except Exception as e:
					print(f"Error processing image {filename}: {e}")
		doc.build(story)



