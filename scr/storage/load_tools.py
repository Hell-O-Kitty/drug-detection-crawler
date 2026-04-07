import os

def read_single_html(file_path):
    # 파일 유효성 검사
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"file not found. : {file_path}"


def load_all_html_in_folder(folder_path):
    html_files = []

    # 폴더 유효성 검사
    if not os.path.exists(folder_path):
        print(f"folder not found. : {folder_path}")
        return html_files

    print(f"folder access success. : {folder_path}")

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".html"):
            print(file_name, end=" / ")
            html_files.append({
                "file_name" : file_name,
                "file_path" : os.path.join(folder_path, file_name)
            })
    print()
    print(f"load {len(html_files)} HTML files.")
    print()

    return html_files