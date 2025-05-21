import streamlit as st
import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from .params import *

api_key = st.secrets["OPENFARMA_API_KEY"]
embedding = OpenAIEmbeddings(api_key=api_key)

# Loading the vectordatabase
DB_ALL_PATH = os.path.join(CHROMA_DB_PATH, "db_all")
DB_BENEFICIOS_PATH = os.path.join(CHROMA_DB_PATH, "db_Beneficios")
DB_CATEGORIA_PATH = os.path.join(CHROMA_DB_PATH, "db_Categoria")
DB_GENERALES_PATH = os.path.join(CHROMA_DB_PATH, "db_General")
DB_INDICACIONES_PATH = os.path.join(CHROMA_DB_PATH, "db_Indicaciones")
DB_USO_PATH = os.path.join(CHROMA_DB_PATH, "db_Modo de uso")
DB_PROPIEDADES_PATH = os.path.join(CHROMA_DB_PATH, "db_Propiedades")

db_all = Chroma(persist_directory=DB_ALL_PATH, embedding_function=embedding)
db_beneficios = Chroma(persist_directory=DB_BENEFICIOS_PATH, embedding_function=embedding)
db_categoria = Chroma(persist_directory=DB_CATEGORIA_PATH, embedding_function=embedding)
db_general = Chroma(persist_directory=DB_GENERALES_PATH, embedding_function=embedding)
db_indicaciones = Chroma(persist_directory=DB_INDICACIONES_PATH, embedding_function=embedding)
db_uso = Chroma(persist_directory=DB_USO_PATH, embedding_function=embedding)
db_propiedades = Chroma(persist_directory=DB_PROPIEDADES_PATH, embedding_function=embedding)
        

def getData(file_path: str, ids_to_check: list, null_stock: bool = False) -> dict:
    """
    Get the data for the ids in the list.

    Args:
        file_path (str): Path to the file.
        ids_to_check (list): List of ids to check.
        null_stock (bool): If True, discard the ids with stock 0.

    Raises:
        Exception: If there's an error getting the data.

    Returns:
        dict: Dictionary with the ids as keys and the data as values.
    """
    try:
        df = pd.read_csv(file_path)
        df.iloc[:, 1] = df.iloc[:, 1].astype(str)
        df = df[df.iloc[:, 1].isin(ids_to_check)]
        if null_stock:
            df = df[df.iloc[:, 2] > 0]
        
        data = {}
        if not df.empty:
            for _, row in df.iterrows():
                data[row.iloc[1]] = f"Stock: {row.iloc[2]}. Precio: ${row.iloc[3]}. Promoción: {row.iloc[4]}."
        return data
    except Exception as e:
        raise Exception(f"Error getting data: {e}")

def retrieveVectorDB(database: Chroma, context: str, k: int=10) -> list:
    """
    Retrieve the ids and their associated text content from the vector database based on similarity to the input context.

    Args:
        database (Chroma): The Chroma vector database to search in
        context (str): The search query text to find similar entries for
        k (int, optional): Maximum number of results to return. Defaults to 10.

    Returns:
        dict: Dictionary mapping EAN IDs to their associated text content, for the k most similar entries

    Raises:
        Exception: If there's an error retrieving from the vector database
    """
    retrieve_dict = {}
    try:
        retrived_from_vdb = database.similarity_search_with_score(context, k=k)
        N = len(retrived_from_vdb)
        for i in range(N):
            id = str(retrived_from_vdb[i][0].metadata['EAN']).strip()
            text = retrived_from_vdb[i][0].page_content
            retrieve_dict[id] = text
        return retrieve_dict
    except Exception as e:
        raise Exception(f"Error retrieving vector database: {e}")
    
def retrieveImages(ids: list, file_path: str) -> dict:
    """
    Retrieve the images for the ids in the list.
    """
    images_by_id = {}
    ids = [str(id).strip() for id in ids]
    df_images = pd.read_csv(file_path, sep=',', encoding='utf-8')
    df_images = df_images.astype(str).apply(lambda x: x.str.strip())
    
    for id in ids:
        match_sku = df_images[df_images['SKU'] == id]
        match_ean = df_images[df_images['EAN'] == id]
        
        # Skip if multiple matches in either SKU or EAN
        if len(match_sku) > 1 or len(match_ean) > 1:
            continue
            
        # Skip if matches in both SKU and EAN but from different rows
        if not match_sku.empty and not match_ean.empty:
            if not match_sku.index.equals(match_ean.index):
                continue
            else:
                images_by_id[id] = match_sku.iloc[0]['IMAGEN']
        elif not match_sku.empty:
            images_by_id[id] = match_sku.iloc[0]['IMAGEN']
        elif not match_ean.empty:
            images_by_id[id] = match_ean.iloc[0]['IMAGEN']
    
    return images_by_id

