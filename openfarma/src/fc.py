import streamlit as st
import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from .params import *

api_key = st.secrets["OPENFARMA_API_KEY"]

# Loading the vectordatabase
embedding = OpenAIEmbeddings(api_key=api_key)
database = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embedding)

# Extra functions they will be used in the functions calling
def checkStock(file_path: str, ids_to_check: list) -> dict:
    """
    Check if the stock is greater than zero for the ids in the list.

    Args:
        file_path (str): Path to the file.
        ids_to_check (list): List of ids to check.

    Raises:
        Exception: If there's an error checking the stock.

    Returns:
        dict: Dictionary with the ids as keys and the stocks as values.
    """
    try:
        df = pd.read_csv(file_path)
        ids = df.iloc[:, 1].tolist()
        stocks = df.iloc[:, 2].tolist()
        # check the ids_to_check in the ids list and return the stocks for the ids in the list
        return {ids[i]: stocks[i] > 0 for i in range(len(ids)) if ids[i] in ids_to_check}
    except Exception as e:
        raise Exception(f"Error checking stock: {e}")
    
def filter(file_path: str, ids_to_check: list, column_id: int, keyword: str, flag: bool = False) -> list:
    """
    Filter the dataframe by the ids in the list, the keyword in the column and the flag.

    Args:
        file_path (str): Path to the file.
        ids_to_check (list): List of ids to check.
        column_id (int): Column id to filter.
        keyword (str): Keyword to filter.
        flag (bool, optional): If True, filter the opposite of the keyword.

    Returns:
        list: List of ids.
    """
    try:
        df = pd.read_csv(file_path)
        # Filter the dataframe by the ids in the list
        df.iloc[:, 1] = df.iloc[:, 1].astype(str)
        df = df[df.iloc[:, 1].isin(ids_to_check)]
        # Filter the dataframe by the keyword in the column
        df.iloc[:, column_id] = df.iloc[:, column_id].str.lower()
        if flag:
            df = df[~df.iloc[:, column_id].str.contains(keyword, case=False, na=False)]
        else:
            df = df[df.iloc[:, column_id].str.contains(keyword, case=False, na=False)]
        
        return df.iloc[:, 1].tolist()
    except Exception as e:
        raise Exception(f"Error filtering: {e}")

def getStock(file_path: str, ids_to_check: list) -> dict:
    """
    Get the stock for the ids in the list.

    Args:
        file_path (str): Path to the file.
        ids_to_check (list): List of ids to check.

    Raises:
        Exception: If there's an error getting the stock.

    Returns:
        dict: Dictionary with the ids as keys and the stocks as values.
    """
    try:
        df = pd.read_csv(file_path)
        ids = df.iloc[:, 1].tolist()
        stocks = df.iloc[:, 2].tolist()
        return {ids[i]: stocks[i] for i in range(len(ids)) if ids[i] in ids_to_check}
    except Exception as e:
        raise Exception(f"Error getting stock: {e}")
    
def getPrice(file_path: str, ids_to_check: list) -> dict:
    """
    Get the price for the ids in the list.

    Args:
        file_path (str): Path to the file.
        ids_to_check (list): List of ids to check.

    Raises:
        Exception: If there's an error getting the price.

    Returns:
        dict: Dictionary with the ids as keys and the prices as values.
    """
    try:
        df = pd.read_csv(file_path)
        ids = df.iloc[:, 1].tolist()
        prices = df.iloc[:, 3].tolist()
        return {ids[i]: prices[i] for i in range(len(ids)) if ids[i] in ids_to_check}
    except Exception as e:
        raise Exception(f"Error getting price: {e}")
    
def getSale(file_path: str, ids_to_check: list) -> dict:
    """
    Get the sale for the ids in the list.

    Args:
        file_path (str): Path to the file.
        ids_to_check (list): List of ids to check.

    Raises:
        Exception: If there's an error getting the sale.

    Returns:
        dict: Dictionary with the ids as keys and the sales as values.
    """
    try:
        df = pd.read_csv(file_path)
        ids = df.iloc[:, 1].tolist()
        sales = df.iloc[:, 4].tolist()
        return {ids[i]: sales[i] for i in range(len(ids)) if ids[i] in ids_to_check}
    except Exception as e:
        raise Exception(f"Error getting sale: {e}")
    
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
    
