#takes a document, add a table in it(with data as the provided dict) and returns the same doc
from docx.shared import RGBColor
import os
import openpyxl
import json
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font
from collections import defaultdict


def add_screenshots_to_docx(doc,directory_path, grafana_ids, table_ids):
    doc.add_heading("Charts", level=2)
    all_shots = os.listdir(directory_path)
    mapping = defaultdict(lambda: defaultdict(lambda: []))
    for shot in all_shots:
        panel_id, n, topic = shot.split('_')
        panel_id,n = int(panel_id),int(n)
        title, _ = topic.split('.')
        mapping[panel_id]['title'] = [title]
        mapping[panel_id]['images'].append(shot)
    
    for index, panel in enumerate(grafana_ids):
        if panel in table_ids:
            mapping[panel]['images'].sort(key=lambda s: int(s.split('_')[1]))
        if panel not in mapping:continue
        title = mapping[panel]['title'][0].capitalize()
        print(f'{index+1}:({panel}){title}')            
        doc.add_heading(title, level=3)
        for filename in mapping[panel]['images']:
            file_path = os.path.join(directory_path, filename)
            try:
                # img = PILImage.open(file_path)
                # img_width, img_height = img.size
                # aspect_ratio = img_height / img_width
                # width = 450
                # height = int(width * aspect_ratio)
                doc.add_picture(file_path)
            except Exception as e:
                print(f"Error processing image {filename}: {e}")
    return doc

def add_table(doc,data_dict):
    title = data_dict["title"]
    header = data_dict["header"]
    body = data_dict["body"]
    doc.add_heading(title, level=3)
    cols = len(header)
    rows = len(body)

    table =doc.add_table(rows=1, cols=cols)
    table.style = 'Table Grid'
    table.autofit = True
    header_cells = table.rows[0].cells
    for col in range(cols):
        header_cells[col].text = header[col]

    for row_num in range(rows):
        row = table.add_row().cells
        for col_num in range(len(body[row_num])):
            try:
                text,value,color = body[row_num][col_num]
            except:
                text,value = body[row_num][col_num]
                color="none"

            run = row[col_num].paragraphs[0].add_run(str(text))

            if color == "green":
                run.font.color.rgb = RGBColor(0, 128, 0)  # Green color
            elif color=="red":
                run.font.color.rgb = RGBColor(255, 0, 0)  # Red color
    return doc

def update_col_width(sheet,value_width,col):
    col_letter = get_column_letter(col)
    if col_letter not in sheet.column_dimensions:
        sheet.column_dimensions[col_letter].width = value_width
    else:
        current_width = sheet.column_dimensions[col_letter].width
        if value_width > current_width:
            sheet.column_dimensions[col_letter].width = value_width



def add_row(sheet,value,row_num,temp_col,found):
    for val in value:
        
        color=None
        try:
            text,num,color = val
        except:
            text,num=val
        try:
            num=float(num)
        except:pass
        
        new_cell = sheet.cell(row=row_num, column=temp_col, value=num)
        if not found:
            new_cell.fill = PatternFill(start_color="b8f1ff", end_color="b8f1ff", fill_type="solid")  # blue fill
        if color and color=="red":
            new_cell.fill = PatternFill(start_color="F0C0C0", end_color="F0C0C0", fill_type="solid")  # Red fill
        elif color and color=="green":
            new_cell.fill = PatternFill(start_color="C0F0CF", end_color="C0F0CF", fill_type="solid")  # Green fill
        temp_col+=1

        update_col_width(sheet,len(str(num)) , temp_col)
        update_col_width(sheet,len(str(num)) , temp_col-1)

    return sheet


def add_columns(sheet_name,data_dict,workbook,build):
    sheet = workbook[sheet_name]
    col = sheet.max_column +1 
    while(col>2 and sheet.cell(row=1,column=col-1).value is None):
        col-=1
        sheet.delete_cols(col)

    build_cell = sheet.cell(row=1, column=col, value=int(build))
    build_cell.font = Font(bold=True)
    metric_cell = sheet.cell(row=1, column=1, value="Metric")
    metric_cell.font = Font(bold=True)
    sheet.freeze_panes = sheet.cell(row=2, column=2)

    for lst in data_dict["body"]:
        key = lst[0][0]
        value = lst[2:]

        found=False

        row = sheet.max_row +1

        for row_num in range(2, row):
            cell_value = sheet.cell(row=row_num, column=1).value
            if cell_value is not None and cell_value.lower() == key.lower():
                found=True
                sheet = add_row(sheet,value,row_num,col,found)
                break  # Exit the loop after finding a match
        if not found:
            sheet.cell(row=row, column=1, value=key.lower())
            sheet = add_row(sheet,value,row,col,found)



    update_col_width(sheet,len(build)+1 , col)
    update_col_width(sheet,len(build)+1 , col-1)
    update_col_width(sheet,58 , 1)




def excel_update(sheets , prev_path, curr_path,build):
    if os.path.exists(curr_path):
        workbook = openpyxl.load_workbook(curr_path)
        missing_sheets = [sheet_name for sheet_name in sheets if sheet_name not in workbook.sheetnames]
        for sheet_name in missing_sheets:
            print(f"Added sheet {sheet_name}")
            workbook.create_sheet(sheet_name)
        print("Loaded existing excel and added new sheets")
    else:
        if not os.path.exists(prev_path):
            workbook = openpyxl.Workbook()
            default_sheet = workbook.active
            workbook.remove(default_sheet)
            for sheet in sheets:
                print(f"Added sheet {sheet}")
                sheet1 = workbook.create_sheet(sheet)
            print("created new excel sheet and added new sheets")
        else:
            workbook = openpyxl.load_workbook(prev_path)
            missing_sheets = [sheet_name for sheet_name in sheets if sheet_name not in workbook.sheetnames]
            for sheet_name in missing_sheets:
                print(f"Added sheet {sheet_name}")
                workbook.create_sheet(sheet_name)
            print("Loaded existing excel and added new sheets")
    for sheet in sheets:
        print(f"Processing sheet {sheet} ...")
        add_columns(sheet,sheets[sheet],workbook,build)
    
    workbook.save(curr_path)
    print("Updated Excel sheet succcessfully")




def add_load_details(doc,details):
    doc.add_heading("Load Details", level=2)
    for key, value in details.items():
        doc.add_paragraph(f"{key}: {value}")
    return doc


