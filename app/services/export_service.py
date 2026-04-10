import csv
import io

def _seconds_to_timecode(seconds_val: float, fps: int = 30) -> str:
    from math import floor
    total_frames = int(round(seconds_val * fps))
    frames = total_frames % fps
    total_seconds = total_frames // fps
    sec = total_seconds % 60
    total_minutes = total_seconds // 60
    mnt = total_minutes % 60
    hr = total_minutes // 60
    return f"{hr:02d}:{mnt:02d}:{sec:02d}:{frames:02d}"

def generate_premiere_csv(recommendations: list[dict]) -> str:
    """
    Gera um arquivo CSV de marcadores compativel com o Adobe Premiere.
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["Marker Name", "Description", "In", "Out", "Duration", "Marker Type"])
    
    for rec in recommendations:
        time = rec.get("timestamp_seconds", 0)
        try:
            time_val = float(time)
        except:
            time_val = 0.0
            
        timecode = _seconds_to_timecode(time_val)
        tag = rec.get("tag", "Marcador")
        description = rec.get("description", "")
        
        writer.writerow([tag, description, timecode, timecode, "00:00:00:00", "Comment"])
        
    return output.getvalue()

def generate_ae_script(recommendations: list[dict]) -> str:
    """
    Gera um script JSX para After Effects que cria marcadores na composição ativa.
    
    Args:
        recommendations: Lista de dicionários contendo 'timestamp_seconds', 'tag', 'description'.
    
    Returns:
        String contendo o código JSX.
    """
    
    # Cabeçalho do script
    script_content = """
{
    function createMarkers() {
        var comp = app.project.activeItem;
        if (!comp || !(comp instanceof CompItem)) {
            alert("Por favor, selecione uma composição ativa.");
            return;
        }

        app.beginUndoGroup("Importar Marcadores IA");

        var layerName = "Marcadores IA";
        var markerLayer = comp.layer(layerName);
        
        // Se não existir a layer, cria um Null
        if (!markerLayer) {
            markerLayer = comp.layers.addNull();
            markerLayer.name = layerName;
            markerLayer.label = 10; // Purple
        }
        
        // Função auxiliar para adicionar marcador
        function addMarker(time, comment, chapter, url) {
            var marker = new MarkerValue(comment);
            marker.chapter = chapter ? chapter.substring(0, 127) : ""; // Chapter limit
            marker.comment = comment;
            // marker.url = url || ""; // Optional
            
            markerLayer.property("Marker").setValueAtTime(time, marker);
        }

"""
    
    # Adicionar os marcadores
    for rec in recommendations:
        # Extrair dados com segurança
        time = rec.get("timestamp_seconds", 0)
        # Se vier como string "MM:SS", converter? O modelo pydantic garante float normalmente.
        # Mas por segurança, garantimos float.
        try:
            time_val = float(time)
        except:
            time_val = 0.0

        tag = rec.get("tag", "Marcador")
        description = rec.get("description", "")
        
        # Escapar aspas para evitar quebra do JS
        tag_safe = tag.replace('"', '\\"').replace('\n', ' ')
        desc_safe = description.replace('"', '\\"').replace('\n', ' ')
        
        line = f'        addMarker({time_val}, "{tag_safe}", "{desc_safe}");\n'
        script_content += line

    # Fechamento do script
    script_content += """
        app.endUndoGroup();
        alert("Marcadores importados com sucesso!");
    }

    createMarkers();
}
"""
    return script_content