def retrieveSaleData(ids: list, file_path: str, null_stock: bool = False) -> dict:
    """
    Retrieve the sale data for the ids in the list.
    """
    sale_data = {}
    ids = [str(id).strip() for id in ids]
    df_sale = pd.read_csv(file_path, sep=',', encoding='utf-8')
    df_sale = df_sale.astype(str).apply(lambda x: x.str.strip())

    for id in ids:
        match_ean = df_sale[df_sale['ean'] == id]
        if len(match_ean) > 1:
            continue
        elif not match_ean.empty:
            if not null_stock:
                if match_ean.iloc[0]['stock'] != '0':
                    sale_data[id] = [
                        match_ean.iloc[0]['stock'],
                        match_ean.iloc[0]['precio'],
                        match_ean.iloc[0]['promo']
                    ]
            else:
                sale_data[id] = [
                    match_ean.iloc[0]['stock'],
                    match_ean.iloc[0]['precio'],
                    match_ean.iloc[0]['promo']
                ]
        else:
            continue
    return sale_data

def buildProductContext(ids: list, product_data: dict, null_stock: bool = False, 
                        force_sale: bool = False, include_images: bool = True, 
                        default_message: str = "No se encontraron productos que cumplan \
                            con los criterios de búsqueda.") -> str:
    """
    Build context string for products based on provided data and filters.
    
    Args:
        ids (list): List of product IDs
        product_data (dict): Product data from vector DB
        null_stock (bool): Whether to include products with 0 stock
        force_sale (bool): Whether to only include products on sale
        include_images (bool): Whether to include product images
        
    Returns:
        str: Formatted context string with product details
    """
    sale_data = retrieveSaleData(ids, STOCK_PATH, null_stock=null_stock)
    url_data = retrieveImages(ids, IMAGES_PATH) if include_images else {}
    
    if len(sale_data) > 0:
        productos = []
        for id in sale_data.keys():
            stock, price, sale = sale_data[id]
            
            # Skip if force_sale is True and product not on sale
            if force_sale and sale.lower() == 'no promo':
                continue
                
            product = product_data[id]
            description = f"{product}\n"
            description += f"Stock: {stock}. Precio: ${price}. Promoción: {sale}\n"
            
            if include_images:
                url = url_data.get(id, "")
                if url:
                    description += f"URL: https://{url}\n"
            
            productos.append(description)

            if len(productos) >= K_VALUE_THOLD:
                break

        if productos:
            context = """Los productos encontrados son:\n\n"""
            for p in productos:
                context += f"{p}\n"
            return context
            
        return default_message
    
    return "No se encontraron productos disponibles."
        
        

# ----------------- #
# FUNCTIONS CALLING #
# ----------------- #

def buscar_productos(**kwargs):
    problem = kwargs['problem']
    product_data = retrieveVectorDB(db_general, problem, k=K_VALUE_SEARCH)
    ids = list(product_data.keys())
    default_message = f"No se encontraron productos que cumplan con la consulta sobre: {problem}."
    
    return buildProductContext(
        ids=ids,
        product_data=product_data,
        null_stock=False,
        force_sale=False,
        include_images=True,
        default_message=default_message
    )
    
def buscar_productos_por_presentacion(**kwargs):
    presentation = kwargs['presentacion']
    product_data = retrieveVectorDB(db_general, presentation, k=K_VALUE_SEARCH)
    ids = list(product_data.keys())
    default_message = f"No se encontraron productos con la presentación: {presentation}."

    return buildProductContext(
        ids=ids,
        product_data=product_data,
        null_stock=False,
        force_sale=False,
        include_images=True,
        default_message=default_message
    )

def buscar_productos_por_beneficios(**kwargs):
    benefits = kwargs['beneficio']
    product_data = retrieveVectorDB(db_beneficios, benefits, k=K_VALUE_SEARCH)
    ids = list(product_data.keys())
    default_message = f"No se encontraron productos con los beneficios: {benefits}."

    return buildProductContext(
        ids=ids,
        product_data=product_data,
        null_stock=False,
        force_sale=False,
        include_images=True,
        default_message=default_message
    )

def buscar_productos_por_categoria(**kwargs):
    category = kwargs['categoria']
    product_data = retrieveVectorDB(db_categoria, category, k=K_VALUE_SEARCH)
    ids = list(product_data.keys())
    default_message = f"No se encontraron productos en la categoría: {category}."
    
    return buildProductContext(
        ids=ids,
        product_data=product_data,
        null_stock=False,
        force_sale=False,
        include_images=True,
        default_message=default_message
    )
    
def buscar_productos_por_indicaciones(**kwargs):
    indications = kwargs['indicacion']
    product_data = retrieveVectorDB(db_indicaciones, indications, k=K_VALUE_SEARCH)
    ids = list(product_data.keys())
    default_message = f"No se encontraron productos con las indicaciones: {indications}."
    
    return buildProductContext(
        ids=ids,
        product_data=product_data,
        null_stock=False,
        force_sale=False,
        include_images=True,
        default_message=default_message
    )
    
def buscar_productos_por_modo_uso(**kwargs):
    mode_of_use = kwargs['uso']
    product_data = retrieveVectorDB(db_uso, mode_of_use, k=K_VALUE_SEARCH)
    ids = list(product_data.keys())
    default_message = f"No se encontraron productos con el modo de uso: {mode_of_use}."
    
    return buildProductContext(
        ids=ids,
        product_data=product_data,
        null_stock=False,
        force_sale=False,
        include_images=True,
        default_message=default_message
    )

