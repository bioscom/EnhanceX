from django.shortcuts import render
from django.http import FileResponse
import os, zipfile, tempfile
from .converter import convert_pdf_to_pptx
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import render

def index(request):
    return render(request, "convert/index.html")

def ajax_convert(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        base_name = os.path.splitext(file.name)[0]
        input_path = default_storage.save(f"{base_name}.pdf", file)
        input_full = os.path.join("media", input_path)
        output_path = os.path.join("media", f"{base_name}.pptx")

        convert_pdf_to_pptx(input_full, output_path)

        return JsonResponse({"status": "success", "url": f"/media/{base_name}.pptx"})
    
    return JsonResponse({"status": "error", "message": "Invalid upload"}, status=400)

def index(request):
    if request.method == "POST":
        uploaded_files = request.FILES.getlist('files')
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "converted.zip")

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for pdf in uploaded_files:
                pdf_name = pdf.name
                pdf_path = os.path.join(temp_dir, pdf_name)
                with open(pdf_path, 'wb+') as f:
                    for chunk in pdf.chunks():
                        f.write(chunk)

                pptx_name = os.path.splitext(pdf_name)[0] + ".pptx"
                pptx_path = os.path.join(temp_dir, pptx_name)

                convert_pdf_to_pptx(pdf_path, pptx_path)
                zipf.write(pptx_path, pptx_name)

        return FileResponse(open(zip_path, 'rb'), as_attachment=True, filename="converted_pptx.zip")

    return render(request, "convert/index.html")