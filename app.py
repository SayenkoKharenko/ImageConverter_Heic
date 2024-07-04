from flask import Flask, render_template, request, send_file, redirect, url_for
import os
import errno
import subprocess
import shutil
import zipfile

app = Flask(__name__)

# Функции конвертации и вспомогательные функции

def create_directory(directory):
    ''' Создание директории, если она не существует. '''
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def convert(inp, outp, quality, rec=False, verbose=False):
    ''' Конвертация из HEIC в JPG. '''
    if os.path.isfile(inp):
        pre, ext = os.path.splitext(inp)
        if ext.lower() in ['.heic', '.heif']:
            if outp is None:
                outp = pre + '.jpg'
            else:
                assert not os.path.isdir(outp), "Both inp and outp should be files"
                pre, ext = os.path.splitext(outp)
                assert ext.lower() in ['.jpg']
                dirname = os.path.dirname(outp)
                create_directory(dirname)
            subprocess.call('heif-convert -q {} "{}" "{}"'.format(quality, inp, outp), shell=True)
        else:
            outp = inp if outp is None else outp
            shutil.copy2(src=inp, dst=outp, follow_symlinks=True)

    elif os.path.isdir(inp):
        if outp is None:
            outp = inp
        else:
            create_directory(outp)
        for name in os.listdir(inp):
            inpath = os.path.join(inp, name)
            outpath = os.path.join(outp, name)
            if os.path.isfile(inpath):
                pre, ext = os.path.splitext(name)
                outpath = os.path.join(outp, pre + '.jpg') if ext.lower() in ['.heic', '.heif'] else outpath
                convert(inpath, outpath, quality, rec, verbose)
            elif os.path.isdir(inpath) and rec:
                convert(inpath, outpath, quality, rec, verbose)
            elif os.path.isdir(inpath) and not rec:
                shutil.copytree(src=inpath, dst=outpath, symlinks=True,
                                ignore_dangling_symlinks=True)

def create_zip_archive(input_folder, output_zip):
    ''' Создание ZIP архива из файлов в указанной директории. '''
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for root, _, files in os.walk(input_folder):
            for file in files:
                file_path = os.path.join(root, file)
                if file_path == output_zip:  # Исключаем сам архив из архивации
                    continue
                zipf.write(file_path, arcname=os.path.relpath(file_path, input_folder))

@app.route('/')
def index():
    return render_template('index.html', download_link=None)

@app.route('/upload', methods=['POST'])
def upload():
    if 'files[]' not in request.files:
        return "No file part"
    files = request.files.getlist('files[]')
    if not files:
        return "No selected files"

    input_folder = '/app/upl/'
    output_folder = '/app/downl/'
    zip_file_path = '/app/output/archive.zip'

    create_directory(input_folder)
    create_directory(output_folder)

    for file in files:
        if file.filename == '':
            continue
        filename = file.filename
        file.save(os.path.join(input_folder, filename))
        # Perform conversion
        input_file_path = os.path.join(input_folder, filename)
        output_file_path = os.path.join(output_folder, os.path.splitext(filename)[0] + '.jpg')
        convert(input_file_path, output_file_path, quality=90, rec=False, verbose=True)

    # Create ZIP archive
    create_zip_archive(output_folder, zip_file_path)

    download_link = url_for('download')
    return render_template('index.html', download_link=download_link)

@app.route('/download')
def download():
    zip_file_path = '/app/output/archive.zip'
    filename = 'converted_files.zip'
    response = send_file(zip_file_path, as_attachment=True)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response

if __name__ == '__main__':
    app.run(debug=True, port=5000)