def buscar_productos_por_propiedades(**kwargs):
    properties = kwargs['propiedad']
    product_data = retrieveVectorDB(db_propiedades, properties, k=K_VALUE_SEARCH)
    ids = list(product_data.keys())
    default_message = f"No se encontraron productos con las propiedades: {properties}."

    return buildProductContext(
        ids=ids,
        product_data=product_data,
        null_stock=False,
        force_sale=False,
        include_images=True,
        default_message=default_message
    )
    
def buscar_productos_por_problema_y_promocion(**kwargs):
    problem = kwargs['problematica']
    product_data = retrieveVectorDB(db_all, problem, k=K_VALUE_SEARCH)
    ids = list(product_data.keys())
    default_message = f"No se encontraron productos en promoción para la consulta sobre: {problem}."
    
    return buildProductContext(
        ids=ids,
        product_data=product_data,
        null_stock=False,
        force_sale=True,
        include_images=True,
        default_message=default_message
    )

def buscar_productos_por_presentacion_y_tamano(**kwargs):
    presentation = f"{kwargs['presentacion']} {kwargs['valor']}{kwargs['unidad']}"
    product_data = retrieveVectorDB(db_general, presentation, k=K_VALUE_SEARCH)
    ids = list(product_data.keys())
    default_message = f"No se encontraron productos con la presentación: {presentation}."
    
    return buildProductContext(
        ids=ids,
        product_data=product_data,
        null_stock=False,
        force_sale=False,
        include_images=True,
        default_message=default_message
    )

def contar_marcas():
    df = pd.read_csv(ABM_PATH, usecols=['Marca'])
    brands = df['Marca'].str.lower().tolist()
    brands = set(brands)
    return f"Hay {len(brands)} marcas en total."

def contar_productos_con_stock():
    try:
        df = pd.read_csv(STOCK_PATH)
        num_products = df.iloc[:, 2].apply(lambda x: x > 0).sum()
    except Exception as e:
        raise Exception(f"Error counting products with stock: {e}")
    return f"Hay {num_products} productos en stock."

def contar_productos_en_promocion():
    try:
        df = pd.read_csv(STOCK_PATH)
        df.iloc[:, 4] = df.iloc[:, 4].apply(lambda x: x.lower())
        num_products = df.iloc[:, 4].apply(lambda x: x != 'no promo').sum()
        return f"Hay {num_products} productos en promoción."
    except Exception as e:
        raise Exception(f"Error counting products in promotion: {e}")

def listar_marcas():
    df = pd.read_csv(ABM_PATH, usecols=['Marca'])
    brands = df['Marca'].str.lower().tolist()
    brands = set(brands)
    brands = [brand.capitalize() for brand in brands]
    return f"Las marcas son: {', '.join(brands)}."

def listar_productos_en_categorias(**kwargs):
    category = kwargs['categoria']
    retrived_from_vdb = retrieveVectorDB(db_categoria, category, k=K_VALUE_SEARCH)
    ids = list(retrived_from_vdb.keys())
    stock_data = getData(STOCK_PATH, ids, null_stock=True)

    if len(stock_data) > 0:
        i = 0
        context = []
        for id, data in stock_data.items():
            index = ids.index(id)
            context.append(f"{retrived_from_vdb[index][0].page_content} {data}")
            i += 1
            if i >= K_VALUE_THOLD:
                break
        context = '\n'.join(context)
    else:
        context = f"No se encontraron productos en la categoría: {category}."
    
    return f"Contexto: {context}"

def verificar_marca(**kwargs):
    brand_to_check = kwargs['marca'].lower()
    df = pd.read_csv(ABM_PATH, usecols=['Marca'])
    brands = df['Marca'].str.lower().tolist()
    brands = set(brands)
    result = brand_to_check in brands
    return f"La marca {brand_to_check.capitalize()} {'sí' if result else 'no'} está en la base de datos."

handlers = {
    "buscar_productos": buscar_productos,
    "buscar_productos_por_presentacion": buscar_productos_por_presentacion,
    "buscar_productos_por_beneficios": buscar_productos_por_beneficios,
    "buscar_productos_por_categoria": buscar_productos_por_categoria,
    "buscar_productos_por_indicaciones": buscar_productos_por_indicaciones,
    "buscar_productos_por_modo_uso": buscar_productos_por_modo_uso,
    "buscar_productos_por_propiedades": buscar_productos_por_propiedades,
    "buscar_productos_por_problema_y_promocion": buscar_productos_por_problema_y_promocion,
    "buscar_productos_por_presentacion_y_tamano": buscar_productos_por_presentacion_y_tamano,
    "contar_marcas": contar_marcas,
    "contar_productos_con_stock": contar_productos_con_stock,
    "contar_productos_en_promocion": contar_productos_en_promocion,
    "listar_marcas": listar_marcas,
    "listar_productos_en_categorias": listar_productos_en_categorias,
    "verificar_marca": verificar_marca
}