def searchInDatabase(ids: list, k: int=5) -> dict:
    """
    Search and get the data from the database based on the ids.

    Args:
        ids (list): List of ids to search.
        k (int, optional): Number of results to return.

    Returns:
        dict: Dictionary with the ids as keys and the data as values.
    """
    try:
        df = pd.read_csv(PRODUCTS_PATH)
        df = df[df.iloc[:, 0].isin(ids)]
        data = {}
        if not df.empty:
            for _, row in df.iterrows():
                data[row.iloc[0]] = row.iloc[2]
        return data
    except Exception as e:
        raise Exception(f"Error searching in database: {e}")


# ----------------- #
# FUNCTIONS CALLING #
# ----------------- #

def buscar_productos(**kwargs):
    problem = kwargs['problem']
    retrived_from_vdb = database.similarity_search_with_score(problem, k=K_VALUE_SEARCH)
    ids = [retrived_from_vdb[i][0].metadata['EAN'] for i in range(K_VALUE_SEARCH)]
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
        context = f"No se encontraron productos para la consulta sobre: {problem}."
    
    return f"Contexto: {context}"

def contar_marcas():
    df = pd.read_csv(PRODUCTS_PATH)
    brands = df.iloc[:, 1].apply(lambda x: x.lower()).tolist()
    brands = list(set(brands))
    return f"Hay {len(brands)} marcas en total."

def listar_marcas():
    df = pd.read_csv(PRODUCTS_PATH)
    brands = df.iloc[:, 1].apply(lambda x: x.lower()).tolist()
    brands = list(set(brands))
    brands = [brand.capitalize() for brand in brands]
    return f"Las marcas son: {', '.join(brands)}."

def verificar_marca(**kwargs):
    brand_to_check = kwargs['marca'].lower()
    df = pd.read_csv(PRODUCTS_PATH)
    brands = df.iloc[:, 1].apply(lambda x: x.lower()).tolist()
    brands = list(set(brands))
    result = brand_to_check in brands
    return f"La marca {brand_to_check.capitalize()} {'sí' if result else 'no'} está en la base de datos."

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

def buscar_productos_por_precio(**kwargs):
    price_min = float(str(kwargs['precio_min']))
    price_max = float(str(kwargs['precio_max']))
    try:
        # Get ids of the products in the range of prices
        df = pd.read_csv(STOCK_PATH)
        df = df[(df.iloc[:, 3] >= price_min) & (df.iloc[:, 3] <= price_max)]
        ids = df.iloc[:, 1].tolist()
        prices = df.iloc[:, 3].tolist()
        # Look for the ids in the database
        data = searchInDatabase(ids, k=K_VALUE_THOLD)
        # Join data with prices for ids in common
        if len(data) > 0:
            context = []
            for id, data in data.items():
                context.append(f"{data} {prices[ids.index(id)]}")
            context = '\n'.join(context)
        else:
            context = f"No se encontraron productos en el rango de precios entre {price_min} y {price_max}."
        return f"Contexto: {context}"
    except Exception as e:
        raise Exception(f"Error searching products by price: {e}")
    
def buscar_productos_por_zona_aplicacion(**kwargs):
    zone = kwargs['zona_aplicacion']
    retrived_from_vdb = database.similarity_search_with_score(zone, k=K_VALUE_SEARCH)
    ids = [retrived_from_vdb[i][0].metadata['EAN'] for i in range(K_VALUE_SEARCH)]
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
        context = f"No se encontraron productos para aplicar en: {zone}."
    
    return f"Contexto: {context}"

def buscar_productos_por_ingrediente(**kwargs):
    ingredient = kwargs['ingrediente']
    retrived_from_vdb = database.similarity_search_with_score(ingredient, k=K_VALUE_SEARCH)
    ids = [retrived_from_vdb[i][0].metadata['EAN'] for i in range(K_VALUE_SEARCH)]
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
        context = f"No se encontraron productos con el ingrediente: {ingredient}."
    
    return f"Contexto: {context}"

