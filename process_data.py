import os
import pandas as pd
import pdfplumber
import re
import streamlit as st

# Define paths and file names
data_path = "data/pdfs"
output_csv = "data/mercadata.csv"

# Define the category keywords
CATEGORY_KEYWORDS = {
    "frutas": ["fruta", "banana", "manzana", "naranja", "fresa", "uvas", "pera", "kiwi", "sandía", "melon", 
               "melocoton", "limon", "platano", "cereza", "ciruela", "mandarina", "mango", "pomelo",
               "aguacate", "piña", "coco", "papaya", "granada", "higo", "guayaba", "mora"],
    "lácteos": ["leche", "yogur", "queso", "mantequilla", "crema", "nata", "kefir", "kéfir", "feta",
                "mozzarella", "parmesano", "burrata", "cheddar", "gouda", "provolone", "ricotta",
                "rulo precortado", "griego", "tiramisu", "curado cortado", "rulo cabra"],
    "carnes": ["pollo", "res", "cerdo", "jamon", "jamón", "salchicha", "mortadela", "chorizo",
               "huevo", "pechuga", "chuleta", "conejo", "pavo", "ternera", "butifarra", "longaniza",
               "cecina", "salami", "lomo", "tocino", "salchichón", "cecina", "fuet", "sobrasada",
               "cordero", "bacon", "serrano", "embutido", "salchichon"],
    "pescado": ["salmón", "atun", "atún", "bacalao", "merluza", "lubina", "sardina", "pulpo", "calamar",
                "gamba", "rodaballo", "boquerones", "anchoas", "pescado"],
    "bebidas": ["agua", "jugo", "refresco", "vino", "cerveza", "café", "coca cola",
                "aquarius", "ladron de manzanas", "fanta", "sprite", "tonica", "red bull",
                "monster", "pepsi", "ambar", "mahou", "estrella galicia", "alhambra", "corona",
                "heineken", "estrella damm", "cafe", "chai", "ron", "whisky", "gin", "vodka",],
    "panadería": ["pan", "bollos", "baguette", "croissant", "brioche", "panecillo", "panettone",
                  "chapata", "hojaldre"],
    "granos y cereales": ["pasta", "arroz", "lenteja", "quinoa", "cuscus", "harina", "avena",
                          "maiz", "garbanzos", "trigo", "cereal", "alubias", "penne",
                          "tortiglioni", "medialuna", "canelones", "tortillas", "spaghetti",
                          "macarron", "fideos", "couscous", "muesli", "digestive", "garbanzo"],
    "limpieza": ["detergente", "jabón", "limpiador", "esponja"],
    "snacks": ["patatas", "galletas", "chocolates", "golosinas", "frutos secos", "palomitas",
               "nachos", "hummus", "salsa", "dip", "anacardos", "cacahuetes", "pipas", "pretzels",
               "choco gotas", ],
    "verduras": ["rucula", "lechuga", "tomate", "cebolla", "ajo", "pimiento", "calabaza",
                 "zanahoria", "berenjena", "calabacin", "pepino", "judia", "espinacas",
                 "cilantro", "perejil", "apio", "remolacha", "coliflor", "brocoli", "oregano",
                 "orégano", "brotes tiernos"],
    "higiene": ["shampoo", "jabón", "pasta de dientes", "desodorante", "cepillo de dientes",
                "toallas sanitarias", "pañales", "crema", "preservativo", "basura", "papel higiénico",
                "papel higienico", "toallitas", "bayeta", "esponja", "pastillas antical",
                "champu", "acondicionador", "gel de ducha", "jabon de manos", "colonia",
                "limpia", "lavavajillas", "roll-on", "bolsa", "body depil"],
    # Add more categories and keywords as needed
}

def categorize_item(item):
    """
    Categorizes an item based on predefined keyword mappings.

    Parameters:
    - item (str): The name of the item to categorize.

    Returns:
    - str: The category of the item.
    """
    item_lower = item.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in item_lower:
                return category.capitalize()
    return "Otros"

