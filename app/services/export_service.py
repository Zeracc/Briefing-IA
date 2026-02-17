
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