def buscar_productos_por_presentacion(**kwargs):
    presentation = kwargs['presentacion']
    retrived_from_vdb = database.similarity_search_with_score(presentation, k=K_VALUE_SEARCH)
    ids = [retrived_from_vdb[i][0].metadata['EAN'] for i in range(K_VALUE_SEARCH)]
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
        context = f"No se encontraron productos con la presentación: {presentation}."
    
    return f"Contexto: {context}"

def listar_productos_en_categorias(**kwargs):
    category = kwargs['categoria']
    retrived_from_vdb = database.similarity_search_with_score(category, k=K_VALUE_SEARCH)
    ids = [retrived_from_vdb[i][0].metadata['EAN'] for i in range(K_VALUE_SEARCH)]
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

def buscar_productos_por_problema_y_promocion(**kwargs):
    problem = kwargs['problematica']
    retrived_from_vdb = database.similarity_search_with_score(problem, k=K_VALUE_SEARCH)
    ids = [retrived_from_vdb[i][0].metadata['EAN'] for i in range(K_VALUE_SEARCH)]
    ids = filter(STOCK_PATH, ids, 4, 'no promo', flag=True)
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
        context = f"No se encontraron productos en promoción para la consulta sobre: {problem}."
    
    return f"Contexto: {context}"

def buscar_productos_por_presentacion_y_tamano(**kwargs):
    presentation = f"{kwargs['presentacion']} {kwargs['valor']}{kwargs['unidad']}"
    retrived_from_vdb = database.similarity_search_with_score(presentation, k=K_VALUE_SEARCH)
    ids = [retrived_from_vdb[i][0].metadata['EAN'] for i in range(K_VALUE_SEARCH)]
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
        context = f"No se encontraron productos con la presentación: {presentation}."
    
    return f"Contexto: {context}"

def listar_productos_por_rango_precio_y_promocion(**kwargs):
    price_min = float(str(kwargs['precio_min']))
    price_max = float(str(kwargs['precio_max']))
    try:
        # Get ids of the products in the range of prices
        df = pd.read_csv(STOCK_PATH)
        df.iloc[:, 4] = df.iloc[:, 4].apply(lambda x: x.lower())
        df = df[df.iloc[:, 4] != 'no promo']
        df = df[(df.iloc[:, 3] >= price_min) & (df.iloc[:, 3] <= price_max)]
        ids = df.iloc[:, 1].tolist()
        prices = df.iloc[:, 3].tolist()
        # Look for the ids in the database
        data = searchInDatabase(ids, k=K_VALUE_THOLD)
        # Join data with prices for ids in common
        if len(data) > 0:
            context = []
            for id, data in data.items():
                context.append(f"{data} {prices[ids.index(id)]}")
            context = '\n'.join(context)
        else:
            context = f"No se encontraron productos en promoción en el rango de precios entre {price_min} y {price_max}."
        return f"Contexto: {context}"
    except Exception as e:
        raise Exception(f"Error searching products by price: {e}")

handlers = {
    "buscar_productos": buscar_productos,
    "contar_marcas": contar_marcas,
    "listar_marcas": listar_marcas,
    "verificar_marca": verificar_marca,
    "contar_productos_con_stock": contar_productos_con_stock,
    "contar_productos_en_promocion": contar_productos_en_promocion,
    "buscar_productos_por_precio": buscar_productos_por_precio,
    "buscar_productos_por_zona_aplicacion": buscar_productos_por_zona_aplicacion,
    "buscar_productos_por_ingrediente": buscar_productos_por_ingrediente,
    "buscar_productos_por_presentacion": buscar_productos_por_presentacion,
    "listar_productos_en_categorias": listar_productos_en_categorias,
    "buscar_productos_por_problema_y_promocion": buscar_productos_por_problema_y_promocion,
    "buscar_productos_por_presentacion_y_tamano": buscar_productos_por_presentacion_y_tamano,
    "listar_productos_por_rango_precio_y_promocion": listar_productos_por_rango_precio_y_promocion
}