def process_pdfs(uploaded_files):
    data = []

    # Ensure data directory exists
    data_path = "data"
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    for uploaded_file in uploaded_files:
        pdf_path = os.path.join(data_path, uploaded_file.name)
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Initialize variables to store receipt-level information
        fecha = ""
        identificativo = ""
        ubicacion = ""

        # Flags and buffers for multi-line items
        waiting_for_continuation = False
        pending_item = {}

        # Process each PDF file
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()

            if text:
                lines = text.split('\n')

                # Extract fecha, identificativo de ticket, and ubicacion
                for line in lines:
                    # Extract fecha and identificativo
                    fecha_match = re.search(r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})\s+OP:\s+(\d+)', line)
                    if fecha_match:
                        fecha = fecha_match.group(1)
                        identificativo = fecha_match.group(2)
                        continue

                    # Extract ubicacion (assuming it's in lines containing an address)
                    ubicacion_match = re.search(r'^(AVDA\.|C\.|CALLE)\s+.*\d+', line, re.IGNORECASE)
                    if ubicacion_match:
                        ubicacion = line.strip()
                        continue

                # Identify the start of the items section
                items_start = False
                for idx, line in enumerate(lines):
                    if re.search(r'Descripción\s+P\.\s+Unit\s+Importe', line, re.IGNORECASE):
                        items_start = True
                        start_idx = idx + 1
                        break

                if not items_start:
                    # If header not found, assume items start after a certain number of lines
                    start_idx = 5  # Adjust as needed

                # Iterate through item lines
                idx = start_idx
                while idx < len(lines):
                    line = lines[idx].strip()

                    # Stop processing when reaching totals or other non-item sections
                    if re.search(r'\b(TOTAL|IVA|TARJETA|IMPORTE)\b', line, re.IGNORECASE):
                        break

                    # Check if the line starts with a quantity (e.g., "1 ", "2 ")
                    quantity_match = re.match(r'^(\d+)\s+(.*)', line)
                    if quantity_match:
                        quantity = quantity_match.group(1)
                        rest = quantity_match.group(2)

                        # Attempt to extract prices using regex
                        # This regex captures all occurrences of prices in the format "X,XX"
                        price_matches = re.findall(r'(\d+,\d{2})', rest)

                        if len(price_matches) >= 2:
                            # Single-line item with unit and total price
                            # Assume the last two matches are unit price and total price
                            precio_total = price_matches[-1].replace(',', '.')
                            # Extract item name by removing the last two price parts
                            # This assumes item name does not contain numbers that look like prices
                            item_name = re.sub(r'\s*\d+,\d{2}$', '', rest).strip()
                            categoria = categorize_item(item_name)
                            data.append([fecha, identificativo, ubicacion, item_name, categoria, float(precio_total)])
                        elif len(price_matches) == 1:
                            # Single-line item with only total price
                            # Extract item name by removing the last price
                            item_name = re.sub(r'\s*\d+,\d{2}$', '', rest).strip()
                            precio_total = price_matches[0].replace(',', '.')
                            categoria = categorize_item(item_name)
                            data.append([fecha, identificativo, ubicacion, item_name, categoria, float(precio_total)])
                        else:
                            # Possible multi-line item without price on the first line
                            item_name = rest.strip()
                            # Look ahead to the next line for weight and price
                            if idx + 1 < len(lines):
                                next_line = lines[idx + 1].strip()
                                # Match patterns like "0,474 kg 1,40 €/kg 0,66"
                                weight_price_match = re.match(r'^(\d+,\d{3})\s+kg\s+(\d+,\d{2})\s+€/kg\s+(\d+,\d{2})', next_line)
                                if weight_price_match:
                                    precio_total = weight_price_match.group(3).replace(',', '.')
                                    categoria = categorize_item(item_name)
                                    data.append([fecha, identificativo, ubicacion, item_name, categoria, float(precio_total)])
                                    idx += 1  # Skip the next line as it's part of the current item
                                else:
                                    # If no weight and price, attempt to find any price in the next line
                                    next_price_matches = re.findall(r'(\d+,\d{2})', next_line)
                                    if next_price_matches:
                                        precio_total = next_price_matches[-1].replace(',', '.')
                                        categoria = categorize_item(item_name)
                                        data.append([fecha, identificativo, ubicacion, item_name, categoria, float(precio_total)])
                                        idx += 1  # Skip the next line as it's part of the current item
                                    else:
                                        # If no price information, skip or handle as needed
                                        pass
                    else:
                        # Handle lines that might be continuations of previous items or other formats
                        # Currently, no specific handling is needed
                        pass

                    idx += 1

    if data:
        # Create a DataFrame and save it locally as CSV
        df = pd.DataFrame(data, columns=["fecha", "identificativo de ticket", "ubicación", "item", "categoría", "precio"])
        print(df)
        print(df.loc[df["categoría"] == "Otros"])
        df.to_csv(output_csv, index=False)
        st.success(f"Archivo CSV generado con éxito: {output_csv}")
    else:
        st.info("No se encontraron datos para escribir en el archivo CSV.")


def main():
    st.title("Procesador de Tickets PDF")

    # Permitir a los usuarios subir archivos PDF
    uploaded_files = st.file_uploader("Sube tus archivos PDF", accept_multiple_files=True, type="pdf")

    if uploaded_files:
        process_pdfs(uploaded_files)

if __name__ == "__main__":
    main()